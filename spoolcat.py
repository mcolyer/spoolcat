#!/usr/bin/env python3
# Spoolcat: ultra-light PDF uploader → CUPS printer
# - No auth (intended for Tailscale-bound access)
# - Color / B&W and Duplex options
# - Tailwind-styled upload + status pages
# - SQLite job log
# - Auto-purges uploaded files after RETENTION_DAYS

import os, sqlite3, subprocess, shlex, time, threading, traceback, json
from datetime import datetime
from bottle import Bottle, request, response, run, BaseRequest, static_file, redirect

# ----- Configuration (override via env) --------------------------------------
PRINTER = os.getenv("PRINTER", "YourCupsQueueName")       # e.g. from `lpstat -p`
DB_PATH = os.getenv("DB_PATH", "./jobs.sqlite3")
SPOOL   = os.getenv("UPLOAD_DIR", "./spool")
HOST    = os.getenv("HOST", "127.0.0.1")                  # set to your Tailscale IP
PORT    = int(os.getenv("PORT", "8080"))
MAX_MB  = int(os.getenv("MAX_UPLOAD_MB", "32"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))    # purge spool files older than N days

# Cap in-memory upload size; Bottle will spool to disk for larger files
BaseRequest.MEMFILE_MAX = MAX_MB * 1024 * 1024
os.makedirs(SPOOL, exist_ok=True)

# ----- App & DB ----------------------------------------------------------------
app = Bottle()
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("""
CREATE TABLE IF NOT EXISTS jobs(
  id INTEGER PRIMARY KEY,
  filename   TEXT NOT NULL,
  cups_job_id INTEGER,
  status     TEXT NOT NULL,       -- spooling | submitted | error | purged
  color      TEXT NOT NULL,       -- Color | Gray
  duplex     TEXT NOT NULL,       -- DuplexNoTumble | None
  created_at TEXT NOT NULL
)
""")
conn.commit()

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _insert_job(filename, status, color, duplex):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO jobs(filename, status, color, duplex, created_at) VALUES(?,?,?,?,?)",
        (filename, status, color, duplex, _now_iso())
    )
    jid = cur.lastrowid
    conn.commit()
    return jid

# ----- Pages -------------------------------------------------------------------
@app.get("/")
def index_page():
    return static_file("index.html", root=".")

@app.get("/status")
def status_page():
    return static_file("status.html", root=".")

# ----- API ---------------------------------------------------------------------
@app.post("/upload")
def upload():
    up = request.files.get("file")
    if not up:
        response.status = 400; return "missing form field 'file'"
    if not up.filename.lower().endswith(".pdf"):
        response.status = 400; return "only PDF files are accepted"

    # Read UI options (defaults are sensible)
    color  = request.forms.get("color", "Color")               # "Color" or "Gray"
    duplex = request.forms.get("duplex", "DuplexNoTumble")     # "DuplexNoTumble" or "None"

    # Save to spool with safe name
    safe_name = f"{int(time.time())}_{up.filename.replace('/','_')}"
    path = os.path.join(SPOOL, safe_name)
    up.save(path)

    jid = _insert_job(safe_name, "spooling", color, duplex)
    try:
        # Send to CUPS queue (queue is created by entrypoint.sh if PRINTER is a URI)
        cmd = f"lp -d {shlex.quote(PRINTER)} -o ColorModel={color} -o Duplex={duplex} {shlex.quote(path)}"
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True).strip()

        # Parse "Printer-123" → 123
        cups_id = next((int(tok.split("-")[-1]) for tok in out.split()
                        if "-" in tok and tok.split("-")[-1].isdigit()), None)

        conn.execute("UPDATE jobs SET status=?, cups_job_id=? WHERE id=?",
                     ("submitted", cups_id, jid))
        conn.commit()
        redirect("/status")
    except subprocess.CalledProcessError as e:
        conn.execute("UPDATE jobs SET status=? WHERE id=?", ("error", jid))
        conn.commit()
        response.status = 500
        return f"Print job failed: {e.output}"

@app.get("/jobs")
def jobs():
    response.content_type = 'application/json'
    try:
        rows = conn.execute(
            "SELECT id,filename,cups_job_id,status,color,duplex,created_at "
            "FROM jobs ORDER BY id DESC LIMIT 200"
        ).fetchall()
        cols = ["id","filename","cups_job_id","status","color","duplex","created_at"]
        result = [dict(zip(cols, r)) for r in rows]
        return json.dumps(result)
    except Exception as e:
        traceback.print_exc()
        response.status = 500
        return json.dumps({"error": str(e)})

# Manual cleanup trigger (safe on Tailnet; no auth by design here)
@app.post("/admin/run_cleanup")
def run_cleanup_now():
    n = _purge_once()
    return {"purged_files": n, "retention_days": RETENTION_DAYS}

# ----- Janitor (hourly) --------------------------------------------------------
def _purge_once():
    cutoff = time.time() - (RETENTION_DAYS * 86400)
    removed = 0
    for name in os.listdir(SPOOL):
        path = os.path.join(SPOOL, name)
        try:
            if not os.path.isfile(path):
                continue
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
                removed += 1
                conn.execute(
                    "UPDATE jobs SET status='purged' WHERE filename=? AND status!='purged'",
                    (name,)
                )
        except Exception:
            traceback.print_exc()
    conn.commit()
    return removed

def _janitor_loop():
    while True:
        try:
            _purge_once()
        except Exception:
            traceback.print_exc()
        time.sleep(3600)  # hourly

def _start_janitor():
    t = threading.Thread(target=_janitor_loop, name="janitor", daemon=True)
    t.start()

# ----- Main --------------------------------------------------------------------
if __name__ == "__main__":
    _start_janitor()
    run(app, host=HOST, port=PORT)


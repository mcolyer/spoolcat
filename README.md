# Spoolcat

Web-based PDF print spooler for CUPS printers.

## Features

- Upload PDFs via web interface
- Print to CUPS queues or IPP URIs
- Color/grayscale and duplex options
- SQLite job history
- Auto-cleanup of old files
- No authentication (designed for private networks)

## Requirements

- Docker and Docker Compose
- CUPS-compatible printer or IPP endpoint

## Usage

```bash
docker compose up -d
```

Access at `http://localhost` (or configured host)

## Configuration

Environment variables in `compose.yaml`:

- `PRINTER`: CUPS queue name or IPP URI (e.g., `ipp://10.0.1.183/ipp/print`)
- `HOST`: Bind address (default: `0.0.0.0`)
- `PORT`: HTTP port (default: `80`)
- `DB_PATH`: SQLite database path (default: `/data/jobs.sqlite3`)
- `UPLOAD_DIR`: Spool directory (default: `/spool`)
- `RETENTION_DAYS`: Days to keep uploaded files (default: `7`)
- `MAX_UPLOAD_MB`: Max file size in MB (default: `64`)

## Docker Image

Available at `ghcr.io/mcolyer/spoolcat:latest`

## License

MIT

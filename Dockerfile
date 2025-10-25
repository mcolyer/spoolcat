# Tiny Python + CUPS client so `lp` can talk IPP directly
FROM python:3.12-slim

# Install cups client tools (lp, lpstat) and curl for health checks if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
      cups-bsd cups-client \
    && rm -rf /var/lib/apt/lists/*

# Copy app
WORKDIR /app
COPY miniprint.py index.html status.html ./

# Runtime dirs for data/spool (mounted as volumes)
RUN mkdir -p /data /spool

# Use uv to run; install uv (tiny, fast)
RUN pip install --no-cache-dir uv

ENV HOST=0.0.0.0 PORT=8080 \
    DB_PATH=/data/jobs.sqlite3 \
    UPLOAD_DIR=/spool \
    MAX_UPLOAD_MB=64 \
    RETENTION_DAYS=7

EXPOSE 8080
CMD ["./spoolcat.py"]


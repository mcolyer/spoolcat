# Tiny Python + CUPS client so `lp` can talk IPP directly
FROM python:3.12-slim

# Install CUPS (server + client tools) for queue management and IPP access
RUN apt-get update && apt-get install -y --no-install-recommends \
      cups cups-bsd cups-client \
    && rm -rf /var/lib/apt/lists/*

# Copy app and entrypoint
WORKDIR /app
COPY spoolcat.py index.html status.html entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Runtime dirs for data/spool (mounted as volumes)
RUN mkdir -p /data /spool

# Use uv to run; install uv (tiny, fast)
RUN pip install --no-cache-dir uv

ENV HOST=0.0.0.0 PORT=80 \
    DB_PATH=/data/jobs.sqlite3 \
    UPLOAD_DIR=/spool \
    MAX_UPLOAD_MB=64 \
    RETENTION_DAYS=7

EXPOSE 80
ENTRYPOINT ["/app/entrypoint.sh"]


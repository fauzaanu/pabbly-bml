import os

# Railway (and most PaaS hosts) inject the port to listen on at runtime.
bind = "0.0.0.0:" + os.environ.get("PORT", "8080")

workers = int(os.environ.get("WEB_CONCURRENCY", "2"))

# Keep gunicorn's worker heartbeat file on tmpfs where one is available —
# container disks can stall it and cause spurious worker timeouts.
worker_tmp_dir = "/dev/shm" if os.path.isdir("/dev/shm") else None

FROM python:3.12-slim

# Keeps .pyc files out of the image and makes log lines appear immediately
# instead of sitting in a buffer, which matters when the only view into a
# container is `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Requirements are copied and installed before the source, so editing app.py
# reuses the cached dependency layer instead of reinstalling on every build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Nothing in here needs root once the dependencies are installed.
RUN useradd --create-home --shell /usr/sbin/nologin bazaar
USER bazaar

# The bind address is configuration, not a literal in the CMD, so the same image
# can sit behind the gateway on whatever interface and port it is given.
ENV BIND_HOST=127.0.0.1 \
    BIND_PORT=8000

EXPOSE 8000

# `exec` so uvicorn replaces the shell and becomes PID 1. Without it the shell
# stays PID 1, and `docker stop` delivers SIGTERM to the shell instead of to the
# server, which then has to be killed.
CMD ["sh", "-c", \
     "exec uvicorn app:app --host \"$BIND_HOST\" --port \"$BIND_PORT\" --no-access-log"]

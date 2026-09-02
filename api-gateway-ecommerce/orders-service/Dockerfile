FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN useradd --create-home --shell /usr/sbin/nologin bazaar
USER bazaar

ENV BIND_HOST=127.0.0.1 \
    BIND_PORT=8001

EXPOSE 8001

# uvicorn's own access log is switched off because the middleware in app.py
# already logs every request with its correlation ID; both would print each
# request twice.
CMD ["sh", "-c", \
     "exec uvicorn app:app --host \"$BIND_HOST\" --port \"$BIND_PORT\" --no-access-log"]

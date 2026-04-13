FROM python:3.13-alpine
WORKDIR /app

RUN addgroup -S appgroup && adduser -S appuser -G appgroup && \
    apk add --no-cache nodejs npm git && \
    npm install -g @asyncapi/cli@5.0.5 && \
    mkdir -p /usr/local/lib/node_modules/@asyncapi/cli/lib/utils/logs && \
    chown -R appuser:appgroup /usr/local/lib/node_modules/@asyncapi/cli/lib/utils/logs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appgroup /app
USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

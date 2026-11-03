# podman build -t looking-glass -f Containerfile .
# podman run -d --name looking-glass -p 5000:5000 -p 5100:5100 -v lg-data:/app/data:Z looking-glass
FROM docker.io/library/python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LG_DATA_DIR=/app/data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY python ./python
COPY static ./static
COPY templates ./templates
COPY web_html ./web_html
COPY config.example.yaml ./config.example.yaml

RUN useradd --system --uid 1001 --home /app lg && mkdir -p /app/data && chown -R lg /app/data
USER lg
VOLUME ["/app/data"]
EXPOSE 5000 5100
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:5000/healthz')" || exit 1
CMD ["python", "python/main.py", "serve"]

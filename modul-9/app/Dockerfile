# Stage 1: Dependencies
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim
LABEL maintainer="admin@pens.ac.id"
LABEL description="Flask Demo — Built by Drone CI"

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=appuser:appuser app.py .
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1
CMD ["python", "app.py"]

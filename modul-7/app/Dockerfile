# SECURE Dockerfile — Production Best Practices

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

LABEL maintainer="admin@pens.ac.id"
LABEL description="Secured Flask App — PENS Docker Lab"

# Buat non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Copy dependencies dari builder stage
COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=appuser:appuser app.py .

# Switch ke non-root user
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

CMD ["python", "app.py"]

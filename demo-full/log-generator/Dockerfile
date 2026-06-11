FROM python:3.11-slim
WORKDIR /app
COPY generator.py .
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
USER appuser
CMD ["python", "-u", "generator.py"]

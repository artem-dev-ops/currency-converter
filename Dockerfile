FROM python:3.11-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl=8.5.0-2ubuntu10.9 && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --disabled-password --gecos '' appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 5000
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:5000 -w ${GUNICORN_WORKERS:-1} app:app"]
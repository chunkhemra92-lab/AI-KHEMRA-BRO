FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl tini && rm -rf /var/lib/apt/lists/* && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser && mkdir -p /var/lib/ai-khemra-bro && chown -R appuser:appuser /var/lib/ai-khemra-bro
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh && chown -R appuser:appuser /app
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 CMD curl --fail --silent http://127.0.0.1:8501/_stcore/health || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]

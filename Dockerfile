FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/appuser \
    HF_HOME=/home/appuser/.cache/huggingface

WORKDIR /app

# FFmpeg/FFprobe power the video and MP3 pipeline. libgomp1 supports
# faster-whisper/ctranslate2 on CPU. tini prevents orphaned child processes.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        ffmpeg \
        gosu \
        libgomp1 \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && mkdir -p /var/lib/ai-khemra-bro "${HF_HOME}" \
    && chown -R appuser:appuser /var/lib/ai-khemra-bro /home/appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh \
    && chown -R appuser:appuser /app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
  CMD curl --fail --silent http://127.0.0.1:8501/_stcore/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]

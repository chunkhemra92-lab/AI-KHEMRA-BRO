from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
COMPOSE = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
CADDY = (ROOT / "Caddyfile").read_text(encoding="utf-8")
ENV_TEMPLATE = (ROOT / ".env.example").read_text(encoding="utf-8")
DOCKERIGNORE = (ROOT / ".dockerignore").read_text(encoding="utf-8")

assert 'os.getenv("LICENSE_DB_PATH"' in APP
assert 'os.getenv(name, default)' in APP
assert 'ffmpeg' in DOCKERFILE
assert 'libgomp1' in DOCKERFILE
assert 'HEALTHCHECK' in DOCKERFILE
assert '/_stcore/health' in DOCKERFILE
assert 'app:' in COMPOSE
assert 'caddy:' in COMPOSE
assert 'restart: unless-stopped' in COMPOSE
assert 'LICENSE_DB_PATH: /var/lib/ai-khemra-bro/licenses.db' in COMPOSE
assert 'ai_khemra_data:/var/lib/ai-khemra-bro' in COMPOSE
assert 'ai_khemra_models:/home/appuser/.cache/huggingface' in COMPOSE
assert 'condition: service_healthy' in COMPOSE
assert '80:80' in COMPOSE and '443:443' in COMPOSE
assert '{$DOMAIN}' in CADDY
assert 'reverse_proxy app:8501' in CADDY
for secret_name in ('ADMIN_USERNAME', 'ADMIN_PASSWORD', 'COOKIE_SECRET', 'LICENSE_PEPPER'):
    assert f'{secret_name}=' in ENV_TEMPLATE
assert '.env' in DOCKERIGNORE
assert 'licenses.db' in DOCKERIGNORE
print("VPS Docker deployment package assertions passed")

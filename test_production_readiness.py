from pathlib import Path
import tomllib

ROOT = Path(__file__).parent
SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
CONFIG_PATH = ROOT / ".streamlit" / "config.toml"

assert 'EDGE_TTS_MAX_CONCURRENT_REQUESTS = 2' in SOURCE
assert 'FFMPEG_FINAL_MIX_TIMEOUT_SECONDS = 900' in SOURCE
assert 'sqlite3.connect(str(LICENSE_DB_PATH), timeout=30)' in SOURCE
assert 'PRAGMA journal_mode=WAL' in SOURCE
assert 'PRAGMA busy_timeout=30000' in SOURCE
assert 'max_mb = 150' in SOURCE
assert CONFIG_PATH.exists(), "Missing Streamlit production configuration"

with CONFIG_PATH.open("rb") as config_file:
    config = tomllib.load(config_file)

assert config["server"]["maxUploadSize"] == 150
assert config["client"]["toolbarMode"] == "viewer"
print("Production readiness safeguards passed")

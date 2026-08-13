import ast
import datetime
import hashlib
import hmac
import re
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path

source_path = Path(__file__).with_name("app.py")
source_text = source_path.read_text(encoding="utf-8")
tree = ast.parse(source_text, filename=str(source_path))
assignments = {"NEW_LICENSE_CARD_HOURS", "LEGACY_COOKIE_SECRET"}
functions = {"normalize_access_code", "_utcnow", "_iso", "_hash_code", "create_access_code_batch"}
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in assignments for name in names):
            nodes.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in functions:
        nodes.append(node)

with tempfile.TemporaryDirectory() as temp_dir:
    db_path = Path(temp_dir) / "licenses.sqlite"

    @contextmanager
    def license_connection():
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    namespace = {
        "datetime": datetime, "sqlite3": sqlite3, "re": re, "hmac": hmac,
        "hashlib": hashlib, "license_connection": license_connection,
        "get_admin_username": lambda: "TEST_OWNER", "_audit": lambda *args: None,
        "_secret": lambda name, default="": default,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)
    with license_connection() as connection:
        connection.execute(
            """CREATE TABLE licenses (
                id INTEGER PRIMARY KEY, customer_name TEXT NOT NULL,
                access_code_hash TEXT UNIQUE, access_code_display TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL, expires_at TEXT NOT NULL, is_active INTEGER NOT NULL,
                created_card_until TEXT, plan_label TEXT
            )"""
        )
        connection.commit()

    codes, expiry = namespace["create_access_code_batch"]("khbr", 1000, 30, "1 ខែ")
    assert len(codes) == 1000
    assert len(set(codes)) == 1000
    assert codes[0] == "KHBR-0001" and codes[-1] == "KHBR-1000"
    assert expiry > datetime.datetime.now(datetime.timezone.utc)
    with license_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM licenses").fetchone()[0] == 1000

    next_codes, _ = namespace["create_access_code_batch"]("KHBR", 10, 30, "1 ខែ")
    assert next_codes[0] == "KHBR-1001" and next_codes[-1] == "KHBR-1010"
    try:
        namespace["create_access_code_batch"]("KHBR", 1001, 30, "1 ខែ")
        raise AssertionError("Expected count validation error")
    except ValueError:
        pass

video_workflow = source_text[source_text.index('with tab_video:'):source_text.index('st.subheader("Generated SRT")')]
assert "khemra-wait-card" in source_text
assert "⏱️ {percent}" not in video_workflow
assert "{minutes:02d}:{seconds:02d}" not in video_workflow
assert "aecho=" not in source_text
assert "MAX_TEMPO_SPEED = 1.28" in source_text
print("Bulk Access Code and calm waiting UI tests: OK")

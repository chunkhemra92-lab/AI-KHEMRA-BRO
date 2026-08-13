import ast
import asyncio
import tempfile
from pathlib import Path

import edge_tts

source_path = Path(__file__).with_name("app.py")
tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
needed_assignments = {"PISITH", "SREYMOM", "VOICE_PROFILES"}
needed_functions = {"normalize_dialogue", "prepare_tts_text", "synthesize"}
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in needed_assignments for name in names):
            nodes.append(node)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in needed_functions:
        nodes.append(node)

namespace = {"re": __import__("re"), "asyncio": asyncio, "edge_tts": edge_tts}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)

async def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        folder = Path(temp_dir)
        normal = folder / "normal.mp3"
        thought = folder / "thought.mp3"
        text = "កុំបារម្ភអីណា ខ្ញុំនឹងដោះស្រាយវា។"
        await namespace["synthesize"](text, namespace["VOICE_PROFILES"]["M"], normal)
        await namespace["synthesize"](text, namespace["VOICE_PROFILES"]["M_THINK"], thought)
        assert normal.exists() and normal.stat().st_size > 500
        assert thought.exists() and thought.stat().st_size > 500

asyncio.run(main())
print("Live Edge-TTS Khmer profile generation: OK")

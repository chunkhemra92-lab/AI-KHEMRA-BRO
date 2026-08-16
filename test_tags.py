import ast
import re

source = open('app.py', encoding='utf-8').read()
tree = ast.parse(source)
names = {'_voice_tag_key', 'compact_voice_tag', 'is_known_voice_tag', 'parse_srt', 'srt_to_structured_cues'}
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
ns = {'re': re}
exec(compile(ast.Module(body=selected, type_ignores=[]), 'app.py', 'exec'), ns)

assert ns['compact_voice_tag']('ស្រី') == 'F'
assert ns['compact_voice_tag']('ប្រុស') == 'M'
assert ns['compact_voice_tag']('ស្រីគិតក្នុងចិត្ត') == 'F_THINK'
assert ns['compact_voice_tag']('ប្រុស_គិត_ក្នុង_ចិត្ត') == 'M_THINK'

srt = '''1\n00:00:00,000 --> 00:00:02,000\n[ស្រីគិតក្នុងចិត្ត] ខ្ញុំមិនអាចប្រាប់គាត់បានទេ\n\n2\n00:00:02,000 --> 00:00:04,000\n[ប្រុស] តើអ្នកទៅណា?\n'''
parsed = ns['parse_srt'](srt)
assert [row['tag'] for row in parsed] == ['F_THINK', 'M']
assert all(row['explicit_tag'] for row in parsed)
assert ns['srt_to_structured_cues'](srt)[0]['explicit_tag'] is True
print('tag regression tests passed')

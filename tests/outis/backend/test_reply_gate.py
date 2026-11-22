"""CB-35: a finished reply with an ASCII diagram or its own open checklist items gets one more model pass.

Run inside an Open WebUI container: docker exec -i -w /app/backend <container> python3 - < this file
scripts/outis-regression.sh runs it against the image under test.
"""
import asyncio

from open_webui.utils.outis_reply_gate import ReplyGate, ascii_diagrams, gate_note, rendered_fences, splice

BOX = '```\n┌──────┐\n│ Leader │──► Append\n└──────┘\n   ▼\n```'
PLUS = '```text\n+------+     +------+\n| A    | --> | B    |\n+------+     +------+\n```'
FORMULA = '```\ncwnd += 1 segment   per ACK\n```'
LOGS = '```\nA: [1:1, 1:2*]    (crashed)\nB: [1:1, 1:2*, 2:3*]\n```'
MERMAID = '```mermaid\nflowchart LR\n  A --> B\n```'
GO = '```go\nfunc main() {\n\t// ┌─ not a diagram, real code\n}\n```'

# Detection: box art and +---+ art yes; formulas, logs, code and rendered fences no.
assert ascii_diagrams(f'x\n{BOX}\ny\n{PLUS}') == [BOX, PLUS]
assert ascii_diagrams('\n'.join([FORMULA, LOGS, MERMAID, GO])) == []
assert rendered_fences(f'{MERMAID}\n{GO}\n```dot\ndigraph {{a->b}}\n```') == [MERMAID, '```dot\ndigraph {a->b}\n```']

# Note: only what is wrong, ids named.
assert gate_note(0, []) is None
note = gate_note(2, [{'id': 'example', 'status': 'in_progress'}])
assert 'example' in note and 'update_task' in note and 'ONLY 2' in note, note
assert 'ASCII' not in gate_note(0, [{'id': 't1', 'status': 'pending'}])

# Splice: same count replaces in place; wrong count changes nothing.
reply = [{'type': 'message', 'content': [{'type': 'output_text', 'text': f'Intro\n{BOX}\nmid\n{PLUS}\nend'}]}]
dot = '```dot\ndigraph { a -> b }\n```'
redraw = [{'type': 'message', 'content': [{'type': 'output_text', 'text': f'{MERMAID}\n\n{dot}'}]}]
assert splice(reply, redraw, [BOX, PLUS])
assert reply[0]['content'][0]['text'] == f'Intro\n{MERMAID}\nmid\n{dot}\nend', reply
kept = [{'type': 'message', 'content': [{'type': 'output_text', 'text': f'a\n{BOX}'}]}]
assert not splice(kept, redraw, [BOX]) and BOX in kept[0]['content'][0]['text']


# The gate: asks once, then splices and drops the extra message.
def run_gate(first_text, open_tasks, second_items, enabled=True):
    output = [{'type': 'message', 'content': [{'type': 'output_text', 'text': first_text}]}]
    dropped = []

    async def tasks():
        return open_tasks

    gate = ReplyGate(lambda: output, tasks, lambda: enabled)
    tool_calls = []

    async def go():
        asked = await gate.check(tool_calls, dropped.extend)
        note = gate.take_note()
        if asked:
            output.extend(second_items)  # what the extra model pass returned
        again = await gate.check(tool_calls, dropped.extend)
        return asked, note, again

    asked, note, again = asyncio.run(go())
    return asked, note, again, tool_calls, output, dropped


second = [{'type': 'message', 'content': [{'type': 'output_text', 'text': MERMAID}]}]
asked, note, again, calls, output, dropped = run_gate(f'Answer\n{BOX}', [], second)
assert asked and calls == [[]] and 'ONLY 1' in note and not again
assert output[0]['content'][0]['text'] == f'Answer\n{MERMAID}' and dropped == second

asked, note, *_ = run_gate(f'Answer\n{MERMAID}', [], second)
assert not asked and note is None  # clean reply: no extra pass

asked, note, again, calls, output, dropped = run_gate(
    'Done', [{'id': 's2', 'status': 'pending'}],
    [{'type': 'function_call', 'name': 'update_task'}, {'type': 'message', 'content': [{'type': 'output_text', 'text': 'ok'}]}])
assert asked and 's2' in note and dropped == [output[2]]  # tasks-only pass: its chatter is dropped, the call stays

asked, *_ = run_gate(f'Answer\n{BOX}', [], second, enabled=False)
assert not asked  # Continue, stop reason or tool-call limit
print('CB-35 pass')

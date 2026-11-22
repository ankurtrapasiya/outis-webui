"""Fork (CB-35): one extra model pass when a finished reply draws a diagram as ASCII art or leaves its own
checklist items open. Design: docs/superpowers/specs/2026-11-22-reply-gate-design.md.

The detection and splice functions are pure so tests/outis/backend/test_reply_gate.py can check them without
a model. ReplyGate is the small state machine the tool loop in utils/middleware.py drives:
check() before the gate pass (detect, queue the note, request one more round) and after it (splice, finish).
"""

import re
from typing import Awaitable, Callable

RENDERED_LANGS = {'mermaid', 'dot', 'graphviz', 'plantuml', 'puml', 'c4', 'c4plantuml'}
PLAIN_LANGS = {'', 'text', 'txt', 'plain', 'ascii'}
BOX_CHARS = set('┌┐└┘├┤┬┴┼─│═║╔╗╚╝╠╣╦╩╬▼▲►◄')
FENCE = re.compile(r'^(?P<tick>`{3,})(?P<lang>[^\n`]*)\n(?P<body>.*?)^(?P=tick)[ \t]*$', re.M | re.S)
PLUS_BORDER = re.compile(r'^\s*\+[-=]{2,}\+(\s*\+[-=]{2,}\+)*\s*$')


def _is_ascii_diagram(body: str) -> bool:
    lines = body.splitlines()
    box_lines = sum(1 for line in lines if any(ch in BOX_CHARS for ch in line))
    plus_lines = sum(1 for line in lines if PLUS_BORDER.match(line))
    return box_lines >= 3 or plus_lines >= 2


def ascii_diagrams(text: str) -> list[str]:
    """The full fences (``` lines included) in text that draw a diagram with characters."""
    return [
        m.group(0)
        for m in FENCE.finditer(text or '')
        if m.group('lang').strip().lower() in PLAIN_LANGS and _is_ascii_diagram(m.group('body'))
    ]


def rendered_fences(text: str) -> list[str]:
    """The full mermaid / dot / plantuml fences in text, in order."""
    return [m.group(0) for m in FENCE.finditer(text or '') if m.group('lang').strip().lower() in RENDERED_LANGS]


def gate_note(diagram_count: int, open_tasks: list[dict]) -> str | None:
    if not diagram_count and not open_tasks:
        return None
    asks = []
    if open_tasks:
        ids = ', '.join(t['id'] for t in open_tasks)
        asks.append(
            f'Your checklist still has open items ({ids}). Call update_task for each: completed if your reply '
            'did it, cancelled if it no longer applies.'
        )
    if diagram_count:
        asks.append(
            f'Your reply drew {diagram_count} diagram(s) as ASCII/box-drawing text, which the chat cannot render. '
            f'Answer with ONLY {diagram_count} fenced block(s), in the same order, each the same diagram as a '
            '```mermaid, ```dot or ```plantuml fence. No other text: they replace the ASCII blocks in place.'
        )
    else:
        asks.append('Then stop: do not write any more text.')
    return '<reply_check>\n' + '\n'.join(asks) + '\n</reply_check>'


def _texts(item: dict) -> list[dict]:
    if item.get('type') != 'message' or not isinstance(item.get('content'), list):
        return []
    return [part for part in item['content'] if isinstance(part, dict) and isinstance(part.get('text'), str)]


def splice(before: list[dict], after: list[dict], blocks: list[str]) -> bool:
    """Replace each ASCII block in the reply items `before` with the matching rendered fence from the gate
    pass items `after`, in order. Only when the counts match; returns whether it did."""
    if not blocks:
        return False
    fences = rendered_fences('\n'.join(part['text'] for item in after for part in _texts(item)))
    if len(fences) != len(blocks):
        return False
    pending = list(zip(blocks, fences))
    for item in before:
        for part in _texts(item):
            while pending and pending[0][0] in part['text']:
                block, fence = pending.pop(0)
                part['text'] = part['text'].replace(block, fence, 1)
    return not pending


class ReplyGate:
    def __init__(
        self,
        full_output: Callable[[], list[dict]],
        open_tasks: Callable[[], Awaitable[list[dict]]],
        enabled: Callable[[], bool],
    ):
        self.full_output = full_output
        self.open_tasks = open_tasks
        self.enabled = enabled
        self.state = 'idle'  # idle -> asked -> done
        self.note = None
        self.marker = 0
        self.blocks: list[str] = []

    def take_note(self) -> str | None:
        note, self.note = self.note, None
        return note

    async def check(self, tool_calls: list, drop: Callable[[list[dict]], None]) -> bool:
        """Called when the tool loop would end. True means: run one more (empty) round with the note."""
        if self.state == 'done':
            return False
        if self.state == 'asked':
            self.state = 'done'
            output = self.full_output()
            before, after = output[: self.marker], output[self.marker :]
            spliced = splice(before, after, self.blocks)
            if spliced or not self.blocks:
                drop([item for item in after if item.get('type') == 'message'])
            return False
        self.state = 'done'
        if not self.enabled():
            return False
        text = '\n'.join(part['text'] for item in self.full_output() for part in _texts(item))
        self.blocks = ascii_diagrams(text)
        self.note = gate_note(len(self.blocks), await self.open_tasks())
        if not self.note:
            return False
        self.state = 'asked'
        self.marker = len(self.full_output())
        tool_calls.append([])
        return True

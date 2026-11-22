# Reply gate: redraw ASCII diagrams, close open tasks (CB-35)

Date: 2026-11-22. Criterion: CB-35 in `tests/outis/specs/SPEC-chat-behaviour.md`. Follows CB-34
(`2026-11-22-task-checklist-per-branch-design.md`), which left this second pass out.

## Problem

Prompt rules are not enough. With the global "never ASCII diagrams" rule live, Systems Tutor
(deepseek-v4-flash) still put one box-drawing diagram in each of two Raft/Paxos replies next to a
correct Mermaid one, and earlier replies ended with checklist items open.

## Design

One extra model pass per reply, at most, when the finished reply has either problem:

1. **Detect** (`utils/outis_reply_gate.py`, pure functions):
   - an ASCII diagram: a code fence whose language is empty, `text`, `txt`, `plain` or `ascii`, and
     whose body has 3+ lines with box-drawing characters (`┌ ─ │ └ ▼ ...`) or 2+ `+---+` border lines.
     Since 2026-11-22 (second deploy) also arrow flows: 2+ lines with `→ ← ↑ ↓ ↔ ⇒`, `-->`, `<--` or `==>`,
     or one such line plus a line holding only an arrow (the `Prepare → Promise` block that got past the
     first version). One arrow line alone (a limit, a signature) and C's `->` do not count.
     Formula, log or code blocks have neither, so they pass. Known false positive: a plain block with two
     lines of maths arrows (`f: X → Y`, `g: Y → Z`) gets a redraw request.
   - open tasks: the chat's checklist is on this reply's branch (CB-34) and has pending or
     in_progress items, and the model has `update_task`.
2. **Ask once.** The tool loop (`while tool_calls`) runs one more round with no tool calls and a
   user-role note after the model's reply: close the open items with `update_task`, and reply with
   only the N replacement diagrams as mermaid, dot or plantuml fences, in order.
3. **Splice.** When that round ends, if it returned exactly N rendered fences, each ASCII block in the
   original reply is replaced by its fence and the extra message is dropped, so the reader sees one
   clean reply. A tasks-only pass also drops its message. A wrong count keeps both (the redraw shows
   after the reply) rather than guess a mapping.
4. Skipped when: Continue, a stateful Responses API chat, the tool-call limit or a stop reason is
   already hit, or the chat is not saved (no tasks).

Kept small in upstream's file: the loop condition, one note append in the follow-up request, and
the gate object; the logic lives in the new module.

## Cost

One extra model call only on replies that break a rule. Measured trigger rate today: 2 of 2
Systems Tutor Raft/Paxos replies (ASCII), so for that model it is often, until it learns the rule.

## Check

`tests/outis/backend/test_reply_gate.py`: detection (box art yes; formulas, logs, mermaid no), note
text, splice by count, mismatch keeps both. The loop wiring is covered by the regression suite
running the image; there is no live model in CI.

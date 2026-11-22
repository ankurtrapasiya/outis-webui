# Task checklist follows the reply branch (CB-34)

Date: 2026-11-22. Criterion: CB-34 in `tests/outis/specs/SPEC-chat-behaviour.md`.

## Problem

`create_tasks` stores one checklist on the chat row (`chat.tasks`). A regenerated reply is a sibling
of the reply that made the list, yet CB-33 put that list in front of it as "still open", and the UI
kept showing the old items. Seen in the Raft chat on 2026-11-21: the first reply was cut off with
"safety-arg" in progress; the regenerate inherited it, rewrote the list and still ended with two
items open.

## Design

1. `create_tasks` writes the creating reply's id on every item (`message_id`). `update_task` edits
   items in place, so the id survives.
2. At the start of a turn (the CB-33 spot in `process_chat_payload`), the list is kept only if every
   owner id is the current reply or one of its ancestors in the chat history. Otherwise the reply
   belongs to another branch (regenerate, edited message, switched branch): the list is cleared on
   the chat row, the UI gets an empty list, and no `<open_tasks>` note is sent.
3. A list with no owner ids (made before this change) or a reply missing from the history keeps
   today's behaviour.
4. The `create_tasks` / `update_task` descriptions tell the model to mark every item completed or
   cancelled before its final answer.

## Not done

A second model pass when a reply ends with open items. The tool loop only calls the model again
while there are tool calls, so it needs either a copy of the follow-up path (about 100 lines) or a
fake tool call. Revisit if models keep ending with open items after point 4.

## Check

`tests/outis/backend/test_builtin_tools.py`: `tasks_on_branch` keeps an ancestor's list, drops a
sibling's, keeps legacy lists, and `create_tasks` items carry `message_id`.

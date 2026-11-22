"""CB-30, CB-31: a model is not offered the create_tool built-in, or the other creators, unless its own settings opt in.

Saving a tool executes the Python it was given on the server. Upstream offers create_tool to every model when
the chat user is an admin; a model (qf-lab, 2026-11-15) used that to create two tools nobody asked for.

Run inside an Open WebUI container: docker exec -i -w /app/backend <container> python3 - < this file
scripts/outis-regression.sh runs it against the image under test.
"""
import asyncio
from types import SimpleNamespace

from open_webui.utils.tools import get_builtin_tools


def offered(meta, note_chat=False):
    request = SimpleNamespace(state=SimpleNamespace(internal=False))
    model = {'id': 'm', 'info': {'meta': meta}}
    user = {'id': 'u1', 'role': 'admin', 'email': 'u1@example.invalid', 'name': 'U1', 'last_active_at': 0, 'updated_at': 0, 'created_at': 0}
    extra = {'__user__': user, '__metadata__': {}}
    return set(asyncio.run(get_builtin_tools(request, extra, {}, model, note_chat)))


assert 'create_tool' not in offered({}), 'default must be off'
assert 'create_tool' not in offered({'builtinTools': {'tools': False}})
assert 'create_tool' in offered({'builtinTools': {'tools': True}}), 'an explicit opt-in still works'
assert offered({}), 'the other built-ins are still offered'
print('CB-30 pass')

# CB-31: the other creators (create_skill is the one a default install always has for an admin; notes, automations and
# calendar depend on config that may be off, so they are only checked for absence)
CREATORS = {'write_note', 'create_skill', 'create_automation', 'create_calendar_event'}
assert not CREATORS & offered({}), CREATORS & offered({})
assert not CREATORS & offered({'builtinTools': {'create': False}})
assert 'create_skill' in offered({'builtinTools': {'create': True}}), 'an explicit opt-in still works'
assert 'write_note' in offered({}, note_chat=True), 'a note chat can still write its note'
assert 'create_tool' not in offered({'builtinTools': {'create': True}}), 'create_tool has its own switch'
print('CB-31 pass')

# CB-33: open checklist items are put back in front of the model each turn
from open_webui.tools.builtin import open_tasks_note

assert open_tasks_note(None) is None and open_tasks_note([]) is None
assert open_tasks_note([{'id': 'a', 'content': 'x', 'status': 'completed'}, {'id': 'b', 'content': 'y', 'status': 'cancelled'}]) is None
note = open_tasks_note([{'id': 'b1', 'content': 'done one', 'status': 'completed'},
                        {'id': 'b2', 'content': 'Diagnose overfit', 'status': 'in_progress'},
                        {'id': 'b3', 'content': 'Implement', 'status': 'pending'}])
assert '- b2 [in_progress] Diagnose overfit' in note and '- b3 [pending] Implement' in note, note
assert 'done one' not in note and 'update_task' in note, note
print('CB-33 pass')

# CB-34: a checklist belongs to the reply branch that made it
import asyncio, inspect
from open_webui.tools.builtin import tasks_on_branch, create_tasks, update_task

history = {'u1': {'parentId': None}, 'a1': {'parentId': 'u1'}, 'u2': {'parentId': 'a1'}, 'a2': {'parentId': 'u2'},
           'a1b': {'parentId': 'u1'}}  # a1b regenerates a1
owned = [{'id': 'x', 'content': 'c', 'status': 'in_progress', 'message_id': 'a1'}]
assert tasks_on_branch(owned, history, 'a1')        # the reply that made it (continue)
assert tasks_on_branch(owned, history, 'a2')        # a later turn on the same branch
assert not tasks_on_branch(owned, history, 'a1b')   # a regenerate is a sibling
assert tasks_on_branch([{'id': 'x', 'content': 'c', 'status': 'pending'}], history, 'a1b')  # pre-CB-34 list kept
assert tasks_on_branch(owned, history, 'missing') and tasks_on_branch(owned, None, 'a1b')  # unknown: keep
assert tasks_on_branch([], history, 'a1b')
assert 'before your final answer' in inspect.getdoc(create_tasks).lower()
assert 'before your final answer' in inspect.getdoc(update_task).lower()

stored = {}
from open_webui.models import chats as chats_mod
async def fake_update(chat_id, tasks): stored[chat_id] = tasks
orig = chats_mod.Chats.update_chat_tasks_by_id
chats_mod.Chats.update_chat_tasks_by_id = fake_update
import open_webui.tools.builtin as builtin_mod
orig_saved = builtin_mod.is_saved_chat_id
builtin_mod.is_saved_chat_id = lambda _id: True
try:
    asyncio.run(create_tasks([{'content': 'Find paper'}, {'content': 'Explain', 'status': 'in_progress'}],
                             __chat_id__='c1', __message_id__='a1'))
finally:
    chats_mod.Chats.update_chat_tasks_by_id = orig
    builtin_mod.is_saved_chat_id = orig_saved
assert [t['message_id'] for t in stored['c1']] == ['a1', 'a1'], stored
print('CB-34 pass')

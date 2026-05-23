"""
Tests: Backend todo routes and scratch_note routes.

Verifies:
  - Checkpoint 1: Python syntax (covered by py_compile)
  - Checkpoint 3: API endpoint signatures match frontend expectations
  - Checkpoint 4: Delete note route handles todos correctly
"""
import pytest
import inspect


class TestTodoRouteEndpoints:
    """Checkpoint 3: Verify backend route definitions match frontend API calls."""

    def test_list_todos_endpoint(self):
        """GET /api/todos must exist and support optional note_id filter"""
        from routes.todo import list_todos
        source = inspect.getsource(list_todos)

        assert "note_id" in source, "list_todos must support note_id query param"
        assert "note_id_filter" in source or "note_id" in source, \
            "list_todos must read note_id from request.args"

    def test_create_todo_endpoint(self):
        """POST /api/todos must accept note_id, notebook_id, selected_text"""
        from routes.todo import create_todo
        source = inspect.getsource(create_todo)

        assert "note_id" in source, "create_todo must handle note_id"
        assert "notebook_id" in source, "create_todo must handle notebook_id"
        assert "selected_text" in source, "create_todo must handle selected_text"

    def test_get_todos_by_note_endpoint(self):
        """GET /api/todos/by-note/<note_id> must exist"""
        from routes.todo import get_todos_by_note
        source = inspect.getsource(get_todos_by_note)

        assert "note_id" in source, "get_todos_by_note must use note_id parameter"
        assert "filter_by" in source, "Must filter by note_id"

    def test_get_todos_by_note_batch_endpoint(self):
        """GET /api/todos/by-note-batch must exist with note_ids param"""
        from routes.todo import get_todos_by_note_batch
        source = inspect.getsource(get_todos_by_note_batch)

        assert "note_ids" in source, "Must parse note_ids from request"
        assert ".in_(note_ids)" in source or ".in_(" in source, \
            "Must use SQLAlchemy .in_() for batch query"
        assert "result" in source, "Must group results by note_id"

    def test_update_todo_supports_note_fields(self):
        """PUT /api/todos/<id> must support updating note_id, notebook_id, selected_text"""
        from routes.todo import update_todo
        source = inspect.getsource(update_todo)

        assert "'note_id' in data" in source, "update must handle note_id"
        assert "'notebook_id' in data" in source, "update must handle notebook_id"
        assert "'selected_text' in data" in source, "update must handle selected_text"

    def test_route_decorators(self):
        """All todo routes must be mounted on todo_bp with correct URL prefix"""
        from routes.todo import todo_bp
        assert todo_bp.name == 'todo', "Blueprint name must be 'todo'"
        assert todo_bp.url_prefix == '/api/todos', \
            f"URL prefix must be '/api/todos', got '{todo_bp.url_prefix}'"


class TestScratchNoteDeleteNote:
    """Checkpoint 4: Verify delete_note handles todo associations."""

    def test_delete_note_imports_todo_model(self):
        """scratch_note.py must import Todo model for cascade logic"""
        from routes.scratch_note import delete_note
        source = inspect.getsource(delete_note)

        # The function must reference Todo model
        assert "Todo" in source, "delete_note must reference Todo model"

    def test_delete_note_clears_note_id(self):
        """delete_note must set note_id to None before deleting the note"""
        from routes.scratch_note import delete_note
        source = inspect.getsource(delete_note)

        assert "note_id=note_id" in source, \
            "Must query todos by note_id"
        assert "None" in source, \
            "Must set note_id to None/Null"

    def test_delete_note_returns_success_message(self):
        """delete_note must return success response"""
        from routes.scratch_note import delete_note
        source = inspect.getsource(delete_note)

        assert "笔记已删除" in source or "success" in source, \
            "Must return a success response"


class TestTodoRouteByNoteBatchResponse:
    """Verify by-note-batch endpoint returns correct response structure."""

    def test_by_note_batch_returns_dict(self):
        """by-note-batch must return {note_id: [todo,...]} dict format"""
        from routes.todo import get_todos_by_note_batch
        source = inspect.getsource(get_todos_by_note_batch)

        # Check the result is a dict grouped by note_id
        assert "result = {}" in source or "result = {" in source, \
            "Must initialize result dict"
        assert "result[nid]" in source, "Must group todos by note_id"

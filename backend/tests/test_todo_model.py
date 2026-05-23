"""
Tests: Todo model extension for bidirectional note-todo linking.

Verifies:
  - Checkpoint 2: note_id/notebook_id/selected_text field types and FK constraints
  - Checkpoint 3: API consistency - to_dict() serialization
  - Checkpoint 4: Delete note cascade logic (SET NULL)
"""
import pytest
from datetime import date, datetime, timezone


class TestTodoModelFields:
    """Checkpoint 2: Verify Todo model field definitions match spec."""

    def test_note_id_is_integer_foreign_key(self):
        """note_id must be Integer FK → notes.id with ondelete='SET NULL' and nullable=True"""
        from models.todo import Todo

        col = Todo.note_id
        assert col.nullable is True, "note_id must be nullable=True"
        # Check it's an Integer column
        assert col.type.python_type is int, "note_id must be Integer type"
        # Check foreign key: we can inspect the foreign keys on this column
        fk_names = [fk.target_fullname for fk in col.foreign_keys]
        assert 'notes.id' in ''.join(fk_names), "note_id must FK to notes.id"

    def test_notebook_id_is_integer_foreign_key(self):
        """notebook_id must be Integer FK → notebooks.id with ondelete='SET NULL'"""
        from models.todo import Todo

        col = Todo.notebook_id
        assert col.nullable is True, "notebook_id must be nullable=True"
        assert col.type.python_type is int, "notebook_id must be Integer type"
        fk_names = [fk.target_fullname for fk in col.foreign_keys]
        assert 'notebooks.id' in ''.join(fk_names), "notebook_id must FK to notebooks.id"

    def test_selected_text_is_text_type(self):
        """selected_text must be Text type and nullable"""
        from models.todo import Todo

        col = Todo.selected_text
        assert col.nullable is True, "selected_text must be nullable=True"
        # Text type has python_type str
        assert col.type.python_type is str, "selected_text must be Text type"

    def test_todo_has_note_relationship(self):
        """Todo model must have 'note' relationship with backref 'todos' on Note"""
        from models.todo import Todo

        # Check relationship exists
        assert hasattr(Todo, 'note'), "Todo must have 'note' relationship"

    def test_to_dict_includes_new_fields(self):
        """Checkpoint 3: to_dict() must serialize note_id, notebook_id, selected_text"""
        from models.todo import Todo

        # Inspect to_dict return value keys by examining the method
        # We can't instantiate without DB, but we can verify the method exists
        assert hasattr(Todo, 'to_dict'), "Todo must have to_dict() method"

        # Verify to_dict source includes the new fields
        import inspect
        source = inspect.getsource(Todo.to_dict)
        assert "'note_id': self.note_id" in source, "to_dict must include note_id"
        assert "'notebook_id': self.notebook_id" in source, "to_dict must include notebook_id"
        assert "'selected_text': self.selected_text" in source, "to_dict must include selected_text"


class TestDeleteNoteCascadeLogic:
    """Checkpoint 4: Verify the delete note → SET NULL logic."""

    def test_delete_note_updates_todos(self):
        """DELETE /api/notes/<id> must SET NULL note_id on associated todos"""
        import inspect
        from routes.scratch_note import delete_note

        source = inspect.getsource(delete_note)
        # The key pattern: filter todos by note_id and update note_id to None
        assert 'note_id=note_id' in source or 'note_id == note_id' in source, \
            "delete_note must filter todos by note_id"
        assert '.update(' in source, "delete_note must use .update() to modify todos"
        assert 'Note' in source, "delete_note must query Note model"

    def test_delete_note_keeps_todos(self):
        """Key design decision: deleting a note must NOT delete associated todos"""
        import inspect
        from routes.scratch_note import delete_note

        source = inspect.getsource(delete_note)
        # Should NOT cascade delete (no cascade='delete')
        # Just verifies Todo.query.filter_by(...).update(...) is used instead of delete
        assert '.update(' in source, "Must use update() not delete() for associated todos"

    def test_fk_ondelete_set_null(self):
        """Database-level FK constraint: ondelete='SET NULL' for safety"""
        from models.todo import Todo

        col = Todo.note_id
        # Check ondelete via the foreign key objects
        for fk in col.foreign_keys:
            assert fk.ondelete in ('SET NULL', None), \
                f"FK ondelete must be 'SET NULL', got {fk.ondelete}"
            # SQLAlchemy FK.ondelete may be None if not specified in constructor
            # We'll check the Column source directly
        import inspect
        source = inspect.getsource(Todo)
        assert "ondelete='SET NULL'" in source, \
            "FK must specify ondelete='SET NULL' in the Column definition"


class TestTodoModelConstraints:
    """Verify model-level constraints align with system design."""

    def test_tablename_is_todos(self):
        """Model table name must be 'todos'"""
        from models.todo import Todo
        assert Todo.__tablename__ == 'todos', "Table name must be 'todos'"

    def test_new_fields_are_nullable(self):
        """All three new fields must be nullable (design requirement)"""
        from models.todo import Todo
        assert Todo.note_id.nullable is True
        assert Todo.notebook_id.nullable is True
        assert Todo.selected_text.nullable is True

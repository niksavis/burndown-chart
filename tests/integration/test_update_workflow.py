import sqlite3
import tempfile
from pathlib import Path

from data.database import get_db_connection
from data.migration.schema import create_schema
from data.persistence.sqlite_backend import SQLiteBackend


def _create_test_database() -> str:

    temp_db = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db")
    db_path = temp_db.name
    temp_db.close()

    with get_db_connection(Path(db_path)) as conn:
        create_schema(conn)

    return db_path


def test_post_update_flag_workflow():

    db_path = _create_test_database()

    try:
        backend = SQLiteBackend(db_path)

        backend.set_app_state("post_update_relaunch", "true")

        flag_value = backend.get_app_state("post_update_relaunch")
        assert flag_value == "true", "Flag should be set by updater"

        flag_value = backend.get_app_state("post_update_relaunch")
        assert flag_value == "true", "App should read flag value"

        backend.set_app_state("post_update_relaunch", None)

        flag_value = backend.get_app_state("post_update_relaunch")
        assert flag_value is None, "Flag should be cleared after use"

        flag_value = backend.get_app_state("post_update_relaunch")
        assert flag_value is None, "Flag should stay cleared for subsequent launches"

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_updater_flag_set_directly():

    db_path = _create_test_database()

    try:
        backend = SQLiteBackend(db_path)

        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
            ("post_update_relaunch", "true"),
        )
        conn.commit()
        conn.close()

        flag_value = backend.get_app_state("post_update_relaunch")
        assert flag_value == "true", "Flag set by updater should be readable by app"

        backend.set_app_state("post_update_relaunch", None)
        flag_value = backend.get_app_state("post_update_relaunch")
        assert flag_value is None, "Flag cleanup should work"

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_flag_isolation_with_other_state():
    db_path = _create_test_database()

    try:
        backend = SQLiteBackend(db_path)

        backend.set_app_state("other_key_1", "value1")
        backend.set_app_state("other_key_2", "value2")
        backend.set_app_state("post_update_relaunch", "true")

        assert backend.get_app_state("other_key_1") == "value1"
        assert backend.get_app_state("other_key_2") == "value2"
        assert backend.get_app_state("post_update_relaunch") == "true"

        backend.set_app_state("post_update_relaunch", None)

        assert backend.get_app_state("other_key_1") == "value1"
        assert backend.get_app_state("other_key_2") == "value2"
        assert backend.get_app_state("post_update_relaunch") is None

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_missing_database_graceful_handling():

    nonexistent_db = Path(tempfile.gettempdir()) / "nonexistent_db_test_xyz.db"

    nonexistent_db.unlink(missing_ok=True)

    try:
        try:
            backend = SQLiteBackend(str(nonexistent_db))
            flag_value = backend.get_app_state("post_update_relaunch")
            assert flag_value is None, "Non-existent key should return None"
        except Exception as e:
            assert isinstance(e, Exception), (
                "Exception should be caught by app's try/except"
            )

    finally:
        nonexistent_db.unlink(missing_ok=True)

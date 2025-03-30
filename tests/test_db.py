import os
import sqlite3

import pytest

from lemma.db import (
    create_connection,
    create_tables,
    delete_review,
    get_all_reviews,
    get_review_with_files,
    insert_file,
    insert_review,
)


@pytest.fixture
def temp_db():
    db_file = "test_database.db"
    conn = create_connection(db_file)
    create_tables(conn)
    yield conn
    conn.close()
    os.remove(db_file)


def test_create_connection():
    conn = create_connection(":memory:")
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_create_tables(temp_db):
    cursor = temp_db.cursor()

    # Check if tables exist
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'"
    )
    assert cursor.fetchone() is not None

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
    assert cursor.fetchone() is not None


def test_insert_review(temp_db):
    review_id = insert_review(
        temp_db,
        "Test Review",
        "https://github.com/test",
        "branch",
        "Test Template",
        "Test Prompt",
        "gpt-4",  # Added llm_model parameter
    )
    assert review_id is not None

    cursor = temp_db.cursor()
    cursor.execute("SELECT * FROM reviews WHERE id=?", (review_id,))
    review = cursor.fetchone()
    assert review is not None
    assert review[1] == "Test Review"


def test_insert_file(temp_db):
    review_id = insert_review(
        temp_db,
        "Test Review",
        "https://github.com/test",
        "branch",
        "Test Template",
        "Test Prompt",
        "gpt-4",  # Added llm_model parameter
    )
    file_id = insert_file(
        temp_db, review_id, "test.py", "test diff", "test code", "test response"
    )
    assert file_id is not None

    cursor = temp_db.cursor()
    cursor.execute("SELECT * FROM files WHERE id=?", (file_id,))
    file = cursor.fetchone()
    assert file is not None
    assert file[2] == "test.py"


def test_delete_review(temp_db):
    review_id = insert_review(
        temp_db,
        "Test Review",
        "https://github.com/test",
        "branch",
        "Test Template",
        "Test Prompt",
        "gpt-4",  # Added llm_model parameter
    )
    insert_file(
        temp_db, review_id, "test.py", "test diff", "test code", "test response"
    )

    delete_review(temp_db, review_id)

    cursor = temp_db.cursor()
    cursor.execute("SELECT * FROM reviews WHERE id=?", (review_id,))
    assert cursor.fetchone() is None

    cursor.execute("SELECT * FROM files WHERE review_id=?", (review_id,))
    assert cursor.fetchone() is None


def test_get_all_reviews(temp_db):
    insert_review(
        temp_db,
        "Test Review 1",
        "https://github.com/test1",
        "branch",
        "Test Template 1",
        "Test Prompt 1",
        "gpt-4",  # Added llm_model parameter
    )
    insert_review(
        temp_db,
        "Test Review 2",
        "https://github.com/test2",
        "file_path",
        "Test Template 2",
        "Test Prompt 2",
        "gpt-4",  # Added llm_model parameter
    )

    reviews = get_all_reviews(temp_db)
    assert len(reviews) == 2
    assert reviews[0][1] == "Test Review 2"  # Assuming DESC order
    assert reviews[1][1] == "Test Review 1"


def test_get_all_reviews_empty(temp_db):
    reviews = get_all_reviews(temp_db)
    assert len(reviews) == 0


def test_get_review_with_files(temp_db):
    review_id = insert_review(
        temp_db,
        "Test Review",
        "https://github.com/test",
        "commit",
        "Test Template",
        "Test Prompt",
        "gpt-4",  # Added llm_model parameter
    )
    insert_file(
        temp_db, review_id, "test1.py", "test diff 1", "test code 1", "test response 1"
    )
    insert_file(
        temp_db, review_id, "test2.py", "test diff 2", "test code 2", "test response 2"
    )

    review, files = get_review_with_files(temp_db, review_id)
    assert review is not None
    assert review[1] == "Test Review"
    assert len(files) == 2
    assert files[0][2] == "test1.py"
    assert files[1][2] == "test2.py"


def test_get_review_with_files_nonexistent(temp_db):
    review, files = get_review_with_files(temp_db, 999)
    assert review is None
    assert files is None  # Changed from [] to None


def test_create_connection_exception():
    with pytest.raises(Exception):
        create_connection(None)


def test_insert_review_exception(temp_db):
    with pytest.raises(sqlite3.Error) as excinfo:
        insert_review(
            temp_db,
            None,
            "https://github.com/test/pull/123",
            "pull_request",
            "Test Template",
            "Test Prompt",
            "gpt-4",  # Added llm_model parameter
        )
    assert "Database error: Name cannot be None" in str(excinfo.value)

    # Verify that no review was inserted
    cursor = temp_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM reviews")
    count = cursor.fetchone()[0]
    assert count == 0


def test_insert_file_exception(temp_db):
    non_existent_review_id = 999
    with pytest.raises(ValueError) as excinfo:
        insert_file(
            temp_db,
            non_existent_review_id,
            "test.py",
            "test diff",
            "test code",
            "test response",
        )
    assert (
        str(excinfo.value) == f"Review with id {non_existent_review_id} does not exist"
    )

    # Double-check that no file was inserted
    cursor = temp_db.cursor()
    cursor.execute("SELECT * FROM files WHERE review_id=?", (non_existent_review_id,))
    assert cursor.fetchone() is None


def test_delete_review_nonexistent(temp_db):
    delete_review(temp_db, 999)  # Should not raise an exception

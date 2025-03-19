import os
import sqlite3
import uuid
from sqlite3 import Error


def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file"""
    conn = None
    try:
        # Ensure the directory exists
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        conn = sqlite3.connect(db_file)
        print(f"SQLite Database created and connected to {db_file}")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Error as e:
        print(f"Error: {e}")
    return conn


def create_tables(conn):
    """Create tables in the SQLite database"""
    try:
        sql_create_projects_table = """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            github_repo_url TEXT NOT NULL,
            repo_validated BOOLEAN NOT NULL CHECK (repo_validated IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );"""

        sql_create_reviews_table = """
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            github_url TEXT NOT NULL,
            github_url_type VARCHAR(100) NULL,
            prompt_template TEXT NULL,
            prompt TEXT NULL,
            llm_model VARCHAR(100) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            project_id TEXT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        );"""

        sql_create_files_table = """
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            review_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            diff TEXT,
            code TEXT,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (review_id) REFERENCES reviews (id)
        );"""

        sql_create_repository_embeddings = """
         CREATE TABLE IF NOT EXISTS repository_embeddings (
            id TEXT PRIMARY KEY,
            branch VARCHAR(255) NULL,
            commit_indexed VARCHAR(50) NULL,
            last_indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) NOT NULL CHECK (status IN ('unindexed', 'in_progress', 'indexed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            project_id TEXT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id)
         );"""

        c = conn.cursor()
        c.execute(sql_create_projects_table)
        c.execute(sql_create_reviews_table)
        c.execute(sql_create_files_table)
        c.execute(sql_create_repository_embeddings)

        # Create triggers to automatically update the updated_at field
        table_triggers = ["reviews", "files", "projects", "repository_embeddings"]
        trigger_template = """
            CREATE TRIGGER IF NOT EXISTS trg_{table}_updated_at
            AFTER UPDATE ON {table}
            FOR EACH ROW
            BEGIN
                UPDATE {table} SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
        """
        for table in table_triggers:
            query = trigger_template.format(table=table)
            c.execute(query)

        # Create indexes
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_reviews_project_id ON reviews(project_id)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews (created_at)"
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_files_review_id ON files(review_id)")
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_repository_embeddings_project_id ON repository_embeddings(project_id)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects (updated_at)"
        )
    except Error as e:
        raise Error(f"Database error: {e}")


def insert_review(
    conn,
    name,
    github_url,
    github_url_type,
    prompt_template,
    prompt,
    llm_model,
    project_id=None,
) -> int:
    """Insert a new review into the reviews table"""
    try:
        if name is None:
            raise ValueError("Name cannot be None")
        review_id = str(uuid.uuid4())
        sql_insert_review = """INSERT INTO reviews(id, name, github_url, github_url_type, prompt_template, prompt, llm_model, project_id)
                              VALUES(?,?,?,?,?,?,?,?)"""
        cur = conn.cursor()
        cur.execute(
            sql_insert_review,
            (
                review_id,
                name,
                github_url,
                github_url_type,
                prompt_template,
                prompt,
                llm_model,
                project_id,
            ),
        )
        conn.commit()
        return review_id
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Database error: {e}")
    except ValueError as e:
        raise sqlite3.Error(f"Database error: {e}")


def insert_file(conn, review_id, file_name, diff, code, response) -> int:
    """Insert a new file into the files table"""
    try:
        c = conn.cursor()
        # First, check if the review exists
        c.execute("SELECT id FROM reviews WHERE id=?", (review_id,))
        if c.fetchone() is None:
            raise ValueError(f"Review with id {review_id} does not exist")

        file_id = str(uuid.uuid4())
        c.execute(
            """INSERT INTO files (id, review_id, file_name, diff, code, response)
                     VALUES (?, ?, ?, ?, ?, ?)""",
            (file_id, review_id, file_name, diff, code, response),
        )
        conn.commit()
        return file_id
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Database error: {e}")


def insert_project(conn, name, github_repo_url, repo_validated) -> int:
    """Insert a new project into the projects table"""
    try:
        c = conn.cursor()
        project_id = str(uuid.uuid4())
        repo_validated_int = 1 if repo_validated else 0
        c.execute(
            """INSERT INTO projects (id, name, github_repo_url, repo_validated)
                     VALUES (?, ?, ?, ?)""",
            (project_id, name, github_repo_url, repo_validated_int),
        )
        conn.commit()
        return project_id
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Database error: {e}")


def delete_review(conn, review_id):
    """Delete a review and its associated files from the database"""
    try:
        sql_delete_files = """DELETE FROM files WHERE review_id = ?"""
        sql_delete_review = """DELETE FROM reviews WHERE id = ?"""
        cur = conn.cursor()
        cur.execute(sql_delete_files, (review_id,))
        cur.execute(sql_delete_review, (review_id,))
        conn.commit()
    except Error as e:
        raise Error(f"Database error: {e}")


def get_all_reviews(conn):
    """
    Query all rows in the reviews table
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews order by reviews.created_at DESC")
        rows = cur.fetchall()
        return rows
    except Error as e:
        raise Error(f"Database error: {e}")


def get_review_with_files(conn, review_id):
    """
    Query a review and all its associated files
    """
    try:
        cur = conn.cursor()
        # Fetch the review
        cur.execute("SELECT * FROM reviews WHERE id=?", (review_id,))
        review = cur.fetchone()

        if review:
            # Fetch associated files
            cur.execute("SELECT * FROM files WHERE review_id=?", (review_id,))
            files = cur.fetchall()
            return review, files
        else:
            print("Review not found")
            return None, None
    except Error as e:
        print(f"Error: {e}")
        return None, None


def get_all_projects(conn):
    """
    Query all rows in the projects table
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects order by projects.updated_at DESC")
        rows = cur.fetchall()
        return rows
    except Error as e:
        raise Error(f"Database error: {e}")


def get_all_project_reviews(conn, project_id):
    """
    Query all rows for the project in the reviews table
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM reviews where project_id=? order by reviews.created_at DESC",
            (project_id,),
        )
        rows = cur.fetchall()
        return rows
    except Error as e:
        raise Error(f"Database error: {e}")


def migrate_database(conn):
    """Add new columns to existing tables if they don't exist"""
    try:
        print("Migrating database...")
        c = conn.cursor()
        # Check if llm_model column exists
        c.execute("PRAGMA table_info(reviews)")
        columns = [column[1] for column in c.fetchall()]

        if "llm_model" not in columns:
            c.execute("ALTER TABLE reviews ADD COLUMN llm_model VARCHAR(100)")
            print("Added llm_model column to reviews table")
        if "github_url_type" not in columns:
            c.execute("ALTER TABLE reviews ADD COLUMN github_url_type VARCHAR(100)")
            print("Added github_url_type column to reviews table")
        if "project_id" not in columns:
            c.execute("ALTER TABLE reviews ADD COLUMN project_id TEXT NULL")
            c.execute("FOREIGN KEY (project_id) REFERENCES projects (id)")
            print("Added project_id column to reviews table")
        conn.commit()
    except Error as e:
        print(f"Migration error: {e}")


def db_init(conn):
    """Create tables and run migrations"""
    if conn is not None:
        create_tables(conn)
        migrate_database(conn)
    else:
        raise Exception("Error! Cannot create the database connection.")

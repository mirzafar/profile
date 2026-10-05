"""SQLite data layer for the profile mini-project.

Pure stdlib (sqlite3 + hashlib). No external services, no ORM.
"""
import os
import sqlite3
import hashlib
import hmac
import secrets
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile.db")

SERVICES = ("consultation", "navigator", "support", "other")
STATUSES = ("new", "in_progress", "done", "rejected")


# ---------- connection ----------

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = connect()
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email         TEXT NOT NULL UNIQUE,
                nickname      TEXT UNIQUE,
                name          TEXT,
                phone         TEXT,
                password_hash TEXT,
                salt          TEXT,
                google_sub    TEXT UNIQUE,
                role          TEXT NOT NULL DEFAULT 'user',
                created_at    INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS requests (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
                name       TEXT NOT NULL,
                phone      TEXT NOT NULL,
                email      TEXT,
                service    TEXT NOT NULL DEFAULT 'other',
                message    TEXT,
                status     TEXT NOT NULL DEFAULT 'new',
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS request_notes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id      INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
                author          TEXT NOT NULL,
                text            TEXT NOT NULL,
                visible_to_user INTEGER NOT NULL DEFAULT 0,
                created_at      INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
            CREATE INDEX IF NOT EXISTS idx_requests_user ON requests(user_id);
            CREATE INDEX IF NOT EXISTS idx_notes_request ON request_notes(request_id);
            """
        )
    conn.close()
    _migrate_users()


def _migrate_users():
    """Upgrade an old users table (pre-Google schema) to the new schema.

    Uses its own connection with legacy_alter_table=ON so that renaming the
    table does NOT rewrite the foreign-key reference in `requests`.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)")]
        if "google_sub" in cols:
            return  # already new schema
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("PRAGMA legacy_alter_table=ON")
        conn.executescript(
            """
            BEGIN;
            ALTER TABLE users RENAME TO users_old;
            CREATE TABLE users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email         TEXT NOT NULL UNIQUE,
                nickname      TEXT UNIQUE,
                name          TEXT,
                phone         TEXT,
                password_hash TEXT,
                salt          TEXT,
                google_sub    TEXT UNIQUE,
                role          TEXT NOT NULL DEFAULT 'user',
                created_at    INTEGER NOT NULL
            );
            INSERT INTO users (id, email, nickname, phone, password_hash, salt, role, created_at)
                SELECT id, email, nickname, phone, password_hash, salt, role, created_at FROM users_old;
            DROP TABLE users_old;
            COMMIT;
            """
        )
        conn.execute("PRAGMA legacy_alter_table=OFF")
    finally:
        conn.close()


# ---------- passwords ----------

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return dk.hex(), salt


def verify_password(password, salt, expected_hash):
    calc, _ = hash_password(password, salt)
    return hmac.compare_digest(calc, expected_hash)


# ---------- users ----------

def create_user(email, name=None, nickname=None, phone=None, password=None,
                role="user", google_sub=None):
    pw_hash = salt = None
    if password:
        pw_hash, salt = hash_password(password)
    conn = connect()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO users (email, name, nickname, phone, password_hash, salt, google_sub, role, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (email, name, nickname, phone, pw_hash, salt, google_sub, role, int(time.time())),
            )
            return cur.lastrowid
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = connect()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def get_user_by_email(email):
    conn = connect()
    try:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()


def get_user_by_google_sub(sub):
    conn = connect()
    try:
        return conn.execute("SELECT * FROM users WHERE google_sub = ?", (sub,)).fetchone()
    finally:
        conn.close()


def link_google(user_id, sub, name=None):
    conn = connect()
    try:
        with conn:
            conn.execute(
                "UPDATE users SET google_sub = ?, name = COALESCE(name, ?) WHERE id = ?",
                (sub, name, user_id),
            )
    finally:
        conn.close()


def get_user_by_login(login):
    """login can be a nickname or an email."""
    conn = connect()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE nickname = ? OR email = ?", (login, login)
        ).fetchone()
    finally:
        conn.close()


def nickname_or_email_taken(nickname, email):
    conn = connect()
    try:
        row = conn.execute(
            "SELECT nickname, email FROM users WHERE nickname = ? OR email = ?",
            (nickname, email),
        ).fetchone()
        if row is None:
            return None
        if row["nickname"] == nickname:
            return "nickname"
        return "email"
    finally:
        conn.close()


def update_password(user_id, new_password):
    pw_hash, salt = hash_password(new_password)
    conn = connect()
    try:
        with conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (pw_hash, salt, user_id),
            )
    finally:
        conn.close()


# ---------- requests ----------

def create_request(name, phone, email, service, message, user_id=None):
    if service not in SERVICES:
        service = "other"
    now = int(time.time())
    conn = connect()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO requests (user_id, name, phone, email, service, message, status, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?, 'new', ?, ?)",
                (user_id, name, phone, email, service, message, now, now),
            )
            return cur.lastrowid
    finally:
        conn.close()


def get_requests_for_user(user_id):
    conn = connect()
    try:
        return conn.execute(
            "SELECT * FROM requests WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
    finally:
        conn.close()


def get_request(request_id):
    conn = connect()
    try:
        return conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
    finally:
        conn.close()


def _request_filters(status, query, email):
    where, params = [], []
    if status and status in STATUSES:
        where.append("status = ?")
        params.append(status)
    if query:
        like = f"%{query}%"
        where.append("(name LIKE ? OR phone LIKE ? OR email LIKE ? OR message LIKE ?)")
        params.extend([like, like, like, like])
    if email:
        where.append("email LIKE ?")
        params.append(f"%{email}%")
    return where, params


def list_requests(status=None, query=None, email=None, limit=50, offset=0):
    sql = "SELECT * FROM requests"
    where, params = _request_filters(status, query, email)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    conn = connect()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def count_requests(status=None, query=None, email=None):
    where, params = _request_filters(status, query, email)
    sql = "SELECT COUNT(*) AS n FROM requests"
    if where:
        sql += " WHERE " + " AND ".join(where)
    conn = connect()
    try:
        return conn.execute(sql, params).fetchone()["n"]
    finally:
        conn.close()


def status_counts():
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS n FROM requests GROUP BY status"
        ).fetchall()
        counts = {s: 0 for s in STATUSES}
        for r in rows:
            counts[r["status"]] = r["n"]
        counts["total"] = sum(counts[s] for s in STATUSES)
        return counts
    finally:
        conn.close()


def set_status(request_id, status):
    if status not in STATUSES:
        return False
    conn = connect()
    try:
        with conn:
            conn.execute(
                "UPDATE requests SET status = ?, updated_at = ? WHERE id = ?",
                (status, int(time.time()), request_id),
            )
        return True
    finally:
        conn.close()


# ---------- notes ----------

def add_note(request_id, author, text, visible_to_user=False):
    conn = connect()
    try:
        with conn:
            conn.execute(
                "INSERT INTO request_notes (request_id, author, text, visible_to_user, created_at) "
                "VALUES (?,?,?,?,?)",
                (request_id, author, text, 1 if visible_to_user else 0, int(time.time())),
            )
    finally:
        conn.close()


def get_notes(request_id, only_visible=False):
    sql = "SELECT * FROM request_notes WHERE request_id = ?"
    params = [request_id]
    if only_visible:
        sql += " AND visible_to_user = 1"
    sql += " ORDER BY created_at ASC"
    conn = connect()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()

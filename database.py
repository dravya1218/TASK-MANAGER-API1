
import os
import libsql_client as sqlite3
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("TURSO_DATABASE_URL")
db_token = os.getenv("TURSO_AUTH_TOKEN")


def _store_timestamp(value):
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def _as_dict(row):
    if row is None:
        return None
    return row.asdict()


def get_connetion():

    if not db_url:
        raise ValueError("Database URL is not set")
    if not db_token:
        raise ValueError("Database token is not set")

    conn = sqlite3.create_client_sync(url=db_url, auth_token=db_token)
    return conn


def create_permission_table():
    conn = get_connetion()
    conn.execute("""CREATE TABLE IF NOT EXISTS permissions(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL UNIQUE)""")
    conn.close()


def seed_permission():
    conn = get_connetion()
    conn.execute("""INSERT OR IGNORE INTO permissions (name)
                   VALUES ('create_task'),
                        ('view_task'),
                        ('update_task'),
                        ('delete_task'),
                        ('view_all_users'),
                        ('view_user_task_count'),
                        ('update_user'),
                        ('delete_user'),
                        ('manage_roles')""")
    conn.close()


def create_role_permissions():
    conn = get_connetion()
    conn.execute("""CREATE TABLE IF NOT EXISTS role_permissions(
                 role_id INTEGER NOT NULL,
                 permission_id INTEGER NOT NULL,
                 UNIQUE(role_id,permission_id),
                 FOREIGN KEY (role_id) REFERENCES roles(id),
                 FOREIGN KEY (permission_id) REFERENCES permissions(id))""")
    conn.close()


def create_user_table():
    conn = get_connetion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL UNIQUE,

            email TEXT NOT NULL UNIQUE,

            password_hash TEXT NOT NULL,

            role_id INTEGER NOT NULL,

            email_verified INTEGER NOT NULL DEFAULT 0,

            pending_email TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(role_id)
            REFERENCES roles(id)
        )
    """)
    conn.close()


def create_role_table():
    conn = get_connetion()
    conn.execute("""CREATE TABLE IF NOT EXISTS roles(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL UNIQUE
                 )""")
    conn.close()


def seed_role():
    conn = get_connetion()
    conn.execute("""INSERT OR IGNORE INTO roles (name)
                   VALUES('admin'),('manager'),('user')""")
    conn.close()


def insert_user(username, email, password, role_id):
    conn = get_connetion()
    try:
        result = conn.execute("""
            INSERT INTO users(
                username,
                email,
                password_hash,
                role_id,
                email_verified
            )
            VALUES(?,?,?,?,?)
        """, (
            username,
            email,
            password,
            role_id,
            0
        ))
        return result.last_insert_rowid
    except sqlite3.LibsqlError:
        return None
    finally:
        conn.close()


def create_otp_table():
    conn = get_connetion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            otp TEXT NOT NULL,

            purpose TEXT NOT NULL,

            expires_at TIMESTAMP NOT NULL,

            attempts INTEGER NOT NULL DEFAULT 0,

            used INTEGER NOT NULL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
            ON DELETE CASCADE
        )
    """)
    conn.close()


def insert_otp(user_id, otp, purpose, expires_at):
    create_otp_table()
    conn = get_connetion()
    try:
        conn.execute("""
            INSERT INTO otp_codes(
                user_id,
                otp,
                purpose,
                expires_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            otp,
            purpose,
            _store_timestamp(expires_at)
        ))
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def get_latest_otp(user_id, purpose):
    conn = get_connetion()
    try:
        result = conn.execute("""
            SELECT id, otp, expires_at, attempts, used
            FROM otp_codes
            WHERE user_id = ?
              AND purpose = ?
              AND used = 0
            ORDER BY id DESC
            LIMIT 1
        """, (
            user_id,
            purpose
        ))
        return _as_dict(result.rows[0] if result.rows else None)
    finally:
        conn.close()


def increment_otp_attempts(otp_id):
    conn = get_connetion()
    try:
        conn.execute("""
            UPDATE otp_codes
            SET attempts = attempts + 1
            WHERE id = ?
        """, (otp_id,))
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def invalidate_otp_codes(user_id, purpose):
    conn = get_connetion()
    try:
        conn.execute("""
            UPDATE otp_codes
            SET used = 1
            WHERE user_id = ?
              AND purpose = ?
              AND used = 0
        """, (
            user_id,
            purpose
        ))
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def get_latest_otp_time(user_id, purpose):
    conn = get_connetion()
    try:
        result = conn.execute("""
            SELECT created_at
            FROM otp_codes
            WHERE user_id = ?
              AND purpose = ?
            ORDER BY id DESC
            LIMIT 1
        """, (
            user_id,
            purpose
        ))
        return _as_dict(result.rows[0] if result.rows else None)
    finally:
        conn.close()


def get_valid_otp(user_id, otp, purpose):
    conn = get_connetion()
    try:
        result = conn.execute("""
            SELECT id, expires_at
            FROM otp_codes
            WHERE user_id = ?
              AND otp = ?
              AND purpose = ?
              AND used = 0
            ORDER BY id DESC
            LIMIT 1
        """, (
            user_id,
            otp,
            purpose
        ))
        return _as_dict(result.rows[0] if result.rows else None)
    finally:
        conn.close()


def mark_otp_used(otp_id):
    conn = get_connetion()
    try:
        conn.execute("""
            UPDATE otp_codes
            SET used = 1
            WHERE id = ?
        """, (otp_id,))
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def verify_user_email(user_id):
    conn = get_connetion()
    try:
        conn.execute("""
            UPDATE users
            SET email_verified = 1
            WHERE id = ?
        """, (user_id,))
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def update_user_password(user_id, password_hash):
    conn = get_connetion()
    try:
        conn.execute("""
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
        """, (
            password_hash,
            user_id
        ))
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def find_role_id_by_name(role_name):
    conn = get_connetion()
    result = conn.execute(""" SELECT (id) FROM roles WHERE name = ?""", (role_name,))
    role = _as_dict(result.rows[0] if result.rows else None)
    conn.close()
    if role is None:
        return None
    return role["id"]


def find_permission_id_by_name(permission_name):
    conn = get_connetion()
    result = conn.execute(""" SELECT (id) FROM permissions WHERE name = ?""", (permission_name,))
    permission = _as_dict(result.rows[0] if result.rows else None)
    conn.close()
    if permission is None:
        return None
    return permission["id"]


def insert_role_permission(role_id, permission_id):
    conn = get_connetion()
    result = conn.execute(
        """INSERT OR IGNORE INTO role_permissions(role_id,permission_id) VALUES(?,?)""",
        (role_id, permission_id)
    )
    success = result.rows_affected > 0
    conn.close()
    return success


def create_task_table():
    conn = get_connetion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            description TEXT,

            status TEXT NOT NULL,

            priority TEXT NOT NULL,

            user_id INTEGER NOT NULL,

            due_date DATE,

            category_id INTEGER,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(category_id)
                REFERENCES categories(id)
                ON DELETE SET NULL

        )
    """)
    conn.close()


def insert_task(
    user_id,
    title,
    description,
    status,
    priority,
    due_date,
    category_id
):
    conn = get_connetion()
    try:
        conn.execute(
            """
            INSERT INTO tasks
            (
                title,
                description,
                status,
                priority,
                user_id,
                due_date,
                category_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                status,
                priority,
                user_id,
                due_date,
                category_id
            )
        )
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def get_all_task(
    user_id,
    limit,
    offset,
    sort_by,
    order,
    search,
    status,
    priority,
    category_id=None
):
    conn = get_connetion()

    query = ["""
        SELECT
            tasks.*,
            categories.name AS category_name
        FROM tasks
        LEFT JOIN categories
            ON tasks.category_id = categories.id
        WHERE tasks.user_id = ?
    """]

    values = [user_id]

    if search:
        query.append("AND LOWER(tasks.title) LIKE ?")
        values.append(f"%{search}%")

    if status:
        query.append("AND tasks.status = ?")
        values.append(status)

    if priority:
        query.append("AND tasks.priority = ?")
        values.append(priority)

    if category_id:
        query.append("AND tasks.category_id = ?")
        values.append(category_id)

    if sort_by == "priority":
        query.append(f"""
            ORDER BY CASE tasks.priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
            END {order}
        """)

    elif sort_by == "status":
        query.append(f"""
            ORDER BY CASE tasks.status
                WHEN 'pending' THEN 1
                WHEN 'completed' THEN 2
            END {order}
        """)

    else:
        query.append(f"ORDER BY tasks.{sort_by} {order}")

    query.append("LIMIT ? OFFSET ?")

    query = " ".join(query)

    values.append(limit)
    values.append(offset)

    result = conn.execute(query, values)
    tasks = [_as_dict(row) for row in result.rows]
    conn.close()
    return tasks


def count_task(user_id, search, status, priority):
    conn = get_connetion()
    qurey = ["SELECT COUNT (*) FROM tasks WHERE user_id = ?"]
    values = [user_id]
    if search:
        qurey.append("AND LOWER(title) LIKE ?")
        values.append(f"%{search}%")
    if status:
        qurey.append("AND status = ?")
        values.append(status)
    if priority:
        qurey.append("AND priority = ?")
        values.append(priority)
    qurey = " ".join(qurey)

    result = conn.execute(qurey, values)
    row = result.rows[0] if result.rows else None
    total_task = row[0] if row is not None else 0
    conn.close()
    return total_task


def get_specific_task(task_id):
    conn = get_connetion()
    result = conn.execute(
        """
        SELECT

            tasks.*,

            categories.name AS category_name

        FROM tasks

        LEFT JOIN categories

            ON tasks.category_id = categories.id

        WHERE tasks.id = ?

        """,
        (task_id,)
    )
    task = _as_dict(result.rows[0] if result.rows else None)
    conn.close()
    return task


def update_task(
    task_id,
    title,
    description,
    status,
    priority,
    due_date,
    category_id
):
    conn = get_connetion()
    result = conn.execute(
        """
        UPDATE tasks
        SET
            title = ?,
            description = ?,
            status = ?,
            priority = ?,
            due_date = ?,
            category_id = ?
        WHERE id = ?
        """,
        (
            title,
            description,
            status,
            priority,
            due_date,
            category_id,
            task_id
        )
    )
    success = result.rows_affected == 1
    conn.close()
    return success


def delete_task(user_id, task_id):
    conn = get_connetion()
    result = conn.execute(
        """DELETE FROM tasks WHERE id = ? AND user_id = ?""",
        (task_id, user_id)
    )
    success = result.rows_affected == 1
    conn.close()
    return success


def get_user_by_username(username):
    conn = get_connetion()
    result = conn.execute("""SELECT 
                   u.id,
                   u.username,
                   u.email,
                   u.password_hash,
                   r.name AS role
                   FROM users u
                   JOIN roles r
                    ON  u.role_id = r.id 
                   WHERE u.username = ?""", (username,))
    user = _as_dict(result.rows[0] if result.rows else None)
    conn.close()
    return user


def get_user_by_email(email):
    conn = get_connetion()
    result = conn.execute("""SELECT 
                   u.id,
                   u.username,
                   u.email,
                   u.password_hash,
                   u.email_verified,
                   r.name AS role
                   FROM users u
                   JOIN roles r
                    ON  u.role_id = r.id 
                   WHERE u.email = ?""", (email,))
    user = _as_dict(result.rows[0] if result.rows else None)
    conn.close()
    return user


def get_all_role_permissions():
    conn = get_connetion()
    result = conn.execute("""
        SELECT
            r.name AS role,
            p.name AS permission
        FROM role_permissions rp
        JOIN roles r
            ON rp.role_id = r.id
        JOIN permissions p
            ON rp.permission_id = p.id
        ORDER BY r.name, p.name
    """)
    rows = result.rows
    conn.close()
    return [_as_dict(row) for row in rows]


def role_has_permission(role_name, permission_name):
    conn = get_connetion()
    result = conn.execute("""
        SELECT 1
        FROM role_permissions rp
        JOIN roles r
            ON rp.role_id = r.id
        JOIN permissions p
            ON rp.permission_id = p.id
        WHERE r.name = ?
          AND p.name = ?
    """, (role_name, permission_name))
    row = result.rows[0] if result.rows else None
    conn.close()
    return row is not None


def delete_role_permission(role_id, permission_id):
    conn = get_connetion()
    result = conn.execute("""DELETE FROM role_permissions
    WHERE role_id = ? AND permission_id = ?""", (role_id, permission_id))
    deleted = result.rows_affected > 0
    conn.close()
    return deleted


def get_all_users():
    conn = get_connetion()
    result = conn.execute("""SELECT u.id,
                    u.username,
                    u.email,
                    r.name AS role
                    FROM users u
                    JOIN roles r
                        ON u.role_id = r.id
                        ORDER BY u.id""")
    users = [_as_dict(row) for row in result.rows]
    conn.close()
    return users


def get_user_by_id(user_id):
    conn = get_connetion()
    result = conn.execute("""
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    u.pending_email,
                    u.password_hash,
                    u.email_verified,
                    r.name AS role
                FROM users u
                JOIN roles r
                    ON u.role_id = r.id
                WHERE u.id = ?
                """, (user_id,))
    row = _as_dict(result.rows[0] if result.rows else None)
    conn.close()
    return row


def delete_users(user_id):
    conn = get_connetion()
    result = conn.execute("DELETE FROM users WHERE id= ?", (user_id,))
    success = result.rows_affected == 1
    conn.close()
    return success


def get_roles_and_permissions():
    conn = get_connetion()
    result = conn.execute("""
        SELECT
            'role' AS type,
            id,
            name
        FROM roles

        UNION ALL

        SELECT
            'permission' AS type,
            id,
            name
        FROM permissions

        ORDER BY type, id
    """)
    data = [_as_dict(row) for row in result.rows]
    conn.close()
    return data


def get_role_permissions(role_id):
    conn = get_connetion()
    result = conn.execute("""
        SELECT
            p.id,
            p.name
        FROM role_permissions rp
        JOIN permissions p
            ON rp.permission_id = p.id
        WHERE rp.role_id = ?
        ORDER BY p.id
    """, (role_id,))
    permissions = [_as_dict(row) for row in result.rows]
    conn.close()
    return permissions


def update_username(user_id, username):
    conn = get_connetion()
    try:
        conn.execute("""
            UPDATE users
            SET username = ?
            WHERE id = ?
        """, (
            username,
            user_id
        ))
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def set_pending_email(user_id, email):
    conn = get_connetion()
    try:
        conn.execute("""
            UPDATE users
            SET pending_email = ?
            WHERE id = ?
        """, (
            email,
            user_id
        ))
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def complete_email_change(user_id):
    conn = get_connetion()
    try:
        conn.execute("""
            UPDATE users
            SET email = pending_email,
                pending_email = NULL,
                email_verified = 1
            WHERE id = ?
              AND pending_email IS NOT NULL
        """, (user_id,))
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def update_user_profile(user_id, username, email):
    conn = get_connetion()

    result = conn.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        AND id != ?
        """,
        (email, user_id)
    )
    existing_user = result.rows[0] if result.rows else None

    if existing_user:
        conn.close()
        return "Email already exists", None

    conn.execute(
        """
        UPDATE users
        SET username = ?, email = ?
        WHERE id = ?
        """,
        (username, email, user_id)
    )
    result = conn.execute(
        """
        SELECT 
            u.id,
            u.username,
            u.email,
            r.name AS role
        FROM users u
        JOIN roles r
            ON u.role_id = r.id
        WHERE u.id = ?
        """,
        (user_id,)
    )
    updated_user = _as_dict(result.rows[0] if result.rows else None)
    conn.close()
    return None, updated_user


def add_due_date_column():
    conn = get_connetion()
    try:
        conn.execute("""
            ALTER TABLE tasks
            ADD COLUMN due_date DATE
        """)
        print("due_date column added successfully.")
    except Exception as e:
        print("due_date column already exists or error:", e)
    finally:
        conn.close()


def update_user_role(user_id, role_name):
    conn = get_connetion()

    result = conn.execute("""
        SELECT id
        FROM roles
        WHERE name = ?
    """, (role_name,))
    role = _as_dict(result.rows[0] if result.rows else None)

    if role is None:
        conn.close()
        return False

    role_id = role["id"]

    result = conn.execute("""
        UPDATE users
        SET role_id = ?
        WHERE id = ?
    """, (role_id, user_id))
    success = result.rows_affected == 1
    conn.close()
    return success


def clear_permissions_for_role(role_id):
    conn = get_connetion()
    conn.execute("""
        DELETE FROM role_permissions
        WHERE role_id = ?
    """, (role_id,))
    conn.close()


def create_category_table():
    conn = get_connetion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            user_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE

        )
    """)
    conn.close()


def add_description_column():
    conn = get_connetion()
    try:
        conn.execute("""
            ALTER TABLE tasks
            ADD COLUMN description TEXT
        """)
    except Exception:
        pass
    conn.close()


def category_exists(user_id, name):
    conn = get_connetion()
    result = conn.execute(
        """
        SELECT id
        FROM categories
        WHERE user_id = ?
        AND LOWER(name) = LOWER(?)
        """,
        (user_id, name)
    )
    row = result.rows[0] if result.rows else None
    conn.close()
    return row is not None


def add_category_column():
    conn = get_connetion()
    try:
        conn.execute("""
            ALTER TABLE tasks
            ADD COLUMN category_id INTEGER
        """)
    except Exception:
        pass
    conn.close()


def get_all_categories(user_id):
    conn = get_connetion()
    result = conn.execute(
        """
        SELECT
            id,
            name
        FROM categories
        WHERE user_id = ?
        ORDER BY name
        """,
        (user_id,)
    )
    categories = [_as_dict(row) for row in result.rows]
    conn.close()
    return categories


def insert_category(user_id, name):
    conn = get_connetion()
    try:
        conn.execute(
            """
            INSERT INTO categories
            (
                name,
                user_id
            )
            VALUES (?, ?)
            """,
            (
                name,
                user_id
            )
        )
        return True
    except sqlite3.LibsqlError:
        return False
    finally:
        conn.close()


def delete_category(user_id, category_id):
    conn = get_connetion()
    result = conn.execute(
        """
        DELETE FROM categories
        WHERE
            id = ?
        AND
            user_id = ?
        """,
        (
            category_id,
            user_id
        )
    )
    success = result.rows_affected == 1
    conn.close()
    return success

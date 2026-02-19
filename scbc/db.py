import re
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from .config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT, db_dsn_no_password

CENTRAL_TABLE_NAME = "schedules"

def _sanitize_class_table_name(class_name: str) -> str:
    """Return a safe table name for a given class identifier.

    Rules:
    - Lowercase
    - Replace any non-alphanumeric with underscore
    - Prefix with 'class_' to guarantee it starts with a letter
    """
    if not class_name:
        raise ValueError("class_name must be provided")
    cleaned = re.sub(r"[^0-9a-zA-Z]", "_", class_name)
    cleaned = cleaned.lower()
    table = f"class_{cleaned}"
    return table


class ScheduleDB:
    """Manages database operations for schedules stored per-class table."""

    def __init__(self):
        self.host = DB_HOST
        self.dbname = DB_NAME
        self.user = DB_USER
        self.password = DB_PASSWORD
        self.port = DB_PORT
        self.conn = None

    def connect(self):
        """Establish connection to PostgreSQL database."""
        if self.conn:
            return self.conn
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                port=self.port,
            )
            return self.conn
        except psycopg2.Error as e:
            hint = " (hint: set SCBC_DB_PASSWORD environment variable)" if "password" in str(e).lower() else ""
            print(f"[ERROR] Database connection failed: {e}{hint}")
            print(f"[DEBUG] Attempted DSN: {db_dsn_no_password()}")
            raise

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_table(self, class_name: str = None):
        """Ensure the central schedules table exists.

        The `class_name` argument is accepted for backward compatibility but is
        not used to create separate tables anymore.
        """
        conn = self.connect()

        create_table_sql = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {tbl} (
                id SERIAL PRIMARY KEY,
                class_name TEXT NOT NULL,
                day TEXT,
                time_slot TEXT,
                subject TEXT,
                "group" TEXT,
                teacher TEXT,
                room TEXT
            );
            """
        ).format(tbl=sql.Identifier(CENTRAL_TABLE_NAME))

        cur = conn.cursor()
        cur.execute(create_table_sql)

        idx_sql = sql.SQL("CREATE INDEX IF NOT EXISTS {idx} ON {tbl} (class_name);").format(
            idx=sql.Identifier(f"idx_{CENTRAL_TABLE_NAME}_class"),
            tbl=sql.Identifier(CENTRAL_TABLE_NAME),
        )
        cur.execute(idx_sql)

        for col in ["class_name", "day", "time_slot", "subject", "group", "teacher", "room"]:
            cur.execute(sql.SQL("ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS {col} TEXT;").format(
                tbl=sql.Identifier(CENTRAL_TABLE_NAME),
                col=sql.Identifier(col),
            ))
        cur.execute(sql.SQL("ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS rid INTEGER;").format(
            tbl=sql.Identifier(CENTRAL_TABLE_NAME),
        ))

        # clean up any legacy columns/type issues
        # 1. drop accidentally created quoted column name "group" (including quotes)
        #    use Identifier to ensure proper quoting; if an error occurs we rollback
        try:
            badname = '"group"'  # actual column name stored in some older tables
            cur.execute(sql.SQL("ALTER TABLE {tbl} DROP COLUMN IF EXISTS {col};").format(
                tbl=sql.Identifier(CENTRAL_TABLE_NAME),
                col=sql.Identifier(badname),
            ))
        except Exception:
            conn.rollback()
            # log but continue; previous malformed column might not exist any more
            print(f"[WARN] failed to drop legacy column {badname}, continuing")
            # re-establish cursor for further operations
            cur = conn.cursor()

        # 2. ensure room column is TEXT (previous schema had it as ARRAY)
        cur.execute(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name=%s AND column_name='room';",
            (CENTRAL_TABLE_NAME,)
        )
        row = cur.fetchone()
        if row and row[0].lower() != 'text':
            # coerce array/text to plain text
            cur.execute(sql.SQL(
                "ALTER TABLE {tbl} ALTER COLUMN room TYPE TEXT USING room::text;"
            ).format(tbl=sql.Identifier(CENTRAL_TABLE_NAME)))

        seq_name = f"{CENTRAL_TABLE_NAME}_rid_seq"
        cur.execute(sql.SQL("CREATE SEQUENCE IF NOT EXISTS {seq};").format(seq=sql.Identifier(seq_name)))
        cur.execute(sql.SQL("ALTER TABLE {tbl} ALTER COLUMN rid SET DEFAULT nextval({seq_literal});").format(
            tbl=sql.Identifier(CENTRAL_TABLE_NAME),
            seq_literal=sql.Literal(seq_name),
        ))
        cur.execute(sql.SQL("UPDATE {tbl} SET rid = nextval({seq_literal}) WHERE rid IS NULL;").format(
            tbl=sql.Identifier(CENTRAL_TABLE_NAME),
            seq_literal=sql.Literal(seq_name),
        ))
        cur.execute(sql.SQL("CREATE UNIQUE INDEX IF NOT EXISTS {idx} ON {tbl} (rid);").format(
            idx=sql.Identifier(f"idx_{CENTRAL_TABLE_NAME}_rid"),
            tbl=sql.Identifier(CENTRAL_TABLE_NAME),
        ))

        conn.commit()
        cur.close()
        return CENTRAL_TABLE_NAME

    def clear_schedule(self, class_name: str):
        """Delete all rows for a given class from the central schedules table."""
        conn = self.connect()
        if not self.table_exists():
            return 0
        cur = conn.cursor()
        try:
            cur.execute(sql.SQL("DELETE FROM {tbl} WHERE class_name = %s;").format(tbl=sql.Identifier(CENTRAL_TABLE_NAME)), (class_name,))
            deleted = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
            conn.commit()
            return deleted
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cur.close()

    def insert_schedule_entries(self, class_name: str, entries: list):
        """Insert schedule entries into the central schedules table.

        entries: list of dicts with keys: day, time_slot, subject, group, teacher, room
        """
        if not entries:
            return 0

        conn = self.connect()
        self._ensure_table(class_name)

        data = []
        for e in entries:
            data.append((
                class_name,
                e.get("day"),
                e.get("time_slot"),
                e.get("subject"),
                e.get("group"),
                e.get("teacher"),
                e.get("room"),
            ))

        insert_sql = sql.SQL("INSERT INTO {tbl} (class_name, day, time_slot, subject, \"group\", teacher, room) VALUES %s").format(
            tbl=sql.Identifier(CENTRAL_TABLE_NAME)
        )

        cur = conn.cursor()
        try:
            execute_values(cur, insert_sql.as_string(conn), data)
            conn.commit()
            return len(data)
        except psycopg2.Error as e:
            conn.rollback()
            print(f"[ERROR] Failed to insert entries into {CENTRAL_TABLE_NAME}: {e}")
            raise
        finally:
            cur.close()

    def replace_schedule_entries(self, class_name: str, entries: list):
        """Atomically replace schedule rows for a class.

        This performs DELETE WHERE class_name = %s and then INSERT the new rows
        inside a single transaction. If anything fails, the transaction is rolled
        back and the previous rows remain intact.

        Returns the number of rows inserted.
        """
        if entries is None:
            entries = []

        conn = self.connect()
        # ensure table (may perform alterations and rollbacks internally)
        self._ensure_table(class_name)
        # obtain fresh cursor after any potential rollback
        cur = conn.cursor()
        try:
            cur.execute("BEGIN;")

            cur.execute(sql.SQL("DELETE FROM {tbl} WHERE class_name = %s;").format(tbl=sql.Identifier(CENTRAL_TABLE_NAME)), (class_name,))

            inserted = 0
            if entries:
                data = []
                for e in entries:
                    data.append((
                        class_name,
                        e.get("day"),
                        e.get("time_slot"),
                        e.get("subject"),
                        e.get("group"),
                        e.get("teacher"),
                        e.get("room"),
                    ))

                insert_sql = sql.SQL("INSERT INTO {tbl} (class_name, day, time_slot, subject, \"group\", teacher, room) VALUES %s").format(
                    tbl=sql.Identifier(CENTRAL_TABLE_NAME)
                )
                execute_values(cur, insert_sql.as_string(conn), data)
                inserted = len(data)

            conn.commit()
            return inserted
        except psycopg2.Error as e:
            conn.rollback()
            print(f"[ERROR] replace_schedule_entries failed for {class_name}: {e}")
            raise
        finally:
            cur.close()

    def get_schedule(self, class_name: str):
        """Retrieve all schedule entries for a class from the central schedules table."""
        conn = self.connect()
        if not self.table_exists():
            return []
        cur = conn.cursor()
        try:
            cur.execute(sql.SQL("SELECT day, time_slot, subject, \"group\", teacher, room FROM {tbl} WHERE class_name = %s ORDER BY day, time_slot;").format(tbl=sql.Identifier(CENTRAL_TABLE_NAME)), (class_name,))
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return [dict(zip(cols, r)) for r in rows]
        except psycopg2.Error as e:
            print(f"[ERROR] Failed to read schedule for {class_name}: {e}")
            return []
        finally:
            cur.close()

    def table_exists(self, class_name: str = None) -> bool:
        """Check whether the central schedules table exists in the DB."""
        conn = self.connect()
        cur = conn.cursor()
        try:
            cur.execute("SELECT to_regclass(%s);", (CENTRAL_TABLE_NAME,))
            res = cur.fetchone()[0]
            return res is not None
        finally:
            cur.close()

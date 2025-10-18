import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    language TEXT DEFAULT 'en',
                    joined_channel BOOLEAN DEFAULT 0,
                    current_stage TEXT,
                    payment_method TEXT,
                    payment_account TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    group_link TEXT,
                    group_username TEXT,
                    group_title TEXT,
                    member_count INTEGER,
                    created_year INTEGER,
                    created_month INTEGER,
                    price INTEGER,
                    transfer_screenshot_file_id TEXT,
                    status TEXT DEFAULT 'pending',
                    payment_method TEXT,
                    payment_account TEXT,
                    admin_notes TEXT,
                    admin_payment_screenshot TEXT,  -- proof uploaded by admin
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS admin_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    submission_id INTEGER,
                    notes TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (submission_id) REFERENCES groups (id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def create_user(self, user_id: int, username: str, language: str = "en"):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO users (user_id, username, language, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, username, language, datetime.now())
            )
            await db.commit()

    async def update_user_language(self, user_id: int, language: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET language = ? WHERE user_id = ?",
                (language, user_id)
            )
            await db.commit()

    async def update_user_channel_status(self, user_id: int, joined: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET joined_channel = ? WHERE user_id = ?",
                (joined, user_id)
            )
            await db.commit()

    async def update_user_stage(self, user_id: int, stage: Optional[str]):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET current_stage = ? WHERE user_id = ?",
                (stage, user_id)
            )
            await db.commit()

    async def update_user_payment(self, user_id: int, payment_method: str, payment_account: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET payment_method = ?, payment_account = ? WHERE user_id = ?",
                (payment_method, payment_account, user_id)
            )
            await db.commit()

    async def get_submissions_by_status(self, status: str, limit: int = 50) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT g.*, u.username AS seller_username
                FROM groups g
                JOIN users u ON g.user_id = u.user_id
                WHERE g.status = ?
                ORDER BY g.created_at DESC
                LIMIT ?
                """,
                (status, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def create_submission(self, user_id: int, group_data: Dict[str, Any]) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO groups (
                    user_id, group_link, group_username, group_title,
                    member_count, created_year, created_month, price, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    group_data.get("group_link"),
                    group_data.get("group_username"),
                    group_data.get("group_title"),
                    group_data.get("member_count"),
                    group_data.get("created_year"),
                    group_data.get("created_month"),
                    group_data.get("price"),
                    "pending"
                )
            )
            await db.commit()
            return cursor.lastrowid

    async def update_submission(self, submission_id: int, updates: Dict[str, Any]):
        # Build dynamic SET clause and append updated_at + id
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [datetime.now(), submission_id]

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE groups SET {set_clause}, updated_at = ? WHERE id = ?",
                values
            )
            await db.commit()

    async def get_submission(self, submission_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM groups WHERE id = ?", (submission_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_user_submissions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM groups
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_pending_submissions(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT g.*, u.username AS seller_username
                FROM groups g
                JOIN users u ON g.user_id = u.user_id
                WHERE g.status IN ('pending', 'awaiting_payment_info', 'manual_review')
                ORDER BY g.created_at DESC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def log_admin_action(
        self,
        admin_id: int,
        action: str,
        submission_id: Optional[int] = None,
        notes: Optional[str] = None
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO admin_actions (admin_id, action, submission_id, notes, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (admin_id, action, submission_id, notes, datetime.now())
            )
            await db.commit()

    async def get_stats(self) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            total = await (await db.execute("SELECT COUNT(*) FROM groups")).fetchone()
            pending = await (await db.execute("SELECT COUNT(*) FROM groups WHERE status = 'pending'")).fetchone()
            approved = await (await db.execute("SELECT COUNT(*) FROM groups WHERE status = 'awaiting_payment_info'")).fetchone()
            paid = await (await db.execute("SELECT COUNT(*) FROM groups WHERE status = 'paid'")).fetchone()
            total_birr = await (await db.execute("SELECT SUM(price) FROM groups WHERE status = 'paid'")).fetchone()

            return {
                "total_submissions": total[0],
                "pending": pending[0],
                "approved": approved[0],
                "paid": paid[0],
                "total_birr_paid": total_birr[0] or 0
            }

    async def get_config(self, key: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT value FROM bot_config WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def set_config(self, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO bot_config (key, value) VALUES (?, ?)",
                (key, value)
            )
            await db.commit()

"""
Cosmic ki baddie - Database Manager
Asynchronous SQLite persistence engine powering all bot systems.
"""

import aiosqlite
import json
import time
import os
from typing import Optional, List, Dict, Any, Tuple
from config import DATABASE_PATH, DEFAULT_PREFIX

class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def init_db(self):
        """Initialize all database tables and indexes."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA foreign_keys=ON;")

            # 1. Guild Configuration
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_config (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT '!',
                    welcome_channel_id INTEGER,
                    welcome_message TEXT,
                    goodbye_channel_id INTEGER,
                    goodbye_message TEXT,
                    mod_log_channel_id INTEGER,
                    general_log_channel_id INTEGER,
                    ticket_category_id INTEGER,
                    ticket_log_channel_id INTEGER,
                    ticket_support_role_id INTEGER,
                    mod_role_id INTEGER,
                    admin_role_id INTEGER,
                    autorole_id INTEGER,
                    safe_mode INTEGER DEFAULT 0,
                    anti_nuke_enabled INTEGER DEFAULT 1,
                    max_warnings INTEGER DEFAULT 3,
                    updated_at REAL
                );
            """)

            # 2. Command & Module Permissions
            await db.execute("""
                CREATE TABLE IF NOT EXISTS command_permissions (
                    guild_id INTEGER,
                    entity_type TEXT, -- 'role' or 'user'
                    entity_id INTEGER,
                    command_name TEXT,
                    access INTEGER, -- 1 = allow, 0 = deny
                    PRIMARY KEY (guild_id, entity_id, command_name)
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS module_permissions (
                    guild_id INTEGER,
                    entity_type TEXT,
                    entity_id INTEGER,
                    module_name TEXT,
                    access INTEGER,
                    PRIMARY KEY (guild_id, entity_id, module_name)
                );
            """)

            # 3. Moderation Records & Warnings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS moderation_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    target_id INTEGER,
                    target_name TEXT,
                    moderator_id INTEGER,
                    moderator_name TEXT,
                    action TEXT,
                    reason TEXT,
                    timestamp REAL,
                    active INTEGER DEFAULT 1
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    moderator_id INTEGER,
                    reason TEXT,
                    timestamp REAL
                );
            """)

            # 4. Support Tickets
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER UNIQUE,
                    creator_id INTEGER,
                    creator_name TEXT,
                    claimer_id INTEGER,
                    claimer_name TEXT,
                    category TEXT,
                    status TEXT DEFAULT 'open',
                    created_at REAL,
                    closed_at REAL,
                    transcript_text TEXT
                );
            """)

            # 5. Activity Tracking & Activity Roles
            await db.execute("""
                CREATE TABLE IF NOT EXISTS activity_stats (
                    guild_id INTEGER,
                    user_id INTEGER,
                    message_count INTEGER DEFAULT 0,
                    voice_minutes INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    last_message_ts REAL DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS activity_roles (
                    guild_id INTEGER,
                    role_id INTEGER,
                    threshold_type TEXT, -- 'messages', 'voice', 'level'
                    threshold_value INTEGER,
                    PRIMARY KEY (guild_id, role_id)
                );
            """)

            # 6. Autoresponders
            await db.execute("""
                CREATE TABLE IF NOT EXISTS autoresponders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    trigger_text TEXT,
                    match_type TEXT DEFAULT 'exact', -- 'exact', 'contains', 'startswith'
                    response_text TEXT,
                    is_embed INTEGER DEFAULT 0,
                    channel_id INTEGER,
                    role_id INTEGER,
                    cooldown_sec INTEGER DEFAULT 5,
                    is_enabled INTEGER DEFAULT 1,
                    last_triggered REAL DEFAULT 0
                );
            """)

            # 7. Giveaways & Entries
            await db.execute("""
                CREATE TABLE IF NOT EXISTS giveaways (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    message_id INTEGER UNIQUE,
                    prize TEXT,
                    winners_count INTEGER DEFAULT 1,
                    end_time REAL,
                    host_id INTEGER,
                    ended INTEGER DEFAULT 0,
                    winner_ids TEXT
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS giveaway_entries (
                    giveaway_id INTEGER,
                    user_id INTEGER,
                    timestamp REAL,
                    PRIMARY KEY (giveaway_id, user_id)
                );
            """)

            # 8. Events & RSVPs
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    title TEXT,
                    description TEXT,
                    event_time REAL,
                    creator_id INTEGER,
                    status TEXT DEFAULT 'active',
                    reminder_sent INTEGER DEFAULT 0
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS event_participants (
                    event_id INTEGER,
                    user_id INTEGER,
                    status TEXT, -- 'going' or 'interested'
                    PRIMARY KEY (event_id, user_id)
                );
            """)

            # 9. Polls & Votes
            await db.execute("""
                CREATE TABLE IF NOT EXISTS polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    message_id INTEGER UNIQUE,
                    question TEXT,
                    options_json TEXT,
                    multiple_choice INTEGER DEFAULT 0,
                    anonymous INTEGER DEFAULT 0,
                    end_time REAL,
                    is_closed INTEGER DEFAULT 0
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS poll_votes (
                    poll_id INTEGER,
                    user_id INTEGER,
                    option_index INTEGER,
                    timestamp REAL,
                    PRIMARY KEY (poll_id, user_id, option_index)
                );
            """)

            # 10. Embed Templates
            await db.execute("""
                CREATE TABLE IF NOT EXISTS embed_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    name TEXT,
                    title TEXT,
                    description TEXT,
                    color INTEGER,
                    thumbnail TEXT,
                    image TEXT,
                    author_name TEXT,
                    footer_text TEXT,
                    fields_json TEXT,
                    UNIQUE(guild_id, name)
                );
            """)

            # 11. Anti-Nuke Settings & Whitelist
            await db.execute("""
                CREATE TABLE IF NOT EXISTS anti_nuke_config (
                    guild_id INTEGER PRIMARY KEY,
                    channel_delete_threshold INTEGER DEFAULT 3,
                    role_delete_threshold INTEGER DEFAULT 3,
                    kick_ban_threshold INTEGER DEFAULT 3,
                    channel_create_threshold INTEGER DEFAULT 4,
                    role_create_threshold INTEGER DEFAULT 4,
                    window_seconds INTEGER DEFAULT 60,
                    protection_mode TEXT DEFAULT 'SERVER_PROTECTION', -- 'SAFE_MODE', 'SERVER_PROTECTION', 'EMERGENCY_LOCKDOWN'
                    action_on_trigger TEXT DEFAULT 'QUARANTINE_ROLE',
                    is_enabled INTEGER DEFAULT 1
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS whitelisted_users (
                    guild_id INTEGER,
                    user_id INTEGER,
                    added_by INTEGER,
                    timestamp REAL,
                    PRIMARY KEY (guild_id, user_id)
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS anti_nuke_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    action_type TEXT,
                    timestamp REAL,
                    mitigated INTEGER DEFAULT 0,
                    details TEXT
                );
            """)

            # 12. Automation Rules
            await db.execute("""
                CREATE TABLE IF NOT EXISTS automation_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    name TEXT,
                    trigger_type TEXT, -- 'member_join', 'message_contains', 'voice_join', 'level_up'
                    trigger_value TEXT,
                    action_type TEXT,  -- 'add_role', 'remove_role', 'send_message', 'dm_user'
                    action_value TEXT,
                    is_enabled INTEGER DEFAULT 1
                );
            """)

            await db.commit()

    # --- Guild Config Helpers ---
    async def get_guild_config(self, guild_id: int) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            # Insert default
            await db.execute(
                "INSERT INTO guild_config (guild_id, prefix, updated_at) VALUES (?, ?, ?)",
                (guild_id, DEFAULT_PREFIX, time.time())
            )
            await db.commit()
            cursor = await db.execute("SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,))
            return dict(await cursor.fetchone())

    async def update_guild_config(self, guild_id: int, **kwargs) -> bool:
        if not kwargs:
            return True
        keys = list(kwargs.keys())
        values = [kwargs[k] for k in keys]
        set_clause = ", ".join([f"{k} = ?" for k in keys]) + ", updated_at = ?"
        values.append(time.time())
        values.append(guild_id)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE guild_config SET {set_clause} WHERE guild_id = ?", values)
            await db.commit()
            return True

    async def get_prefix(self, guild_id: Optional[int]) -> str:
        if not guild_id:
            return DEFAULT_PREFIX
        config = await self.get_guild_config(guild_id)
        return config.get("prefix", DEFAULT_PREFIX) or DEFAULT_PREFIX

    async def set_prefix(self, guild_id: int, new_prefix: str) -> bool:
        await self.update_guild_config(guild_id, prefix=new_prefix)
        return True

    # --- Permissions System Helpers ---
    async def get_command_access(self, guild_id: int, entity_id: int, command_name: str) -> Optional[bool]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT access FROM command_permissions WHERE guild_id = ? AND entity_id = ? AND command_name = ?",
                (guild_id, entity_id, command_name.lower())
            )
            row = await cursor.fetchone()
            if row is not None:
                return bool(row[0])
            return None

    async def get_module_access(self, guild_id: int, entity_id: int, module_name: str) -> Optional[bool]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT access FROM module_permissions WHERE guild_id = ? AND entity_id = ? AND module_name = ?",
                (guild_id, entity_id, module_name.lower())
            )
            row = await cursor.fetchone()
            if row is not None:
                return bool(row[0])
            return None

    async def set_command_access(self, guild_id: int, entity_type: str, entity_id: int, command_name: str, access: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO command_permissions (guild_id, entity_type, entity_id, command_name, access)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, entity_id, command_name) DO UPDATE SET access = excluded.access;
            """, (guild_id, entity_type, entity_id, command_name.lower(), 1 if access else 0))
            await db.commit()

    async def set_module_access(self, guild_id: int, entity_type: str, entity_id: int, module_name: str, access: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO module_permissions (guild_id, entity_type, entity_id, module_name, access)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, entity_id, module_name) DO UPDATE SET access = excluded.access;
            """, (guild_id, entity_type, entity_id, module_name.lower(), 1 if access else 0))
            await db.commit()

    async def get_all_permissions(self, guild_id: int) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor_cmds = await db.execute("SELECT * FROM command_permissions WHERE guild_id = ?", (guild_id,))
            cmds = [dict(r) for r in await cursor_cmds.fetchall()]
            cursor_mods = await db.execute("SELECT * FROM module_permissions WHERE guild_id = ?", (guild_id,))
            mods = [dict(r) for r in await cursor_mods.fetchall()]
            return {"commands": cmds, "modules": mods}

    # --- Moderation Logs & Warnings ---
    async def add_mod_action(self, guild_id: int, target_id: int, target_name: str,
                             moderator_id: int, moderator_name: str, action: str, reason: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO moderation_records (guild_id, target_id, target_name, moderator_id, moderator_name, action, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, target_id, target_name, moderator_id, moderator_name, action, reason, time.time()))
            await db.commit()
            return cursor.lastrowid

    async def get_mod_logs(self, guild_id: int, limit: int = 25, target_id: Optional[int] = None) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if target_id:
                cursor = await db.execute(
                    "SELECT * FROM moderation_records WHERE guild_id = ? AND target_id = ? ORDER BY id DESC LIMIT ?",
                    (guild_id, target_id, limit)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM moderation_records WHERE guild_id = ? ORDER BY id DESC LIMIT ?",
                    (guild_id, limit)
                )
            return [dict(r) for r in await cursor.fetchall()]

    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (guild_id, user_id, moderator_id, reason, time.time()))
            await db.commit()
            return cursor.lastrowid

    async def get_warnings(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY id DESC",
                (guild_id, user_id)
            )
            return [dict(r) for r in await cursor.fetchall()]

    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            await db.commit()
            return cursor.rowcount

    # --- Support Tickets ---
    async def create_ticket(self, guild_id: int, channel_id: int, creator_id: int, creator_name: str, category: str = "General Support") -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO tickets (guild_id, channel_id, creator_id, creator_name, category, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'open', ?)
            """, (guild_id, channel_id, creator_id, creator_name, category, time.time()))
            await db.commit()
            return cursor.lastrowid

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM tickets WHERE channel_id = ?", (channel_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_user_open_tickets(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM tickets WHERE guild_id = ? AND creator_id = ? AND status = 'open'",
                (guild_id, user_id)
            )
            return [dict(r) for r in await cursor.fetchall()]

    async def claim_ticket(self, channel_id: int, claimer_id: int, claimer_name: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tickets SET claimer_id = ?, claimer_name = ? WHERE channel_id = ?",
                (claimer_id, claimer_name, channel_id)
            )
            await db.commit()
            return True

    async def close_ticket(self, channel_id: int, transcript_text: str = "") -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tickets SET status = 'closed', closed_at = ?, transcript_text = ? WHERE channel_id = ?",
                (time.time(), transcript_text, channel_id)
            )
            await db.commit()
            return True

    async def reopen_ticket(self, channel_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE tickets SET status = 'open' WHERE channel_id = ?", (channel_id,))
            await db.commit()
            return True

    # --- Activity & Leveling ---
    async def record_activity_message(self, guild_id: int, user_id: int) -> Tuple[int, int, bool]:
        """
        Record message activity with anti-spam rate limiting (60s cooldown for XP).
        Returns (new_messages, new_level, leveled_up).
        """
        now = time.time()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT message_count, xp, level, last_message_ts FROM activity_stats WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            row = await cursor.fetchone()
            if not row:
                # First message
                await db.execute("""
                    INSERT INTO activity_stats (guild_id, user_id, message_count, xp, level, last_message_ts)
                    VALUES (?, ?, 1, 15, 1, ?)
                """, (guild_id, user_id, now))
                await db.commit()
                return (1, 1, False)

            count = row["message_count"] + 1
            last_ts = row["last_message_ts"] or 0
            xp = row["xp"]
            current_level = row["level"]
            leveled_up = False

            # Anti-spam: award XP only if > 45 seconds since last
            if (now - last_ts) >= 45:
                xp += 15
                needed_xp = current_level * 100
                if xp >= needed_xp:
                    current_level += 1
                    leveled_up = True

            await db.execute("""
                UPDATE activity_stats SET message_count = ?, xp = ?, level = ?, last_message_ts = ?
                WHERE guild_id = ? AND user_id = ?
            """, (count, xp, current_level, now, guild_id, user_id))
            await db.commit()
            return (count, current_level, leveled_up)

    async def get_activity_leaderboard(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT user_id, message_count, voice_minutes, xp, level
                FROM activity_stats
                WHERE guild_id = ?
                ORDER BY xp DESC, message_count DESC
                LIMIT ?
            """, (guild_id, limit))
            return [dict(r) for r in await cursor.fetchall()]

    async def set_activity_role(self, guild_id: int, role_id: int, threshold_type: str, threshold_val: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO activity_roles (guild_id, role_id, threshold_type, threshold_value)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, role_id) DO UPDATE SET threshold_type = excluded.threshold_type, threshold_value = excluded.threshold_value
            """, (guild_id, role_id, threshold_type, threshold_val))
            await db.commit()

    async def get_activity_roles(self, guild_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM activity_roles WHERE guild_id = ? ORDER BY threshold_value ASC", (guild_id,))
            return [dict(r) for r in await cursor.fetchall()]

    # --- Autoresponders ---
    async def add_autoresponder(self, guild_id: int, trigger: str, response: str, match_type: str = "exact",
                                is_embed: bool = False, channel_id: Optional[int] = None,
                                role_id: Optional[int] = None, cooldown: int = 5) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO autoresponders (guild_id, trigger_text, match_type, response_text, is_embed, channel_id, role_id, cooldown_sec)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, trigger.lower().strip(), match_type, response, 1 if is_embed else 0, channel_id, role_id, cooldown))
            await db.commit()
            return cursor.lastrowid

    async def get_autoresponders(self, guild_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM autoresponders WHERE guild_id = ?", (guild_id,))
            return [dict(r) for r in await cursor.fetchall()]

    async def delete_autoresponder(self, guild_id: int, rule_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM autoresponders WHERE guild_id = ? AND id = ?", (guild_id, rule_id))
            await db.commit()
            return cursor.rowcount > 0

    async def toggle_autoresponder(self, guild_id: int, rule_id: int, enable: bool) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("UPDATE autoresponders SET is_enabled = ? WHERE guild_id = ? AND id = ?", (1 if enable else 0, guild_id, rule_id))
            await db.commit()
            return cursor.rowcount > 0

    # --- Anti-Nuke Security ---
    async def get_antinuke_config(self, guild_id: int) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM anti_nuke_config WHERE guild_id = ?", (guild_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            # Insert default
            await db.execute("INSERT INTO anti_nuke_config (guild_id) VALUES (?)", (guild_id,))
            await db.commit()
            cursor = await db.execute("SELECT * FROM anti_nuke_config WHERE guild_id = ?", (guild_id,))
            return dict(await cursor.fetchone())

    async def update_antinuke_config(self, guild_id: int, **kwargs) -> bool:
        keys = list(kwargs.keys())
        values = [kwargs[k] for k in keys]
        set_clause = ", ".join([f"{k} = ?" for k in keys])
        values.append(guild_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE anti_nuke_config SET {set_clause} WHERE guild_id = ?", values)
            await db.commit()
            return True

    async def is_whitelisted(self, guild_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT 1 FROM whitelisted_users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            return (await cursor.fetchone()) is not None

    async def add_whitelist(self, guild_id: int, user_id: int, added_by: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO whitelisted_users (guild_id, user_id, added_by, timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id) DO NOTHING
            """, (guild_id, user_id, added_by, time.time()))
            await db.commit()
            return True

    async def remove_whitelist(self, guild_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM whitelisted_users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            await db.commit()
            return cursor.rowcount > 0

    async def log_antinuke_action(self, guild_id: int, user_id: int, action_type: str, details: str = "", mitigated: bool = False):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO anti_nuke_logs (guild_id, user_id, action_type, timestamp, mitigated, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (guild_id, user_id, action_type, time.time(), 1 if mitigated else 0, details))
            await db.commit()

    async def get_recent_action_count(self, guild_id: int, user_id: int, action_type: str, window_seconds: int = 60) -> int:
        cutoff = time.time() - window_seconds
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) FROM anti_nuke_logs
                WHERE guild_id = ? AND user_id = ? AND action_type = ? AND timestamp >= ?
            """, (guild_id, user_id, action_type, cutoff))
            row = await cursor.fetchone()
            return row[0] if row else 0

    # --- Giveaways ---
    async def create_giveaway(self, guild_id: int, channel_id: int, message_id: int, prize: str, winners_count: int, end_time: float, host_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO giveaways (guild_id, channel_id, message_id, prize, winners_count, end_time, host_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, channel_id, message_id, prize, winners_count, end_time, host_id))
            await db.commit()
            return cursor.lastrowid

    async def enter_giveaway(self, giveaway_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("INSERT INTO giveaway_entries (giveaway_id, user_id, timestamp) VALUES (?, ?, ?)",
                                 (giveaway_id, user_id, time.time()))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_giveaway_entries(self, giveaway_id: int) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT user_id FROM giveaway_entries WHERE giveaway_id = ?", (giveaway_id,))
            return [row[0] for row in await cursor.fetchall()]

    async def end_giveaway(self, giveaway_id: int, winner_ids: List[int]) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE giveaways SET ended = 1, winner_ids = ? WHERE id = ?", (json.dumps(winner_ids), giveaway_id))
            await db.commit()
            return True

    # --- Events ---
    async def create_event(self, guild_id: int, channel_id: int, title: str, description: str, event_time: float, creator_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO events (guild_id, channel_id, title, description, event_time, creator_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (guild_id, channel_id, title, description, event_time, creator_id))
            await db.commit()
            return cursor.lastrowid

    async def rsvp_event(self, event_id: int, user_id: int, status: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO event_participants (event_id, user_id, status)
                VALUES (?, ?, ?)
                ON CONFLICT(event_id, user_id) DO UPDATE SET status = excluded.status
            """, (event_id, user_id, status))
            await db.commit()
            return True

    async def get_event_rsvps(self, event_id: int) -> Dict[str, List[int]]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT user_id, status FROM event_participants WHERE event_id = ?", (event_id,))
            rows = await cursor.fetchall()
            result = {"going": [], "interested": []}
            for user_id, status in rows:
                if status in result:
                    result[status].append(user_id)
            return result

    # --- Polls ---
    async def create_poll(self, guild_id: int, channel_id: int, message_id: int, question: str,
                          options: List[str], multiple_choice: bool, anonymous: bool, end_time: float) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO polls (guild_id, channel_id, message_id, question, options_json, multiple_choice, anonymous, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, channel_id, message_id, question, json.dumps(options), 1 if multiple_choice else 0, 1 if anonymous else 0, end_time))
            await db.commit()
            return cursor.lastrowid

    async def vote_poll(self, poll_id: int, user_id: int, option_idx: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT multiple_choice, is_closed FROM polls WHERE id = ?", (poll_id,))
            poll = await cursor.fetchone()
            if not poll or poll["is_closed"]:
                return False

            if not poll["multiple_choice"]:
                # Single choice: remove previous votes first
                await db.execute("DELETE FROM poll_votes WHERE poll_id = ? AND user_id = ?", (poll_id, user_id))

            try:
                await db.execute("INSERT INTO poll_votes (poll_id, user_id, option_index, timestamp) VALUES (?, ?, ?, ?)",
                                 (poll_id, user_id, option_idx, time.time()))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_poll_results(self, poll_id: int) -> Dict[int, int]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT option_index, COUNT(*) FROM poll_votes WHERE poll_id = ? GROUP BY option_index", (poll_id,))
            return {row[0]: row[1] for row in await cursor.fetchall()}

    # --- Embed Templates ---
    async def save_embed_template(self, guild_id: int, name: str, title: str, description: str,
                                  color: int, thumbnail: str, image: str, author: str, footer: str, fields: List[Dict]) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO embed_templates (guild_id, name, title, description, color, thumbnail, image, author_name, footer_text, fields_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, name) DO UPDATE SET
                    title=excluded.title, description=excluded.description, color=excluded.color,
                    thumbnail=excluded.thumbnail, image=excluded.image, author_name=excluded.author_name,
                    footer_text=excluded.footer_text, fields_json=excluded.fields_json
            """, (guild_id, name.lower(), title, description, color, thumbnail, image, author, footer, json.dumps(fields)))
            await db.commit()
            return True

    async def get_embed_template(self, guild_id: int, name: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM embed_templates WHERE guild_id = ? AND name = ?", (guild_id, name.lower()))
            row = await cursor.fetchone()
            if row:
                d = dict(row)
                d["fields"] = json.loads(d["fields_json"]) if d.get("fields_json") else []
                return d
            return None

# Global instance singleton
db_manager = DatabaseManager()

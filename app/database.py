"""SQLite database layer for the ticket system — persistent across restarts."""

import aiosqlite
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import config

DB_PATH = config.BASE_DIR / "data" / "tickets.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Team members (configurable)
TEAM_MEMBERS = ["Eugene", "Nadia", "Afrah"]


async def init_db():
    """Create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                ticket_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                ticket_id TEXT NOT NULL,
                message_id TEXT,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id),
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        """)
        # Review package support (website overhaul output)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS review_packages (
                ticket_id TEXT PRIMARY KEY,
                review_package_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending_review',
                page_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                reviewed_at TEXT,
                reviewed_by TEXT,
                notes TEXT,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
        """)
        # Failed build scripts — for retry functionality
        await db.execute("""
            CREATE TABLE IF NOT EXISTS failed_scripts (
                ticket_id TEXT PRIMARY KEY,
                script_path TEXT NOT NULL,
                error_msg TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
        """)
        # Plans table — CEO's checklist per ticket
        await db.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id TEXT PRIMARY KEY,
                ticket_id TEXT NOT NULL,
                goal TEXT NOT NULL,
                success_criteria TEXT,
                deliverables TEXT,
                checklist TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'planning',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
        """)
        await db.commit()


def _now():
    return datetime.now().isoformat()


def _uuid():
    return str(uuid.uuid4())[:8]


# ─── Ticket Operations ────────────────────────────────────────────────

async def create_ticket(title: str, created_by: str) -> dict:
    """Create a new ticket. Returns the ticket dict."""
    ticket_id = _uuid()
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tickets (id, title, status, created_by, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (ticket_id, title, "open", created_by, now, now),
        )
        await db.commit()
    return {
        "id": ticket_id, "title": title, "status": "open",
        "created_by": created_by, "created_at": now, "updated_at": now,
    }


async def list_tickets(status_filter: str = "") -> List[dict]:
    """List all tickets, optionally filtered by status."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status_filter:
            cursor = await db.execute(
                "SELECT * FROM tickets WHERE status = ? ORDER BY updated_at DESC", (status_filter,)
            )
        else:
            cursor = await db.execute("SELECT * FROM tickets ORDER BY updated_at DESC")
        rows = await cursor.fetchall()

    tickets = []
    for row in rows:
        ticket = dict(row)
        # Get last message preview
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT content, role FROM messages WHERE ticket_id = ? ORDER BY created_at DESC LIMIT 1",
                (ticket["id"],),
            )
            last_msg = await cursor.fetchone()
            cursor2 = await db.execute(
                "SELECT COUNT(*) as cnt FROM messages WHERE ticket_id = ?", (ticket["id"],)
            )
            count_row = await cursor2.fetchone()
            cursor3 = await db.execute(
                "SELECT COUNT(*) as cnt FROM artifacts WHERE ticket_id = ?", (ticket["id"],)
            )
            art_count_row = await cursor3.fetchone()

        ticket["last_message"] = dict(last_msg)["content"][:100] if last_msg else ""
        ticket["last_role"] = dict(last_msg)["role"] if last_msg else ""
        ticket["message_count"] = dict(count_row)["cnt"] if count_row else 0
        ticket["artifact_count"] = dict(art_count_row)["cnt"] if art_count_row else 0
        tickets.append(ticket)

    return tickets


async def get_ticket(ticket_id: str) -> Optional[dict]:
    """Get a single ticket with all messages and artifacts."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        ticket_row = await cursor.fetchone()
        if not ticket_row:
            return None
        ticket = dict(ticket_row)

        # Get messages
        cursor = await db.execute(
            "SELECT * FROM messages WHERE ticket_id = ? ORDER BY created_at ASC", (ticket_id,)
        )
        messages = [dict(row) for row in await cursor.fetchall()]

        # Get artifacts
        cursor = await db.execute(
            "SELECT * FROM artifacts WHERE ticket_id = ? ORDER BY created_at ASC", (ticket_id,)
        )
        artifacts = [dict(row) for row in await cursor.fetchall()]

    ticket["messages"] = messages
    ticket["artifacts"] = artifacts
    return ticket


async def update_ticket_status(ticket_id: str, status: str) -> Optional[dict]:
    """Update ticket status (open, in_progress, completed)."""
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, ticket_id),
        )
        await db.commit()
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
    return dict(row) if row else None


async def update_ticket_title(ticket_id: str, title: str) -> Optional[dict]:
    """Update ticket title."""
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, ticket_id),
        )
        await db.commit()
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
    return dict(row) if row else None


async def delete_ticket(ticket_id: str) -> bool:
    """Soft-delete: just mark as deleted status."""
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET status = 'deleted', updated_at = ? WHERE id = ?",
            (now, ticket_id),
        )
        await db.commit()
    return True


# ─── Message Operations ───────────────────────────────────────────────

async def add_message(ticket_id: str, role: str, content: str) -> dict:
    """Add a message to a ticket. Also updates ticket timestamp and status."""
    msg_id = _uuid()
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (id, ticket_id, role, content, created_at) VALUES (?,?,?,?,?)",
            (msg_id, ticket_id, role, content, now),
        )
        # Auto-update ticket status to in_progress when user sends a message
        if role == "user":
            await db.execute(
                "UPDATE tickets SET status = 'in_progress', updated_at = ? WHERE id = ?",
                (now, ticket_id),
            )
        else:
            await db.execute(
                "UPDATE tickets SET updated_at = ? WHERE id = ?", (now, ticket_id),
            )
        await db.commit()
    return {"id": msg_id, "ticket_id": ticket_id, "role": role, "content": content, "created_at": now}


async def get_messages(ticket_id: str) -> List[dict]:
    """Get all messages for a ticket in chronological order."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM messages WHERE ticket_id = ? ORDER BY created_at ASC", (ticket_id,)
        )
        return [dict(row) for row in await cursor.fetchall()]


# ─── Artifact Operations ──────────────────────────────────────────────

async def add_artifact(ticket_id: str, file_path: str, message_id: str = "") -> dict:
    """Link an artifact file to a ticket and optionally a message."""
    art_id = _uuid()
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO artifacts (id, ticket_id, message_id, file_path, created_at) VALUES (?,?,?,?,?)",
            (art_id, ticket_id, message_id or "", file_path, now),
        )
        await db.commit()
    return {"id": art_id, "ticket_id": ticket_id, "message_id": message_id, "file_path": file_path, "created_at": now}


async def get_artifacts(ticket_id: str) -> List[dict]:
    """Get all artifacts for a ticket."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM artifacts WHERE ticket_id = ? ORDER BY created_at ASC", (ticket_id,)
        )
        return [dict(row) for row in await cursor.fetchall()]


# ─── Review Package Operations ────────────────────────────────────────────────

async def create_review_package(
    ticket_id: str,
    review_package_path: str,
    page_count: int = 0,
) -> dict:
    """Register a review package for a ticket. Sets ticket status to pending_review."""
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO review_packages
               (ticket_id, review_package_path, status, page_count, created_at)
               VALUES (?, ?, 'pending_review', ?, ?)""",
            (ticket_id, review_package_path, page_count, now),
        )
        # Flip ticket status to pending_review
        await db.execute(
            "UPDATE tickets SET status = 'pending_review', updated_at = ? WHERE id = ?",
            (now, ticket_id),
        )
        await db.commit()

    return {
        "ticket_id": ticket_id,
        "review_package_path": review_package_path,
        "status": "pending_review",
        "page_count": page_count,
        "created_at": now,
    }


async def get_review_package(ticket_id: str) -> Optional[dict]:
    """Get review package for a ticket."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM review_packages WHERE ticket_id = ?", (ticket_id,)
        )
        row = await cursor.fetchone()
    return dict(row) if row else None


async def update_review_status(
    ticket_id: str,
    status: str,  # 'pending_review' | 'approved' | 'changes_requested' | 'applied'
    reviewed_by: str = "",
    notes: str = "",
) -> Optional[dict]:
    """Update review package status after human review."""
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE review_packages
               SET status = ?, reviewed_at = ?, reviewed_by = ?, notes = ?
               WHERE ticket_id = ?""",
            (status, now, reviewed_by, notes, ticket_id),
        )
        # Mirror status to ticket
        ticket_status = status if status in ("approved", "applied") else "pending_review"
        if status == "changes_requested":
            ticket_status = "in_progress"
        await db.execute(
            "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
            (ticket_status, now, ticket_id),
        )
        await db.commit()

    return await get_review_package(ticket_id)


async def list_pending_reviews() -> List[dict]:
    """List all tickets with pending_review status."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT rp.*, t.title, t.created_by
               FROM review_packages rp
               JOIN tickets t ON rp.ticket_id = t.id
               WHERE rp.status = 'pending_review'
               ORDER BY rp.created_at DESC"""
        )
        return [dict(row) for row in await cursor.fetchall()]


# ─── Plan Operations ──────────────────────────────────────────────────────────

async def create_plan(
    ticket_id: str,
    goal: str,
    checklist: list,
    success_criteria: str = "",
    deliverables: list = None,
) -> dict:
    """Create a new plan for a ticket. Returns the plan dict."""
    plan_id = _uuid()
    now = _now()
    deliverables_json = json.dumps(deliverables or [])
    checklist_json = json.dumps(checklist)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO plans
               (id, ticket_id, goal, success_criteria, deliverables, checklist, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'planning', ?, ?)""",
            (plan_id, ticket_id, goal, success_criteria, deliverables_json, checklist_json, now, now),
        )
        await db.commit()
    return {
        "id": plan_id,
        "ticket_id": ticket_id,
        "goal": goal,
        "success_criteria": success_criteria,
        "deliverables": deliverables or [],
        "checklist": checklist,
        "status": "planning",
        "created_at": now,
        "updated_at": now,
    }


async def get_plan(plan_id: str) -> Optional[dict]:
    """Get a plan by ID, with checklist parsed from JSON."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
        row = await cursor.fetchone()
    if not row:
        return None
    plan = dict(row)
    plan["checklist"] = json.loads(plan["checklist"])
    plan["deliverables"] = json.loads(plan["deliverables"] or "[]")
    return plan


async def get_plan_for_ticket(ticket_id: str) -> Optional[dict]:
    """Get the most recent plan for a ticket."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM plans WHERE ticket_id = ? ORDER BY created_at DESC LIMIT 1",
            (ticket_id,),
        )
        row = await cursor.fetchone()
    if not row:
        return None
    plan = dict(row)
    plan["checklist"] = json.loads(plan["checklist"])
    plan["deliverables"] = json.loads(plan["deliverables"] or "[]")
    return plan


async def update_plan_status(plan_id: str, status: str) -> Optional[dict]:
    """Update plan status: 'planning' | 'executing' | 'completed' | 'failed'."""
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE plans SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, plan_id),
        )
        await db.commit()
    return await get_plan(plan_id)


async def update_checklist_item(
    plan_id: str,
    item_id: int,
    status: str,
    file_paths: list = None,
    error: str = "",
) -> Optional[dict]:
    """Update a single checklist item's status and file paths."""
    plan = await get_plan(plan_id)
    if not plan:
        return None
    checklist = plan["checklist"]
    for item in checklist:
        if item.get("id") == item_id:
            item["status"] = status
            if file_paths:
                item["file_paths"] = file_paths
            if error:
                item["error"] = error
            break
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE plans SET checklist = ?, updated_at = ? WHERE id = ?",
            (json.dumps(checklist), now, plan_id),
        )
        await db.commit()
    return await get_plan(plan_id)


async def list_pending_items(plan_id: str) -> list:
    """Return checklist items that are not yet 'done' or 'error'."""
    plan = await get_plan(plan_id)
    if not plan:
        return []
    return [
        item for item in plan["checklist"]
        if item.get("status") not in ("done", "error", "skipped")
    ]


# ─── Failed Script Operations ─────────────────────────────────────────────────

async def save_failed_script(ticket_id: str, script_path: str, error_msg: str) -> None:
    """Store or update a failed build script for a ticket."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO failed_scripts (ticket_id, script_path, error_msg, created_at)
               VALUES (?, ?, ?, ?)""",
            (ticket_id, script_path, error_msg, _now()),
        )
        await db.commit()


async def get_failed_script(ticket_id: str) -> Optional[dict]:
    """Return failed script info for a ticket, or None."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM failed_scripts WHERE ticket_id = ?", (ticket_id,)
        )
        row = await cursor.fetchone()
    return dict(row) if row else None


async def delete_failed_script(ticket_id: str) -> None:
    """Remove failed script record once successfully retried."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM failed_scripts WHERE ticket_id = ?", (ticket_id,))
        await db.commit()

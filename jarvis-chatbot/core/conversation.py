import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "conversations.db")
_MAX_SEARCH_RESULTS = 100
_MAX_EXPORT_LENGTH = 50000


class ConversationManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()
        self._migrate_tables()
        self.current_id: Optional[int] = None
        self.current_title: str = "Nova Conversa"

    def _create_tables(self):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL DEFAULT 'Nova Conversa',
                    provider TEXT DEFAULT '',
                    model TEXT DEFAULT '',
                    pinned INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)"
            )
            cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    content, tokenize='unicode61',
                    content=messages, content_rowid=id
                )
            """)
            try:
                cur.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
            except Exception:
                pass
            self.conn.commit()
            logger.debug("Tabelas do banco criadas/verificadas")

    def _migrate_tables(self):
        with self._lock:
            try:
                self.conn.execute("ALTER TABLE conversations ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")
                self.conn.commit()
                logger.info("Migração: coluna 'pinned' adicionada")
            except Exception:
                pass

    def _sync_fts(self):
        with self._lock:
            try:
                self.conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
                self.conn.commit()
            except Exception as e:
                logger.warning("Falha ao rebuildar FTS: %s", e)

    def new_conversation(self, provider: str = "", model: str = "") -> int:
        with self._lock:
            now = datetime.now().isoformat()
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO conversations (title, provider, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                ("Nova Conversa", provider, model, now, now),
            )
            self.conn.commit()
            self.current_id = cur.lastrowid
            self.current_title = "Nova Conversa"
            return self.current_id

    def rename_conversation(self, conv_id: int, title: str):
        with self._lock:
            self.conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title[:100], datetime.now().isoformat(), conv_id),
            )
            self.conn.commit()
            if conv_id == self.current_id:
                self.current_title = title[:100]

    def add_message(self, role: str, content: str, conv_id: Optional[int] = None):
        with self._lock:
            cid = conv_id or self.current_id
            if cid is None:
                cid = self.new_conversation()
            now = datetime.now().isoformat()
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (cid, role, content[:100000], now),
            )
            msg_id = cur.lastrowid
            self.conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, cid),
            )
            self.conn.commit()
            try:
                self.conn.execute("INSERT INTO messages_fts(rowid, content) VALUES (?, ?)", (msg_id, content[:100000]))
                self.conn.commit()
            except Exception as e:
                logger.warning("Falha ao indexar FTS: %s", e)
            if not self.current_title or self.current_title == "Nova Conversa":
                if role == "user" and len(content) > 10:
                    title = content[:60] + ("..." if len(content) > 60 else "")
                    self.rename_conversation(cid, title)

    def get_messages(self, conv_id: int) -> list[dict]:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id ASC",
                (conv_id,),
            )
            return [{"role": r, "content": c} for r, c in cur.fetchall()]

    def pin_conversation(self, conv_id: int, pinned: bool = True):
        with self._lock:
            self.conn.execute("UPDATE conversations SET pinned = ? WHERE id = ?", (1 if pinned else 0, conv_id))
            self.conn.commit()

    def get_conversations(self, search: str = "") -> list[dict]:
        with self._lock:
            cur = self.conn.cursor()
            if search:
                try:
                    cur.execute(
                        "SELECT DISTINCT c.id, c.title, c.provider, c.model, c.created_at, c.updated_at, c.pinned "
                        "FROM conversations c "
                        "JOIN messages_fts ON messages_fts.content MATCH ? "
                        "JOIN messages m ON messages_fts.rowid = m.id AND m.conversation_id = c.id "
                        "ORDER BY c.pinned DESC, c.updated_at DESC LIMIT ?",
                        (search, _MAX_SEARCH_RESULTS),
                    )
                except Exception:
                    cur.execute(
                        "SELECT DISTINCT c.id, c.title, c.provider, c.model, c.created_at, c.updated_at, "
                        "COALESCE((SELECT pinned FROM conversations WHERE id = c.id), 0) as pinned "
                        "FROM conversations c LEFT JOIN messages m ON c.id = m.conversation_id "
                        "WHERE c.title LIKE ? OR m.content LIKE ? "
                        "ORDER BY pinned DESC, c.updated_at DESC LIMIT ?",
                        (f"%{search}%", f"%{search}%", _MAX_SEARCH_RESULTS),
                    )
            else:
                try:
                    cur.execute(
                        "SELECT id, title, provider, model, created_at, updated_at, pinned FROM conversations ORDER BY pinned DESC, updated_at DESC LIMIT ?",
                        (_MAX_SEARCH_RESULTS,),
                    )
                except Exception:
                    cur.execute(
                        "SELECT id, title, provider, model, created_at, updated_at, 0 as pinned FROM conversations ORDER BY updated_at DESC LIMIT ?",
                        (_MAX_SEARCH_RESULTS,),
                    )
            rows = cur.fetchall()
            return [
                {"id": r[0], "title": r[1], "provider": r[2], "model": r[3], "created_at": r[4], "updated_at": r[5], "pinned": bool(r[6])}
                for r in rows
            ]

    def delete_conversation(self, conv_id: int):
        with self._lock:
            msg_ids = self.conn.execute(
                "SELECT id FROM messages WHERE conversation_id = ?", (conv_id,)
            ).fetchall()
            for (mid,) in msg_ids:
                try:
                    self.conn.execute("DELETE FROM messages_fts WHERE rowid = ?", (mid,))
                except Exception as e:
                    logger.warning("Falha ao limpar FTS para msg %d: %s", mid, e)
            self.conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            self.conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            self.conn.commit()
            if self.current_id == conv_id:
                self.current_id = None
                self.current_title = "Nova Conversa"

    def export_conversation(self, conv_id: int, filepath: str, fmt: str = "txt"):
        with self._lock:
            messages = self.get_messages(conv_id)
            title = ""
            convs = self.get_conversations()
            for c in convs:
                if c["id"] == conv_id:
                    title = c["title"]
                    break

            if fmt == "json":
                data = {"title": title, "messages": messages}
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif fmt == "md":
                lines = [f"# {title}\n"]
                for msg in messages:
                    role = "**Você**" if msg["role"] == "user" else "**JARVIS**"
                    content = msg['content'][:_MAX_EXPORT_LENGTH]
                    lines.append(f"### {role}\n{content}\n")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
            elif fmt == "pdf":
                self._export_pdf(filepath, title, messages)
            else:
                lines = [f"=== {title} ===\n"]
                for msg in messages:
                    role = "Você:" if msg["role"] == "user" else "JARVIS:"
                    content = msg['content'][:_MAX_EXPORT_LENGTH]
                    lines.append(f"{role}\n{content}\n---\n")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

    def _export_pdf(self, filepath: str, title: str, messages: list[dict]):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

            doc = SimpleDocTemplate(filepath, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle("Title2", parent=styles["Title"],
                                          fontSize=18, spaceAfter=12)
            user_style = ParagraphStyle("UserMsg", parent=styles["Normal"],
                                         textColor="#0066ff", spaceBefore=8, spaceAfter=4)
            ai_style = ParagraphStyle("AiMsg", parent=styles["Normal"],
                                       textColor="#00d4ff", spaceBefore=8, spaceAfter=4)
            content_style = ParagraphStyle("Content", parent=styles["Normal"],
                                            fontSize=10, spaceAfter=12)

            elements = [Paragraph(title, title_style), Spacer(1, 0.5*cm)]
            for msg in messages:
                role_label = "Você" if msg["role"] == "user" else "JARVIS"
                role_style = user_style if msg["role"] == "user" else ai_style
                elements.append(Paragraph(f"<b>{role_label}:</b>", role_style))
                text = msg["content"].replace("\n", "<br/>")
                elements.append(Paragraph(text, content_style))
            doc.build(elements)
        except ImportError:
            raise ImportError("reportlab não instalado. Instale com: pip install reportlab")

    def search_messages(self, query: str) -> list[dict]:
        with self._lock:
            cur = self.conn.cursor()
            try:
                cur.execute(
                    "SELECT m.id, m.conversation_id, m.role, snippet(messages_fts, -1, '<b>', '</b>', '...', 32) as preview, m.timestamp, c.title "
                    "FROM messages_fts "
                    "JOIN messages m ON messages_fts.rowid = m.id "
                    "JOIN conversations c ON m.conversation_id = c.id "
                    "WHERE messages_fts MATCH ? "
                    "ORDER BY m.timestamp DESC LIMIT 50",
                    (query,),
                )
            except Exception:
                cur.execute(
                    "SELECT m.id, m.conversation_id, m.role, m.content, m.timestamp, c.title "
                    "FROM messages m JOIN conversations c ON m.conversation_id = c.id "
                    "WHERE m.content LIKE ? ORDER BY m.timestamp DESC LIMIT 50",
                    (f"%{query}%",),
                )
            return [
                {"id": r[0], "conv_id": r[1], "role": r[2], "content": r[3][:200], "timestamp": r[4], "conv_title": r[5]}
                for r in cur.fetchall()
            ]

    def close(self):
        with self._lock:
            self.conn.close()
            logger.debug("Conexão com banco fechada")

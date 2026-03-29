"""Scholar feedback storage for fiqh masail review."""
import sqlite3
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

DB_PATH = os.path.join(os.path.dirname(__file__), 'feedback.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            masala_key TEXT NOT NULL,
            scholar_name TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            comment TEXT DEFAULT '',
            suggested_result TEXT DEFAULT '',
            suggested_hukm TEXT DEFAULT '',
            corrections TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_feedback_masala ON feedback(masala_key);
        CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
    ''')
    conn.close()


init_db()


class FeedbackCreate(BaseModel):
    masala_key: str
    scholar_name: str = ''
    status: str = 'pending'
    comment: str = ''
    suggested_result: str = ''
    suggested_hukm: str = ''
    corrections: str = ''


router = APIRouter(prefix='/api/feedback')


@router.post('/')
def create_feedback(fb: FeedbackCreate):
    now = datetime.utcnow().isoformat()
    conn = get_db()
    cur = conn.execute(
        '''INSERT INTO feedback (masala_key, scholar_name, status, comment,
           suggested_result, suggested_hukm, corrections, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (fb.masala_key, fb.scholar_name, fb.status, fb.comment,
         fb.suggested_result, fb.suggested_hukm, fb.corrections, now, now)
    )
    fb_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {'id': fb_id, 'status': 'created'}


@router.get('/masala/{masala_key}')
def get_feedback_for_masala(masala_key: str):
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM feedback WHERE masala_key = ? ORDER BY created_at DESC',
        (masala_key,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get('/all')
def get_all_feedback(status: Optional[str] = None, limit: int = 100, offset: int = 0):
    conn = get_db()
    if status:
        rows = conn.execute(
            'SELECT * FROM feedback WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (status, limit, offset)
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT * FROM feedback ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get('/stats')
def feedback_stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]
    by_status = conn.execute(
        'SELECT status, COUNT(*) as cnt FROM feedback GROUP BY status'
    ).fetchall()
    by_masala = conn.execute(
        'SELECT masala_key, COUNT(*) as cnt FROM feedback GROUP BY masala_key ORDER BY cnt DESC LIMIT 20'
    ).fetchall()
    conn.close()
    return {
        'total': total,
        'by_status': {r['status']: r['cnt'] for r in by_status},
        'top_masail': [{'masala_key': r['masala_key'], 'count': r['cnt']} for r in by_masala],
    }


@router.put('/{feedback_id}')
def update_feedback(feedback_id: int, fb: FeedbackCreate):
    now = datetime.utcnow().isoformat()
    conn = get_db()
    conn.execute(
        '''UPDATE feedback SET scholar_name=?, status=?, comment=?,
           suggested_result=?, suggested_hukm=?, corrections=?, updated_at=?
           WHERE id=?''',
        (fb.scholar_name, fb.status, fb.comment,
         fb.suggested_result, fb.suggested_hukm, fb.corrections, now, feedback_id)
    )
    conn.commit()
    conn.close()
    return {'id': feedback_id, 'status': 'updated'}


@router.delete('/{feedback_id}')
def delete_feedback(feedback_id: int):
    conn = get_db()
    conn.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
    conn.commit()
    conn.close()
    return {'id': feedback_id, 'status': 'deleted'}

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import psycopg2
import os

router = APIRouter(tags=["CodeQuest Academy"])

DB_URL = os.getenv("FLEMING_DB_URL", "dbname=fleming_db user=fleming_user password=fl3m1ng_db_2026! host=localhost")


def get_conn():
    return psycopg2.connect(DB_URL)


class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    subject: str = ""
    message: str


@router.post("/cqa/messages")
async def create_message(msg: ContactMessage):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO cqa_messages (name, email, subject, message) VALUES (%s, %s, %s, %s) RETURNING id",
            (msg.name, msg.email, msg.subject, msg.message)
        )
        msg_id = cur.fetchone()[0]
        conn.commit()
        return {"id": msg_id, "status": "success"}
    finally:
        conn.close()


@router.get("/cqa/messages")
async def list_messages():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, subject, message, created_at FROM cqa_messages ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [{"id": r[0], "name": r[1], "email": r[2], "subject": r[3], "message": r[4], "created_at": str(r[5])} for r in rows]
    finally:
        conn.close()

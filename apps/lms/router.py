from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
import psycopg2.extras
import json
import os
from .auth import get_current_user

router = APIRouter(prefix="/lms", tags=["LMS"])

DB_URL = os.getenv("FLEMING_DB_URL", "dbname=fleming_db user=fleming_user password=fl3m1ng_db_2026! host=localhost")


def get_conn():
    return psycopg2.connect(DB_URL)


def require_role(user, roles):
    if user["role"] not in roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


# ─── Subjects ─────────────────────────────────────────────────────

@router.get("/subjects")
async def list_subjects():
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM lms_subjects ORDER BY label")
        return cur.fetchall()
    finally:
        conn.close()


@router.post("/subjects")
async def create_subject(slug: str, label: str, emoji: str = "", user=Depends(get_current_user)):
    require_role(user, ["superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO lms_subjects (slug, label, emoji) VALUES (%s, %s, %s) RETURNING id", (slug, label, emoji))
        conn.commit()
        return {"id": cur.fetchone()[0]}
    finally:
        conn.close()


@router.delete("/subjects/{subject_id}")
async def delete_subject(subject_id: int, user=Depends(get_current_user)):
    require_role(user, ["superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM lms_subjects WHERE id = %s", (subject_id,))
        conn.commit()
        return {"status": "deleted"}
    finally:
        conn.close()


# ─── Classes ──────────────────────────────────────────────────────

class ClassModel(BaseModel):
    name: str
    subject_id: Optional[int] = None
    school_id: Optional[int] = None
    code: Optional[str] = None
    description: Optional[str] = None


@router.get("/classes")
async def list_classes(teacher_id: Optional[int] = None, student_id: Optional[int] = None):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if student_id:
            cur.execute("""
                SELECT c.*, s.label as subject_label, s.emoji as subject_emoji,
                    (SELECT COUNT(*) FROM lms_enrollments WHERE class_id = c.id AND status = 'active') as student_count
                FROM lms_classes c
                LEFT JOIN lms_subjects s ON c.subject_id = s.id
                JOIN lms_enrollments e ON e.class_id = c.id AND e.student_id = %s AND e.status = 'active'
                ORDER BY c.name
            """, (student_id,))
        elif teacher_id:
            cur.execute("""
                SELECT c.*, s.label as subject_label, s.emoji as subject_emoji,
                    (SELECT COUNT(*) FROM lms_enrollments WHERE class_id = c.id AND status = 'active') as student_count
                FROM lms_classes c
                LEFT JOIN lms_subjects s ON c.subject_id = s.id
                WHERE c.teacher_id = %s ORDER BY c.name
            """, (teacher_id,))
        else:
            cur.execute("""
                SELECT c.*, s.label as subject_label, s.emoji as subject_emoji,
                    (SELECT COUNT(*) FROM lms_enrollments WHERE class_id = c.id AND status = 'active') as student_count
                FROM lms_classes c
                LEFT JOIN lms_subjects s ON c.subject_id = s.id
                ORDER BY c.name
            """)
        return cur.fetchall()
    finally:
        conn.close()


@router.post("/classes")
async def create_class(cls: ClassModel, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        code = cls.code or f"C{user['id']}{os.urandom(3).hex().upper()}"
        cur.execute(
            "INSERT INTO lms_classes (name, teacher_id, subject_id, school_id, code, description) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
            (cls.name, user["id"], cls.subject_id, cls.school_id, code, cls.description)
        )
        conn.commit()
        return {"id": cur.fetchone()[0], "code": code}
    finally:
        conn.close()


@router.get("/classes/{class_id}")
async def get_class(class_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.*, s.label as subject_label, s.emoji as subject_emoji, u.name as teacher_name
            FROM lms_classes c
            LEFT JOIN lms_subjects s ON c.subject_id = s.id
            LEFT JOIN lms_users u ON c.teacher_id = u.id
            WHERE c.id = %s
        """, (class_id,))
        cls = cur.fetchone()
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        return cls
    finally:
        conn.close()


# ─── Enrollments ──────────────────────────────────────────────────

@router.post("/enrollments")
async def enroll(class_id: int, user=Depends(get_current_user)):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO lms_enrollments (student_id, class_id, status) VALUES (%s, %s, 'pending') ON CONFLICT (student_id, class_id) DO NOTHING RETURNING id",
            (user["id"], class_id)
        )
        conn.commit()
        row = cur.fetchone()
        return {"id": row[0] if row else None, "status": "pending"}
    finally:
        conn.close()


@router.get("/enrollments")
async def list_enrollments(class_id: Optional[int] = None, status: Optional[str] = None):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = "SELECT e.*, u.name as student_name, u.email as student_email FROM lms_enrollments e JOIN lms_users u ON e.student_id = u.id WHERE 1=1"
        params = []
        if class_id:
            query += " AND e.class_id = %s"
            params.append(class_id)
        if status:
            query += " AND e.status = %s"
            params.append(status)
        query += " ORDER BY e.created_at DESC"
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()


@router.put("/enrollments/{enrollment_id}")
async def update_enrollment(enrollment_id: int, status: str, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE lms_enrollments SET status = %s WHERE id = %s", (status, enrollment_id))
        conn.commit()
        return {"status": status}
    finally:
        conn.close()


@router.delete("/enrollments/{enrollment_id}")
async def delete_enrollment(enrollment_id: int, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM lms_enrollments WHERE id = %s", (enrollment_id,))
        conn.commit()
        return {"status": "deleted"}
    finally:
        conn.close()


# ─── Lessons ──────────────────────────────────────────────────────

class LessonModel(BaseModel):
    title: str
    content: Optional[str] = None
    intro: Optional[str] = None
    summary: Optional[str] = None
    chapter_number: Optional[int] = None
    order_index: Optional[int] = 0


@router.get("/classes/{class_id}/lessons")
async def list_lessons(class_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM lms_lessons WHERE class_id = %s ORDER BY order_index, chapter_number", (class_id,))
        return cur.fetchall()
    finally:
        conn.close()


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM lms_lessons WHERE id = %s", (lesson_id,))
        lesson = cur.fetchone()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson
    finally:
        conn.close()


@router.post("/classes/{class_id}/lessons")
async def create_lesson(class_id: int, lesson: LessonModel, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO lms_lessons (class_id, title, content, intro, summary, chapter_number, order_index) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (class_id, lesson.title, lesson.content, lesson.intro, lesson.summary, lesson.chapter_number, lesson.order_index)
        )
        conn.commit()
        return {"id": cur.fetchone()[0]}
    finally:
        conn.close()


@router.put("/lessons/{lesson_id}")
async def update_lesson(lesson_id: int, lesson: LessonModel, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE lms_lessons SET title=%s, content=%s, intro=%s, summary=%s, chapter_number=%s, order_index=%s WHERE id=%s",
            (lesson.title, lesson.content, lesson.intro, lesson.summary, lesson.chapter_number, lesson.order_index, lesson_id)
        )
        conn.commit()
        return {"status": "updated"}
    finally:
        conn.close()


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(lesson_id: int, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM lms_lessons WHERE id = %s", (lesson_id,))
        conn.commit()
        return {"status": "deleted"}
    finally:
        conn.close()


# ─── Quizzes ──────────────────────────────────────────────────────

class QuizModel(BaseModel):
    title: str
    description: Optional[str] = None
    published: bool = False


@router.get("/classes/{class_id}/quizzes")
async def list_quizzes(class_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT q.*, (SELECT COUNT(*) FROM lms_questions WHERE quiz_id = q.id) as question_count
            FROM lms_quizzes q WHERE q.class_id = %s ORDER BY q.created_at
        """, (class_id,))
        return cur.fetchall()
    finally:
        conn.close()


@router.post("/classes/{class_id}/quizzes")
async def create_quiz(class_id: int, quiz: QuizModel, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO lms_quizzes (class_id, title, description, published) VALUES (%s,%s,%s,%s) RETURNING id",
            (class_id, quiz.title, quiz.description, quiz.published)
        )
        conn.commit()
        return {"id": cur.fetchone()[0]}
    finally:
        conn.close()


@router.put("/quizzes/{quiz_id}")
async def update_quiz(quiz_id: int, quiz: QuizModel, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE lms_quizzes SET title=%s, description=%s, published=%s WHERE id=%s",
                     (quiz.title, quiz.description, quiz.published, quiz_id))
        conn.commit()
        return {"status": "updated"}
    finally:
        conn.close()


@router.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: int, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM lms_quizzes WHERE id = %s", (quiz_id,))
        conn.commit()
        return {"status": "deleted"}
    finally:
        conn.close()


# ─── Questions ────────────────────────────────────────────────────

class QuestionModel(BaseModel):
    body: str
    type: str = "multiple_choice"
    options: Optional[list] = None
    correct_answer: Optional[str] = None
    hint_lesson_id: Optional[int] = None
    hint_text: Optional[str] = None
    order_num: int = 0


@router.get("/quizzes/{quiz_id}/questions")
async def list_questions(quiz_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM lms_questions WHERE quiz_id = %s ORDER BY order_num", (quiz_id,))
        return cur.fetchall()
    finally:
        conn.close()


@router.post("/quizzes/{quiz_id}/questions")
async def create_question(quiz_id: int, q: QuestionModel, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO lms_questions (quiz_id, body, type, options, correct_answer, hint_lesson_id, hint_text, order_num) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (quiz_id, q.body, q.type, json.dumps(q.options) if q.options else None, q.correct_answer, q.hint_lesson_id, q.hint_text, q.order_num)
        )
        conn.commit()
        return {"id": cur.fetchone()[0]}
    finally:
        conn.close()


@router.put("/questions/{question_id}")
async def update_question(question_id: int, q: QuestionModel, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE lms_questions SET body=%s, type=%s, options=%s, correct_answer=%s, hint_lesson_id=%s, hint_text=%s, order_num=%s WHERE id=%s",
            (q.body, q.type, json.dumps(q.options) if q.options else None, q.correct_answer, q.hint_lesson_id, q.hint_text, q.order_num, question_id)
        )
        conn.commit()
        return {"status": "updated"}
    finally:
        conn.close()


@router.delete("/questions/{question_id}")
async def delete_question(question_id: int, user=Depends(get_current_user)):
    require_role(user, ["teacher", "superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM lms_questions WHERE id = %s", (question_id,))
        conn.commit()
        return {"status": "deleted"}
    finally:
        conn.close()


# ─── Quiz Taking & Grading ───────────────────────────────────────

class SubmitQuizModel(BaseModel):
    answers: list  # [{question_id: int, answer: str}, ...]


@router.post("/quizzes/{quiz_id}/attempt")
async def submit_quiz(quiz_id: int, submission: SubmitQuizModel, user=Depends(get_current_user)):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Get correct answers
        cur.execute("SELECT id, correct_answer, type FROM lms_questions WHERE quiz_id = %s", (quiz_id,))
        questions = {q["id"]: q for q in cur.fetchall()}
        total = len(questions)
        score = 0
        graded_answers = []
        for ans in submission.answers:
            q = questions.get(ans.get("question_id"))
            if not q:
                continue
            correct = False
            if q["correct_answer"]:
                if q["type"] == "short_answer":
                    correct = ans.get("answer", "").strip().lower() == q["correct_answer"].strip().lower()
                else:
                    correct = ans.get("answer") == q["correct_answer"]
            if correct:
                score += 1
            graded_answers.append({"question_id": ans["question_id"], "answer": ans.get("answer", ""), "correct": correct})

        # Create attempt
        cur.execute(
            "INSERT INTO lms_quiz_attempts (quiz_id, student_id, score, total, completed, completed_at) VALUES (%s,%s,%s,%s,TRUE,NOW()) RETURNING id",
            (quiz_id, user["id"], score, total)
        )
        attempt_id = cur.fetchone()["id"]

        # Save answers
        for ga in graded_answers:
            cur.execute(
                "INSERT INTO lms_quiz_answers (attempt_id, question_id, answer, correct) VALUES (%s,%s,%s,%s)",
                (attempt_id, ga["question_id"], ga["answer"], ga["correct"])
            )
        conn.commit()
        return {"attempt_id": attempt_id, "score": score, "total": total}
    finally:
        conn.close()


@router.get("/attempts/{attempt_id}")
async def get_attempt(attempt_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM lms_quiz_attempts WHERE id = %s", (attempt_id,))
        attempt = cur.fetchone()
        if not attempt:
            raise HTTPException(status_code=404, detail="Attempt not found")
        cur.execute("""
            SELECT a.*, q.body, q.type, q.options, q.correct_answer, q.hint_text
            FROM lms_quiz_answers a
            JOIN lms_questions q ON a.question_id = q.id
            WHERE a.attempt_id = %s ORDER BY q.order_num
        """, (attempt_id,))
        attempt["answers"] = cur.fetchall()
        return attempt
    finally:
        conn.close()


# ─── Messages ─────────────────────────────────────────────────────

class MessageModel(BaseModel):
    to_id: int
    body: str
    class_id: Optional[int] = None


@router.get("/messages")
async def list_messages(user=Depends(get_current_user)):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT m.*,
                f.name as from_name, f.email as from_email,
                t.name as to_name, t.email as to_email
            FROM lms_messages m
            JOIN lms_users f ON m.from_id = f.id
            JOIN lms_users t ON m.to_id = t.id
            WHERE m.from_id = %s OR m.to_id = %s
            ORDER BY m.created_at DESC
        """, (user["id"], user["id"]))
        return cur.fetchall()
    finally:
        conn.close()


@router.post("/messages")
async def send_message(msg: MessageModel, user=Depends(get_current_user)):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO lms_messages (from_id, to_id, body, class_id) VALUES (%s,%s,%s,%s) RETURNING id",
            (user["id"], msg.to_id, msg.body, msg.class_id)
        )
        conn.commit()
        return {"id": cur.fetchone()[0]}
    finally:
        conn.close()


@router.put("/messages/{message_id}/read")
async def mark_read(message_id: int, user=Depends(get_current_user)):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE lms_messages SET read = TRUE WHERE id = %s AND to_id = %s", (message_id, user["id"]))
        conn.commit()
        return {"status": "read"}
    finally:
        conn.close()


# ─── Admin ────────────────────────────────────────────────────────

@router.get("/admin/users")
async def list_users(user=Depends(get_current_user)):
    require_role(user, ["superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, email, name, role, org, state, created_at FROM lms_users ORDER BY created_at DESC")
        return cur.fetchall()
    finally:
        conn.close()


@router.put("/admin/users/{user_id}/role")
async def set_user_role(user_id: int, role: str, user=Depends(get_current_user)):
    require_role(user, ["superadmin"])
    if role not in ("student", "teacher", "superadmin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE lms_users SET role = %s WHERE id = %s", (role, user_id))
        conn.commit()
        return {"status": "updated"}
    finally:
        conn.close()


@router.get("/admin/schools")
async def list_schools(user=Depends(get_current_user)):
    require_role(user, ["superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM lms_schools ORDER BY name")
        return cur.fetchall()
    finally:
        conn.close()


@router.get("/admin/teacher-subjects")
async def list_teacher_subjects(user=Depends(get_current_user)):
    require_role(user, ["superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT ts.*, u.name as teacher_name, s.label as subject_label
            FROM lms_teacher_subjects ts
            JOIN lms_users u ON ts.teacher_id = u.id
            JOIN lms_subjects s ON ts.subject_id = s.id
        """)
        return cur.fetchall()
    finally:
        conn.close()


@router.post("/admin/teacher-subjects")
async def assign_teacher_subject(teacher_id: int, subject_id: int, user=Depends(get_current_user)):
    require_role(user, ["superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO lms_teacher_subjects (teacher_id, subject_id) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING id",
            (teacher_id, subject_id)
        )
        conn.commit()
        return {"status": "assigned"}
    finally:
        conn.close()


@router.delete("/admin/teacher-subjects/{ts_id}")
async def unassign_teacher_subject(ts_id: int, user=Depends(get_current_user)):
    require_role(user, ["superadmin"])
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM lms_teacher_subjects WHERE id = %s", (ts_id,))
        conn.commit()
        return {"status": "deleted"}
    finally:
        conn.close()

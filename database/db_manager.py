import sqlite3
import os
from typing import List, Dict, Any, Tuple

DB_PATH = os.getenv("DATABASE_PATH", "video_assistant.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Check if table already initialized
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='VIDEO'")
    if not cursor.fetchone():
        if os.path.exists("database.sql"):
            with open("database.sql", "r", encoding="utf-8") as f:
                cursor.executescript(f.read())
    conn.commit()
    conn.close()

def insert_video(file_name: str, file_path: str, duration: float, uploaded_by: str = "Student_Candidate") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO VIDEO (file_name, file_path, duration, uploaded_by) VALUES (?, ?, ?, ?)",
        (file_name, file_path, duration, uploaded_by)
    )
    video_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return video_id

def insert_transcripts(video_id: int, segments: List[Dict[str, Any]]):
    conn = get_connection()
    cursor = conn.cursor()
    for seg in segments:
        cursor.execute(
            "INSERT INTO TRANSCRIPT (video_id, text, start_time, end_time) VALUES (?, ?, ?, ?)",
            (video_id, seg["text"], seg["start"], seg["end"])
        )
    conn.commit()
    conn.close()

def insert_chunks(video_id: int, chunks: List[Dict[str, Any]]):
    conn = get_connection()
    cursor = conn.cursor()
    for idx, chk in enumerate(chunks):
        cursor.execute(
            """INSERT INTO VIDEO_CHUNK (video_id, chunk_index, chunk_text, start_time, end_time, vector_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (video_id, idx, chk["text"], chk["start"], chk["end"], f"chk_{video_id}_{idx}")
        )
    conn.commit()
    conn.close()

def log_query(video_id: int, question: str, answer: str, retrieved_chunk_ids: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO QUERY_HISTORY (video_id, question, answer, retrieved_chunk_ids) VALUES (?, ?, ?, ?)",
        (video_id, question, answer, retrieved_chunk_ids)
    )
    conn.commit()
    conn.close()

def get_all_videos() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM VIDEO ORDER BY uploaded_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_transcripts_for_video(video_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM TRANSCRIPT WHERE video_id = ? ORDER BY start_time ASC", (video_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_chunks_for_video(video_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM VIDEO_CHUNK WHERE video_id = ? ORDER BY start_time ASC", (video_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_query_history(video_id: int = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if video_id:
        cursor.execute("SELECT * FROM QUERY_HISTORY WHERE video_id = ? ORDER BY created_at DESC", (video_id,))
    else:
        cursor.execute("""
            SELECT q.*, v.file_name 
            FROM QUERY_HISTORY q 
            JOIN VIDEO v ON q.video_id = v.video_id 
            ORDER BY q.created_at DESC
        """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def run_custom_query(query: str, params: tuple = ()) -> Tuple[List[str], List[Tuple]]:
    clean_query = query.strip()
    first_word = clean_query.split()[0].upper() if clean_query else ""
    if first_word != "SELECT":
        raise ValueError("Security Policy Violation: Only read-only SELECT queries are permitted.")

    sub_statements = [s.strip() for s in clean_query.split(";") if s.strip()]
    if len(sub_statements) > 1:
        raise ValueError("Multi-statement query execution is forbidden for SQL injection protection.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    columns = [col[0] for col in cursor.description] if cursor.description else []
    rows = cursor.fetchall()
    conn.close()
    return columns, rows

def insert_chapters(video_id: int, chapters: List[Dict[str, Any]]):
    conn = get_connection()
    cursor = conn.cursor()
    for ch in chapters:
        cursor.execute(
            """INSERT INTO MOVIE_CHAPTER (video_id, chapter_num, title, start_time, end_time, summary, characters)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (video_id, ch.get("chapter_num", 0), ch.get("title", ""),
             ch.get("start_time", 0.0), ch.get("end_time", 0.0),
             ch.get("summary", ""), ch.get("characters", ""))
        )
    conn.commit()
    conn.close()

def get_chapters_for_video(video_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM MOVIE_CHAPTER WHERE video_id = ? ORDER BY chapter_num ASC", (video_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def insert_review(video_id: int, review_text: str, notes_text: str, summary_text: str, rating: float = 0.0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO MOVIE_REVIEW (video_id, review_text, notes_text, summary_text, rating)
           VALUES (?, ?, ?, ?, ?)""",
        (video_id, review_text, notes_text, summary_text, rating)
    )
    conn.commit()
    conn.close()

def get_review_for_video(video_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM MOVIE_REVIEW WHERE video_id = ? ORDER BY created_at DESC LIMIT 1", (video_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

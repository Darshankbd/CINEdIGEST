-- ========================================================
-- e2eRosh IT Solutions - Project 3: AI Video Knowledge Assistant
-- Database Schema: SQLite / MySQL Compatible
-- ========================================================

-- Enable Foreign Key Support
PRAGMA foreign_keys = ON;

-- 1. VIDEO TABLE
CREATE TABLE IF NOT EXISTS VIDEO (
    video_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    duration REAL DEFAULT 0.0,
    uploaded_by VARCHAR(100) DEFAULT 'Student_User',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TRANSCRIPT TABLE
CREATE TABLE IF NOT EXISTS TRANSCRIPT (
    transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    FOREIGN KEY (video_id) REFERENCES VIDEO(video_id) ON DELETE CASCADE
);

-- 3. VIDEO_CHUNK TABLE (For RAG Vector mapping & timestamp provenance)
CREATE TABLE IF NOT EXISTS VIDEO_CHUNK (
    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    vector_id VARCHAR(100),
    FOREIGN KEY (video_id) REFERENCES VIDEO(video_id) ON DELETE CASCADE
);

-- 4. QUERY_HISTORY TABLE
CREATE TABLE IF NOT EXISTS QUERY_HISTORY (
    query_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    retrieved_chunk_ids TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES VIDEO(video_id) ON DELETE CASCADE
);

-- 5. MOVIE_CHAPTER TABLE (For sequential story chapter breakdowns)
CREATE TABLE IF NOT EXISTS MOVIE_CHAPTER (
    chapter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    chapter_num INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    summary TEXT,
    characters TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES VIDEO(video_id) ON DELETE CASCADE
);

-- 6. MOVIE_REVIEW TABLE (For AI-generated reviews, notes, summaries)
CREATE TABLE IF NOT EXISTS MOVIE_REVIEW (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    review_text TEXT,
    notes_text TEXT,
    summary_text TEXT,
    rating REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES VIDEO(video_id) ON DELETE CASCADE
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_transcript_video ON TRANSCRIPT(video_id);
CREATE INDEX IF NOT EXISTS idx_chunk_video ON VIDEO_CHUNK(video_id);
CREATE INDEX IF NOT EXISTS idx_query_video ON QUERY_HISTORY(video_id);
CREATE INDEX IF NOT EXISTS idx_chapter_video ON MOVIE_CHAPTER(video_id);
CREATE INDEX IF NOT EXISTS idx_review_video ON MOVIE_REVIEW(video_id);

-- ========================================================
-- SAMPLE SEED DATA
-- ========================================================
INSERT INTO VIDEO (file_name, file_path, duration, uploaded_by) 
VALUES ('Python_OOP_Lecture.mp4', 'uploads/Python_OOP_Lecture.mp4', 1200.0, 'Campus_Candidate');

INSERT INTO TRANSCRIPT (video_id, text, start_time, end_time) VALUES
(1, 'Welcome everyone. Today we will cover Object Oriented Programming in Python.', 0.0, 15.0),
(1, 'Classes are blueprints for creating objects. An object is an instance of a class.', 15.1, 45.0),
(1, 'Inheritance allows a class to inherit methods and properties from another class.', 45.1, 90.0),
(1, 'Polymorphism allows methods to have the same name but different implementations.', 90.1, 140.0),
(1, 'To wrap up, encapsulation restricts direct access to some of an object components.', 140.1, 180.0);

INSERT INTO VIDEO_CHUNK (video_id, chunk_index, chunk_text, start_time, end_time, vector_id) VALUES
(1, 0, 'Welcome everyone. Today we will cover Object Oriented Programming in Python. Classes are blueprints.', 0.0, 45.0, 'chk_1_0'),
(1, 1, 'Inheritance allows a class to inherit methods and properties from another class.', 45.1, 90.0, 'chk_1_1'),
(1, 2, 'Polymorphism allows methods to have the same name but different implementations.', 90.1, 140.0, 'chk_1_2'),
(1, 3, 'To wrap up, encapsulation restricts direct access to some of an object components.', 140.1, 180.0, 'chk_1_3');

INSERT INTO QUERY_HISTORY (video_id, question, answer, retrieved_chunk_ids) VALUES
(1, 'Explain the topic of inheritance', 'Inheritance allows a child class to inherit attributes and methods from a parent class.', 'chk_1_1'),
(1, 'What are the main concepts discussed?', 'The main concepts discussed are OOP principles: Classes, Inheritance, Polymorphism, and Encapsulation.', 'chk_1_0,chk_1_1,chk_1_2');

-- ========================================================
-- 5 MANDATORY SQL QUERIES (For Technical Viva / Discussion)
-- ========================================================

-- Query 1: Multi-Table JOIN with Filtering
-- Retrieves user queries along with video title and length
SELECT 
    v.video_id,
    v.file_name,
    v.duration,
    q.question,
    q.answer,
    q.created_at
FROM VIDEO v
INNER JOIN QUERY_HISTORY q ON v.video_id = q.video_id
WHERE v.duration > 300
ORDER BY q.created_at DESC;

-- Query 2: Aggregation & GROUP BY
-- Computes total chunks, average chunk duration, and question count per video
SELECT 
    v.video_id,
    v.file_name,
    COUNT(DISTINCT c.chunk_id) AS total_chunks,
    ROUND(AVG(c.end_time - c.start_time), 2) AS avg_chunk_duration_sec,
    COUNT(DISTINCT q.query_id) AS total_questions_asked
FROM VIDEO v
LEFT JOIN VIDEO_CHUNK c ON v.video_id = c.video_id
LEFT JOIN QUERY_HISTORY q ON v.video_id = q.video_id
GROUP BY v.video_id, v.file_name;

-- Query 3: HAVING Clause with Conditional Aggregation
-- Identifies videos that have been actively queried (more than 1 question asked)
SELECT 
    v.file_name,
    COUNT(q.query_id) AS query_count,
    MAX(q.created_at) AS latest_query_time
FROM VIDEO v
JOIN QUERY_HISTORY q ON v.video_id = q.video_id
GROUP BY v.video_id, v.file_name
HAVING COUNT(q.query_id) >= 1;

-- Query 4: Subquery (Scalar)
-- Find video chunks that have longer duration than the overall average chunk length
SELECT 
    chunk_id,
    video_id,
    ROUND(end_time - start_time, 2) AS chunk_length,
    chunk_text
FROM VIDEO_CHUNK
WHERE (end_time - start_time) >= (
    SELECT AVG(end_time - start_time) FROM VIDEO_CHUNK
);

-- Query 5: Complex Text Search with LIKE & JOIN
-- Finds which videos mention specific core topics in their chunks
SELECT 
    v.file_name,
    c.chunk_index,
    c.start_time,
    c.end_time,
    c.chunk_text
FROM VIDEO v
JOIN VIDEO_CHUNK c ON v.video_id = c.video_id
WHERE LOWER(c.chunk_text) LIKE '%inheritance%' 
   OR LOWER(c.chunk_text) LIKE '%polymorphism%'
ORDER BY c.start_time ASC;

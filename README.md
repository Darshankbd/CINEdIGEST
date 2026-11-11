# 🎬 CineDigest — Movie Review & Summary Platform

An AI-powered platform that transforms any movie into a comprehensive review, chapter breakdown, and downloadable PDF report — designed for busy people who don't have time to watch full 3-hour films.

---

## 🚀 Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Movie Upload** | Upload any video file (MP4, MKV, AVI, MOV, WEBM) |
| 2 | **Audio Extraction** | Automatic 16kHz mono WAV extraction via FFmpeg |
| 3 | **AI Transcription** | Gemini 2.5 Flash transcribes with timestamps & speaker identification |
| 4 | **Chunked Processing** | Handles 3-hour movies by splitting audio into 10-min chunks |
| 5 | **Story Chapters** | AI generates 10-15 sequential story chapters with timestamps |
| 6 | **Scene Notes** | Comprehensive topic-by-topic notes covering every scene |
| 7 | **Movie Review** | Professional review with plot synopsis, character analysis, themes |
| 8 | **Executive Summary** | 300-500 word summary for quick understanding |
| 9 | **PDF Export** | Download everything as a professionally styled PDF report |
| 10 | **SQLite Database** | All data persisted across 6 normalized tables |

---

## 🏗️ Architecture

```
Movie Upload ➔ Audio Extraction ➔ AI Transcription ➔ Chapter Generation
                                                      ➔ Notes Generation
                                                      ➔ Review & Summary
                                                      ➔ PDF Export
```

### Tech Stack
- **Frontend**: Streamlit (Python)
- **AI Engine**: Google Gemini 2.5 Flash (multimodal)
- **Database**: SQLite (6 tables: VIDEO, TRANSCRIPT, VIDEO_CHUNK, QUERY_HISTORY, MOVIE_CHAPTER, MOVIE_REVIEW)
- **Audio**: imageio-ffmpeg (bundled FFmpeg binary)
- **PDF**: ReportLab (professional PDF generation)
- **Vector Search**: ChromaDB / Lightweight cosine similarity fallback

---

## 📁 Project Structure

```
project e2e it solutions/
├── app.py                      # Main Streamlit UI (6 tabs)
├── core/
│   ├── audio_extractor.py      # FFmpeg audio extraction
│   ├── transcriber.py          # AI transcription with chunked processing
│   ├── movie_analyzer.py       # AI chapter/notes/review/summary generator
│   ├── rag_engine.py           # Vector search & RAG Q&A engine
│   └── pdf_generator.py        # Professional PDF report builder
├── database/
│   └── db_manager.py           # SQLite CRUD operations
├── database.sql                # Schema DDL + seed data + 5 SQL queries
├── static/uploads/             # Uploaded movie files
├── requirements.txt            # Python dependencies
├── .env                        # GEMINI_API_KEY configuration
└── README.md                   # This file
```

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
Create a `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_PATH=video_assistant.db
```

### 3. Run the App
```bash
python -m streamlit run app.py
```

### 4. Use the Platform
1. Go to **Tab 1** → Upload any movie file
2. Click **"Run Full Movie Analysis Pipeline"**
3. Browse chapters, notes, review in **Tabs 2-5**
4. Download the complete PDF report in **Tab 6**

---

## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `VIDEO` | Stores uploaded video metadata |
| `TRANSCRIPT` | Timestamped transcript segments |
| `VIDEO_CHUNK` | Semantic chunks for vector search |
| `QUERY_HISTORY` | RAG Q&A query log |
| `MOVIE_CHAPTER` | AI-generated story chapters |
| `MOVIE_REVIEW` | AI review, notes, summary, rating |

---

## 📋 5 Mandatory SQL Queries

1. **Multi-Table JOIN** — Video + Query History with filtering
2. **Aggregation & GROUP BY** — Chunk counts and query stats per video
3. **HAVING Clause** — Actively queried videos
4. **Subquery** — Above-average duration chunks
5. **Pattern Search with LIKE & JOIN** — Topic keyword search

---

## 🎯 Target Audience

Busy professionals who want to:
- Understand a 3-hour movie in 5 minutes
- Get chapter-by-chapter story breakdowns
- Read professional AI-generated reviews
- Download offline PDF reports

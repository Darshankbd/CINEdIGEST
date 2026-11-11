# Test Cases Document

**Project**: AI Video Knowledge Assistant (Project 3)  
**Company Assessment**: e2eRosh IT Solutions, Bangalore  
**Target**: BE/B.Tech 7th Semester Campus Technical Assessment  

---

| Test Case ID | Feature / Component | Test Input | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Video Ingestion | Upload `How does Bluetooth Work__720p.mp4` | Video accepts format, extracts audio stream, displays video player | Video player renders; 16kHz audio extracted | **PASS** |
| **TC-02** | Audio Extraction & Audio Player | Extracted audio track | Audio player embedded in UI plays 16kHz mono audio cleanly | Audio player loads and plays track | **PASS** |
| **TC-03** | Time-Aligned Transcription | Audio stream input | Produces timestamp-bounded segments with start and end times | Segments generated with continuous timestamps | **PASS** |
| **TC-04** | Speaker Diarization | Audio segments | Identifies and tags speakers (Speaker 1: Instructor, Speaker 2: Co-Presenter) | Speaker tags attached to each transcript segment | **PASS** |
| **TC-05** | Relational Database Storage | Ingestion completion | Persists records in `VIDEO`, `TRANSCRIPT`, `VIDEO_CHUNK` tables | Records verified in live SQL Table Inspector | **PASS** |
| **TC-06** | Semantic RAG Retrieval | Query: *"How does Bluetooth avoid interference?"* | Retrieves relevant chunk mentioning FHSS (Frequency Hopping) with high similarity | Top match retrieved with 92.5% similarity score | **PASS** |
| **TC-07** | Timestamp-based Answers | Query: *"What was discussed around 15 minutes?"* | Answers with exact timestamp interval citation `[01:25 - 03:15]` | Displays exact timestamp box and chunk evidence | **PASS** |
| **TC-08** | Structured Notes Export | Click 'Download Notes (.txt)' button | Downloads formatted markdown lecture notes file | Plain text/markdown notes generated and downloaded | **PASS** |
| **TC-09** | Chapters & Summaries | Video chunks | Automatically partitions video into named chapters with time boundaries | Structured chapters rendered with collapsible cards | **PASS** |
| **TC-10** | Interactive 10-Question Quiz & Grading | Select MCQ options from 10 randomized questions and click submit | Evaluates user selections, calculates score out of 10, and explains answers | Scores calculated out of 10 with detailed explanations and performance badge | **PASS** |
| **TC-11** | Study Flashcards | Click flashcard expander | Reveals question on front and answer on back | Flashcard flip displays hidden answers | **PASS** |
| **TC-12** | Multi-Language Translation | Translate summary to Spanish/French/German/Hindi | Translates technical summary to selected language | Translated summary rendered accurately | **PASS** |
| **TC-13** | SQL Security & 5 Queries | Execute 5 advanced SQL queries (Joins, Aggregations, Subqueries) | Queries execute successfully; dangerous operations (`DROP`, `DELETE`) blocked | All 5 queries return expected records; attacks rejected | **PASS** |

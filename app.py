import streamlit as st
import os
import time
import re
import pandas as pd
import importlib
from dotenv import load_dotenv

load_dotenv()

# Bridge Streamlit Cloud Secrets into environment if present
try:
    if "GEMINI_API_KEY" in st.secrets and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = str(st.secrets["GEMINI_API_KEY"]).strip()
except Exception:
    pass

import database.db_manager
importlib.reload(database.db_manager)
from database.db_manager import (
    init_db, insert_video, insert_transcripts, insert_chunks, log_query,
    get_all_videos, get_transcripts_for_video, get_chunks_for_video,
    get_query_history, run_custom_query,
    insert_chapters, get_chapters_for_video, insert_review, get_review_for_video
)

from core.audio_extractor import extract_audio
import core.transcriber
importlib.reload(core.transcriber)
from core.transcriber import transcribe_audio

import core.rag_engine
importlib.reload(core.rag_engine)
from core.rag_engine import VideoRAGEngine

from core.movie_analyzer import MovieAnalyzer
from core.pdf_generator import generate_movie_pdf

# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CineDigest — Movie Review & Summary Platform",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS for premium look ──
st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #1a237e, #ff6f00); }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #e8eaf6 0%, #c5cae9 100%);
        border-radius: 12px; padding: 12px 16px;
        border-left: 4px solid #1a237e;
    }
    .chapter-card {
        background: linear-gradient(135deg, #fafafa, #f5f5f5);
        border-radius: 10px; padding: 16px; margin-bottom: 10px;
        border-left: 4px solid #ff6f00;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
init_db()

# ── Ensure new tables exist ──
try:
    from database.db_manager import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS MOVIE_CHAPTER (
        chapter_id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER NOT NULL, chapter_num INTEGER NOT NULL,
        title VARCHAR(500) NOT NULL, start_time REAL NOT NULL, end_time REAL NOT NULL,
        summary TEXT, characters TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (video_id) REFERENCES VIDEO(video_id) ON DELETE CASCADE)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS MOVIE_REVIEW (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER NOT NULL, review_text TEXT, notes_text TEXT,
        summary_text TEXT, rating REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (video_id) REFERENCES VIDEO(video_id) ON DELETE CASCADE)""")
    conn.commit()
    conn.close()
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
st.sidebar.markdown("## 🎬 CineDigest")
st.sidebar.caption("Movie Review & Summary Platform")
st.sidebar.markdown("---")

api_key = os.getenv("GEMINI_API_KEY", "").strip()
if api_key:
    st.sidebar.success("🟢 Gemini AI Connected")
else:
    st.sidebar.warning("🟡 Offline Mode (No API Key)")

st.sidebar.info(
    "📌 Upload any movie → AI transcribes, generates chapters, "
    "notes, review & downloadable PDF report."
)

nav = st.sidebar.radio(
    "Navigation",
    [
        "🎬 1. Upload & Process Movie",
        "📜 2. Full Transcript",
        "📑 3. Story Chapters",
        "📝 4. Notes & Review",
        "📊 5. Summary Dashboard",
        "📥 6. Download PDF Report",
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Pipeline:**\n"
    "`Movie` ➔ `Audio` ➔ `Transcription` ➔ `Chapters` ➔ `Notes` ➔ `Review` ➔ `PDF`"
)

# ═══════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = VideoRAGEngine()
if "movie_analyzer" not in st.session_state:
    st.session_state.movie_analyzer = MovieAnalyzer()
if "current_video_id" not in st.session_state:
    st.session_state.current_video_id = None
if "current_segments" not in st.session_state:
    st.session_state.current_segments = []
if "current_chunks" not in st.session_state:
    st.session_state.current_chunks = []
if "current_chapters" not in st.session_state:
    st.session_state.current_chapters = []
if "current_notes" not in st.session_state:
    st.session_state.current_notes = ""
if "current_review" not in st.session_state:
    st.session_state.current_review = ""
if "current_summary" not in st.session_state:
    st.session_state.current_summary = ""
if "movie_title" not in st.session_state:
    st.session_state.movie_title = ""
if "movie_duration" not in st.session_state:
    st.session_state.movie_duration = 0.0
if "pipeline_complete" not in st.session_state:
    st.session_state.pipeline_complete = False

def _fmt(seconds: float) -> str:
    """Format seconds to HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# ═══════════════════════════════════════════════════════════════
# TAB 1: UPLOAD & PROCESS MOVIE
# ═══════════════════════════════════════════════════════════════
if "1. Upload" in nav:
    st.title("🎬 Upload & Process Movie")
    st.markdown(
        "Choose how you want to analyze a movie — **upload a video file** or simply **search by name**."
    )

    input_mode = st.radio(
        "Choose input method:",
        ["📁 Upload Video File", "🔍 Search by Movie Name"],
        horizontal=True
    )

    st.markdown("---")

    # ── OPTION 1: Upload Video File ──
    if "Upload" in input_mode:
        c1, c2 = st.columns([1, 1], gap="large")

        with c1:
            st.subheader("📁 Movie Upload")
            uploaded_file = st.file_uploader(
                "Upload your movie file",
                type=["mp4", "mkv", "avi", "mov", "webm"],
                help="Supports up to 5 GB. Larger files take longer to process."
            )

            video_path = None
            if uploaded_file is not None:
                os.makedirs("static/uploads", exist_ok=True)
                video_path = os.path.join("static/uploads", uploaded_file.name)
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.video(video_path)
                file_size_mb = len(uploaded_file.getbuffer()) / (1024 * 1024)
                st.success(f"**{uploaded_file.name}** | Size: **{file_size_mb:.1f} MB**")

        with c2:
            st.subheader("⚡ AI Processing Pipeline")
            vname = uploaded_file.name if uploaded_file else ""

            st.markdown(
                "| Step | Description |\n"
                "|:-----|:------------|\n"
                "| 1 | Extract 16kHz audio from video |\n"
                "| 2 | AI transcription with timestamps |\n"
                "| 3 | Store transcript in database |\n"
                "| 4 | Generate story chapters |\n"
                "| 5 | Generate detailed notes |\n"
                "| 6 | Generate movie review & summary |\n"
            )

            if st.button("🚀 Run Full Movie Analysis Pipeline", type="primary", use_container_width=True):
                if not video_path:
                    st.error("Please upload a movie file first!")
                else:
                    pbar = st.progress(0)
                    status = st.empty()
                    analyzer = st.session_state.movie_analyzer

                    status.info("⏳ Step 1/6: Extracting audio from movie...")
                    audio_out = extract_audio(video_path)
                    pbar.progress(10)
                    time.sleep(0.2)

                    status.info("⏳ Step 2/6: AI transcribing movie dialogue...")
                    segments = transcribe_audio(audio_out, video_name=vname, video_path=video_path)
                    st.session_state.current_segments = segments
                    pbar.progress(30)

                    status.info("⏳ Step 3/6: Storing transcript in database...")
                    duration = segments[-1]["end"] if segments else 120.0
                    vid_id = insert_video(vname, video_path, duration)
                    insert_transcripts(vid_id, segments)
                    chunks = st.session_state.rag_engine.chunk_transcript(segments)
                    insert_chunks(vid_id, chunks)
                    st.session_state.current_chunks = chunks
                    st.session_state.rag_engine.index_video(vid_id, chunks)
                    st.session_state.current_video_id = vid_id
                    st.session_state.movie_title = vname
                    st.session_state.movie_duration = duration
                    pbar.progress(40)

                    status.info("⏳ Step 4/6: AI generating story chapters...")
                    chapters = analyzer.generate_chapters(segments)
                    st.session_state.current_chapters = chapters
                    insert_chapters(vid_id, chapters)
                    pbar.progress(60)

                    status.info("⏳ Step 5/6: AI generating detailed scene notes...")
                    notes = analyzer.generate_notes(segments)
                    st.session_state.current_notes = notes
                    pbar.progress(80)

                    status.info("⏳ Step 6/6: AI generating movie review & executive summary...")
                    review = analyzer.generate_review(segments, chapters)
                    summary = analyzer.generate_summary(segments)
                    st.session_state.current_review = review
                    st.session_state.current_summary = summary
                    insert_review(vid_id, review, notes, summary, 0.0)
                    pbar.progress(100)

                    st.session_state.pipeline_complete = True
                    status.success(
                        f"✅ Pipeline Complete! Movie: **{vname}** | "
                        f"Duration: **{_fmt(duration)}** | "
                        f"Chapters: **{len(chapters)}** | Video ID: **{vid_id}**"
                    )

    # ── OPTION 2: Search by Movie Name ──
    else:
        st.subheader("🔍 Search Movie by Name")
        st.caption("Type any movie name — AI will fetch details, generate chapters, review, and summary using Gemini.")

        movie_name_input = st.text_input(
            "Enter movie name:",
            placeholder="e.g. Inception, The Dark Knight, RRR, KGF Chapter 2..."
        )

        if st.button("🔍 Search & Analyze Movie", type="primary", use_container_width=True):
            if not movie_name_input.strip():
                st.error("Please enter a movie name!")
            elif not st.session_state.movie_analyzer.api_available:
                st.error("⚠️ Gemini API key is required for search-by-name. Add it to your `.env` file.")
            else:
                pbar = st.progress(0)
                status = st.empty()
                analyzer = st.session_state.movie_analyzer

                status.info(f"⏳ Step 1/5: Fetching details for **{movie_name_input}**...")
                pbar.progress(5)

                status.info(f"⏳ Step 2/5: AI generating story chapters...")
                pbar.progress(20)

                result = analyzer.search_movie_by_name(movie_name_input)
                pbar.progress(70)

                details = result["details"]
                chapters = result["chapters"]
                segments = result["segments"]
                duration = result["duration"]

                # Store in database
                status.info("⏳ Step 3/5: Storing in database...")
                title = details.get("title", movie_name_input)
                vid_id = insert_video(title, f"search://{movie_name_input}", duration)
                insert_transcripts(vid_id, segments)
                insert_chapters(vid_id, chapters)
                insert_review(vid_id, result["review"], result["notes"], result["summary"], details.get("rating_imdb", 0))
                pbar.progress(85)

                # Update session state
                st.session_state.current_video_id = vid_id
                st.session_state.movie_title = title
                st.session_state.movie_duration = duration
                st.session_state.current_segments = segments
                st.session_state.current_chapters = chapters
                st.session_state.current_notes = result["notes"]
                st.session_state.current_review = result["review"]
                st.session_state.current_summary = result["summary"]
                st.session_state.pipeline_complete = True
                pbar.progress(100)

                status.success(
                    f"✅ Analysis Complete! **{title}** ({details.get('year', '')}) | "
                    f"Director: **{details.get('director', 'N/A')}** | "
                    f"Runtime: **{details.get('duration_minutes', 120)} min** | "
                    f"Chapters: **{len(chapters)}**"
                )

                # Show movie info card
                st.markdown("---")
                st.subheader("🎬 Movie Details")
                d1, d2, d3, d4 = st.columns(4)
                d1.metric("🎬 Title", details.get("title", movie_name_input)[:20])
                d2.metric("📅 Year", details.get("year", "N/A"))
                d3.metric("⏱️ Runtime", f"{details.get('duration_minutes', 120)} min")
                d4.metric("⭐ IMDB", f"{details.get('rating_imdb', 'N/A')}/10")

                i1, i2 = st.columns(2)
                with i1:
                    st.markdown(f"**Director:** {details.get('director', 'N/A')}")
                    st.markdown(f"**Genre:** {details.get('genre', 'N/A')}")
                with i2:
                    st.markdown(f"**Cast:** {details.get('cast', 'N/A')}")
                    st.markdown(f"**Language:** {details.get('language', 'N/A')}")

                if details.get("plot_brief"):
                    st.info(f"📖 {details['plot_brief']}")

    # Show quick stats if pipeline has been run
    if st.session_state.pipeline_complete:
        st.markdown("---")
        st.subheader("📊 Processing Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Duration", _fmt(st.session_state.movie_duration))
        m2.metric("Transcript Segments", len(st.session_state.current_segments))
        m3.metric("Story Chapters", len(st.session_state.current_chapters))
        m4.metric("Video ID", st.session_state.current_video_id)



# ═══════════════════════════════════════════════════════════════
# TAB 2: FULL TRANSCRIPT
# ═══════════════════════════════════════════════════════════════
elif "2. Full Transcript" in nav:
    st.title("📜 Full Timestamped Transcript")

    if not st.session_state.current_segments:
        st.warning("⚠️ No movie processed yet. Go to **Tab 1** and run the pipeline first.")
    else:
        segments = st.session_state.current_segments
        st.success(f"**{st.session_state.movie_title}** — {len(segments)} segments | Duration: {_fmt(st.session_state.movie_duration)}")

        # Search functionality
        search_term = st.text_input("🔍 Search transcript:", placeholder="Type to search...")

        st.markdown("---")

        for i, seg in enumerate(segments, 1):
            text = seg["text"]

            # Filter by search
            if search_term and search_term.lower() not in text.lower():
                continue

            ts_start = _fmt(seg["start"])
            ts_end = _fmt(seg["end"])
            speaker = seg.get("speaker", "Speaker")

            with st.container():
                col_ts, col_text = st.columns([1, 5])
                with col_ts:
                    st.markdown(f"**`{ts_start}`**")
                    st.caption(f"→ `{ts_end}`")
                    st.caption(f"🎤 {speaker}")
                with col_text:
                    # Highlight search terms
                    if search_term:
                        highlighted = re.sub(
                            f"({re.escape(search_term)})",
                            r"**\1**",
                            text,
                            flags=re.IGNORECASE
                        )
                        st.markdown(highlighted)
                    else:
                        st.write(text)
                st.markdown("---")


# ═══════════════════════════════════════════════════════════════
# TAB 3: STORY CHAPTERS
# ═══════════════════════════════════════════════════════════════
elif "3. Story Chapters" in nav:
    st.title("📑 Story Chapters — Sequential Breakdown")

    if not st.session_state.current_chapters:
        # Try loading from database
        if st.session_state.current_video_id:
            db_chapters = get_chapters_for_video(st.session_state.current_video_id)
            if db_chapters:
                st.session_state.current_chapters = db_chapters

    if not st.session_state.current_chapters:
        st.warning("⚠️ No chapters generated yet. Go to **Tab 1** and run the pipeline first.")
    else:
        chapters = st.session_state.current_chapters
        st.success(
            f"**{st.session_state.movie_title}** — "
            f"**{len(chapters)} Chapters** | Duration: {_fmt(st.session_state.movie_duration)}"
        )

        st.markdown("---")

        for ch in chapters:
            ch_num = ch.get("chapter_num", 0)
            ch_title = ch.get("title", f"Chapter {ch_num}")
            start = ch.get("start_time", 0)
            end = ch.get("end_time", 0)
            ch_summary = ch.get("summary", "")
            characters = ch.get("characters", "")

            with st.expander(
                f"📖 Chapter {ch_num}: {ch_title}  —  [{_fmt(start)} → {_fmt(end)}]",
                expanded=(ch_num <= 3)
            ):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**Summary:**\n\n{ch_summary}")
                with c2:
                    st.markdown(f"**Timestamp:**\n`{_fmt(start)}` → `{_fmt(end)}`")
                    if characters:
                        st.markdown(f"**Characters:**\n{characters}")

        # Chapter timeline visualization
        st.markdown("---")
        st.subheader("📊 Chapter Timeline")

        timeline_data = []
        for ch in chapters:
            duration_min = (ch.get("end_time", 0) - ch.get("start_time", 0)) / 60
            timeline_data.append({
                "Chapter": f"Ch. {ch.get('chapter_num', 0)}",
                "Duration (minutes)": round(duration_min, 1)
            })

        if timeline_data:
            df = pd.DataFrame(timeline_data)
            st.bar_chart(df.set_index("Chapter"))


# ═══════════════════════════════════════════════════════════════
# TAB 4: NOTES & REVIEW
# ═══════════════════════════════════════════════════════════════
elif "4. Notes & Review" in nav:
    st.title("📝 Detailed Notes & Movie Review")

    if not st.session_state.current_notes and not st.session_state.current_review:
        # Try loading from database
        if st.session_state.current_video_id:
            db_review = get_review_for_video(st.session_state.current_video_id)
            if db_review:
                st.session_state.current_notes = db_review.get("notes_text", "")
                st.session_state.current_review = db_review.get("review_text", "")
                st.session_state.current_summary = db_review.get("summary_text", "")

    tab_notes, tab_review = st.tabs(["📝 Scene-by-Scene Notes", "🎬 Movie Review"])

    with tab_notes:
        if st.session_state.current_notes:
            st.markdown(st.session_state.current_notes)

            # Download notes as text
            st.download_button(
                "💾 Download Notes (.txt)",
                data=st.session_state.current_notes,
                file_name=f"{st.session_state.movie_title}_notes.txt",
                mime="text/plain"
            )
        else:
            st.warning("⚠️ No notes generated yet. Run the pipeline in **Tab 1** first.")

    with tab_review:
        if st.session_state.current_review:
            st.markdown(st.session_state.current_review)

            st.download_button(
                "💾 Download Review (.txt)",
                data=st.session_state.current_review,
                file_name=f"{st.session_state.movie_title}_review.txt",
                mime="text/plain"
            )
        else:
            st.warning("⚠️ No review generated yet. Run the pipeline in **Tab 1** first.")


# ═══════════════════════════════════════════════════════════════
# TAB 5: SUMMARY DASHBOARD
# ═══════════════════════════════════════════════════════════════
elif "5. Summary Dashboard" in nav:
    st.title("📊 Movie Summary Dashboard")

    if not st.session_state.pipeline_complete and st.session_state.current_video_id:
        db_review = get_review_for_video(st.session_state.current_video_id)
        if db_review:
            st.session_state.current_summary = db_review.get("summary_text", "")

    if not st.session_state.current_summary:
        st.warning("⚠️ No summary generated yet. Run the pipeline in **Tab 1** first.")
    else:
        # Quick stats row
        s1, s2, s3, s4 = st.columns(4)

        duration = st.session_state.movie_duration
        hrs = int(duration // 3600)
        mins = int((duration % 3600) // 60)

        s1.metric("🎬 Movie", re.sub(r'\.[^.]+$', '', st.session_state.movie_title).replace("_", " ")[:25])
        s2.metric("⏱️ Runtime", f"{hrs}h {mins}m")
        s3.metric("📑 Chapters", len(st.session_state.current_chapters))
        s4.metric("📜 Segments", len(st.session_state.current_segments))

        st.markdown("---")

        # Executive Summary
        st.subheader("📋 Executive Summary")
        st.markdown(st.session_state.current_summary)

        st.markdown("---")

        # Character/Speaker Analysis
        st.subheader("🎭 Speakers Identified")
        speakers = set()
        for seg in st.session_state.current_segments:
            speakers.add(seg.get("speaker", "Unknown"))

        speaker_counts = {}
        for seg in st.session_state.current_segments:
            sp = seg.get("speaker", "Unknown")
            speaker_counts[sp] = speaker_counts.get(sp, 0) + 1

        if speaker_counts:
            df_speakers = pd.DataFrame([
                {"Speaker": sp, "Segments": count}
                for sp, count in sorted(speaker_counts.items(), key=lambda x: -x[1])
            ])
            st.dataframe(df_speakers, use_container_width=True, hide_index=True)

        # Quick chapter overview
        st.markdown("---")
        st.subheader("📖 Chapter Overview")
        if st.session_state.current_chapters:
            ch_data = []
            for ch in st.session_state.current_chapters:
                ch_data.append({
                    "#": ch.get("chapter_num", 0),
                    "Title": ch.get("title", ""),
                    "Start": _fmt(ch.get("start_time", 0)),
                    "End": _fmt(ch.get("end_time", 0)),
                    "Characters": ch.get("characters", "")[:40]
                })
            st.dataframe(pd.DataFrame(ch_data), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# TAB 6: DOWNLOAD PDF REPORT
# ═══════════════════════════════════════════════════════════════
elif "6. Download PDF" in nav:
    st.title("📥 Download PDF Report")

    if not st.session_state.pipeline_complete:
        # Check if we can load from database
        if st.session_state.current_video_id:
            db_review = get_review_for_video(st.session_state.current_video_id)
            db_chapters = get_chapters_for_video(st.session_state.current_video_id)
            if db_review and db_chapters:
                st.session_state.current_chapters = db_chapters
                st.session_state.current_notes = db_review.get("notes_text", "")
                st.session_state.current_review = db_review.get("review_text", "")
                st.session_state.current_summary = db_review.get("summary_text", "")
                st.session_state.pipeline_complete = True

    if not st.session_state.pipeline_complete:
        st.warning("⚠️ No movie processed yet. Go to **Tab 1** and run the pipeline first.")
        st.info("Once you process a movie, you'll be able to download a complete PDF report with:\n"
                "- Executive Summary\n"
                "- Story Chapters with timestamps\n"
                "- Detailed Scene Notes\n"
                "- Movie Review & Analysis\n"
                "- Full Transcript")
    else:
        st.success(
            f"**{st.session_state.movie_title}** — Ready for PDF export! | "
            f"Duration: {_fmt(st.session_state.movie_duration)} | "
            f"Chapters: {len(st.session_state.current_chapters)}"
        )

        st.markdown("---")

        # Preview what the PDF will contain
        st.subheader("📄 PDF Report Preview")

        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown("**📋 Executive Summary**")
            preview_summary = st.session_state.current_summary[:200]
            st.caption(preview_summary + "..." if len(st.session_state.current_summary) > 200 else preview_summary)

        with p2:
            st.markdown(f"**📑 {len(st.session_state.current_chapters)} Story Chapters**")
            for ch in st.session_state.current_chapters[:3]:
                st.caption(f"Ch. {ch.get('chapter_num', 0)}: {ch.get('title', '')[:30]}")
            if len(st.session_state.current_chapters) > 3:
                st.caption(f"... and {len(st.session_state.current_chapters) - 3} more")

        with p3:
            st.markdown(f"**📜 {len(st.session_state.current_segments)} Transcript Segments**")
            st.caption(f"Full movie transcript with timestamps")

        st.markdown("---")

        # Generate PDF
        if st.button("📥 Generate & Download PDF Report", type="primary", use_container_width=True):
            with st.spinner("Generating professional PDF report..."):
                movie_data = {
                    "title": st.session_state.movie_title,
                    "duration": st.session_state.movie_duration,
                    "transcript_segments": st.session_state.current_segments,
                    "chapters": st.session_state.current_chapters,
                    "notes": st.session_state.current_notes,
                    "review": st.session_state.current_review,
                    "summary": st.session_state.current_summary
                }

                pdf_bytes = generate_movie_pdf(movie_data)

                clean_name = re.sub(r'\.[^.]+$', '', st.session_state.movie_title)
                clean_name = re.sub(r'[^\w\s-]', '', clean_name).strip().replace(" ", "_")

                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"CineDigest_{clean_name}_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

                st.success(f"✅ PDF generated! ({len(pdf_bytes) / 1024:.1f} KB)")

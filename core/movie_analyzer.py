import os
import re
import json
from typing import List, Dict, Any


class MovieAnalyzer:
    """
    AI-powered movie analysis engine using Google Gemini 2.5 Flash.
    Generates story chapters, detailed notes, reviews, and summaries from movie transcripts.
    """

    def __init__(self):
        self.api_available = False
        self.model = None
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel("gemini-2.5-flash")
                self.api_available = True
            except Exception:
                pass

    def _format_time(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _build_timestamped_transcript(self, segments: List[Dict[str, Any]]) -> str:
        """Build a transcript string with timestamps for AI prompts."""
        lines = []
        for seg in segments:
            ts = f"[{self._format_time(seg['start'])} - {self._format_time(seg['end'])}]"
            speaker = seg.get("speaker", "Speaker")
            lines.append(f"{ts} {speaker}: {seg['text']}")
        return "\n".join(lines)

    def _call_gemini(self, prompt: str) -> str:
        """Send prompt to Gemini and return text response."""
        if not self.api_available or not self.model:
            return ""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception:
            return ""

    # ─────────────────────────────────────────────────────────
    # CHAPTER GENERATION
    # ─────────────────────────────────────────────────────────
    def generate_chapters(self, transcript_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Break a movie transcript into 10-15 sequential story chapters.
        Each chapter has: chapter_num, title, start_time, end_time, summary, characters.
        """
        transcript_text = self._build_timestamped_transcript(transcript_segments)
        total_duration = transcript_segments[-1]["end"] if transcript_segments else 0

        prompt = (
            "You are a professional movie analyst. Below is a complete timestamped transcript of a movie.\n\n"
            f"TRANSCRIPT:\n{transcript_text}\n\n"
            "TASK: Break this movie into 10 to 15 sequential story chapters that follow the narrative arc.\n"
            "Each chapter should cover a distinct part of the story (introduction, rising action, climax, resolution, etc.).\n\n"
            "Output ONLY a valid JSON array. Each object must have these exact keys:\n"
            '- "chapter_num" (integer, starting from 1)\n'
            '- "title" (string, a creative chapter title)\n'
            '- "start_time" (float, seconds from start of movie)\n'
            '- "end_time" (float, seconds from start of movie)\n'
            '- "summary" (string, 2-4 sentences describing what happens in this chapter)\n'
            '- "characters" (string, comma-separated list of characters involved)\n\n'
            "Ensure chapters are in chronological order and cover the entire movie duration.\n"
            'Example: [{"chapter_num": 1, "title": "The Beginning", "start_time": 0.0, "end_time": 900.0, '
            '"summary": "The story opens...", "characters": "John, Mary"}]'
        )

        response_text = self._call_gemini(prompt)

        if response_text:
            match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return parsed
                except json.JSONDecodeError:
                    pass

        # Offline fallback: split into equal time-based chapters
        return self._fallback_chapters(transcript_segments, total_duration)

    def _fallback_chapters(self, segments: List[Dict[str, Any]], total_duration: float) -> List[Dict[str, Any]]:
        """Generate basic chapters by splitting transcript into equal time windows."""
        num_chapters = min(max(len(segments) // 2, 5), 12)
        chapter_duration = total_duration / num_chapters if total_duration > 0 else 300.0
        chapters = []

        chapter_titles = [
            "The Opening", "Setting the Stage", "First Encounters",
            "Rising Tensions", "Turning Point", "Deepening Conflict",
            "Midpoint Revelation", "Escalation", "The Dark Hour",
            "Building to Climax", "The Climax", "Resolution & Aftermath"
        ]

        for i in range(num_chapters):
            start = i * chapter_duration
            end = min((i + 1) * chapter_duration, total_duration)

            # Gather segments that fall within this chapter's time range
            chapter_texts = []
            chapter_speakers = set()
            for seg in segments:
                if seg["start"] >= start and seg["start"] < end:
                    chapter_texts.append(seg["text"])
                    chapter_speakers.add(seg.get("speaker", "Unknown"))

            summary = " ".join(chapter_texts[:2]) if chapter_texts else f"Chapter {i+1} of the movie."
            if len(summary) > 300:
                summary = summary[:297] + "..."

            chapters.append({
                "chapter_num": i + 1,
                "title": chapter_titles[i % len(chapter_titles)],
                "start_time": round(start, 1),
                "end_time": round(end, 1),
                "summary": summary,
                "characters": ", ".join(list(chapter_speakers)[:4]) or "Main Cast"
            })

        return chapters

    # ─────────────────────────────────────────────────────────
    # NOTES GENERATION
    # ─────────────────────────────────────────────────────────
    def generate_notes(self, transcript_segments: List[Dict[str, Any]]) -> str:
        """Generate comprehensive topic-by-topic notes covering every scene."""
        transcript_text = self._build_timestamped_transcript(transcript_segments)

        prompt = (
            "You are a professional movie analyst. Below is a complete timestamped transcript of a movie.\n\n"
            f"TRANSCRIPT:\n{transcript_text}\n\n"
            "TASK: Generate comprehensive, detailed notes covering EVERY important scene and topic in this movie.\n"
            "Format the notes in Markdown with:\n"
            "- Main section headings (##) for major story arcs\n"
            "- Sub-sections (###) for individual scenes\n"
            "- Timestamps in [HH:MM:SS] format for each scene\n"
            "- Bullet points for key details, dialogue highlights, and character actions\n"
            "- Bold text for important plot points and character names\n\n"
            "Cover everything: settings, character development, plot twists, dialogue themes, visual motifs."
        )

        response_text = self._call_gemini(prompt)
        if response_text and len(response_text) > 100:
            return response_text

        # Offline fallback
        return self._fallback_notes(transcript_segments)

    def _fallback_notes(self, segments: List[Dict[str, Any]]) -> str:
        """Generate basic notes from transcript segments."""
        notes = "# 📝 Movie Scene-by-Scene Notes\n\n"
        notes += "---\n\n"

        for i, seg in enumerate(segments, 1):
            ts = self._format_time(seg["start"])
            notes += f"### Scene {i} — [{ts}]\n"
            notes += f"**Speaker:** {seg.get('speaker', 'Unknown')}\n\n"
            notes += f"{seg['text']}\n\n"
            notes += "---\n\n"

        return notes

    # ─────────────────────────────────────────────────────────
    # MOVIE REVIEW
    # ─────────────────────────────────────────────────────────
    def generate_review(self, transcript_segments: List[Dict[str, Any]], chapters: List[Dict[str, Any]]) -> str:
        """Generate a professional movie review with plot synopsis, analysis, and rating."""
        transcript_text = self._build_timestamped_transcript(transcript_segments)

        chapters_text = ""
        for ch in chapters:
            chapters_text += f"Chapter {ch['chapter_num']}: {ch['title']} ({self._format_time(ch['start_time'])} - {self._format_time(ch['end_time'])})\n"
            chapters_text += f"  Summary: {ch['summary']}\n\n"

        prompt = (
            "You are a professional film critic. Below is a movie transcript and its chapter breakdown.\n\n"
            f"TRANSCRIPT:\n{transcript_text}\n\n"
            f"CHAPTERS:\n{chapters_text}\n\n"
            "TASK: Write a comprehensive, professional movie review in Markdown format with these sections:\n"
            "1. ## 🎬 Plot Synopsis (4-6 paragraphs covering the full story without spoiler warnings)\n"
            "2. ## 👥 Character Analysis (analyze each major character's arc and development)\n"
            "3. ## 🎭 Themes & Motifs (identify and discuss the major themes)\n"
            "4. ## ⏱️ Pacing & Structure (evaluate the movie's pacing and narrative structure)\n"
            "5. ## ⭐ Rating & Recommendation (give a rating out of 10 with justification)\n\n"
            "Write in an engaging, analytical tone suitable for busy professionals who want to understand the movie."
        )

        response_text = self._call_gemini(prompt)
        if response_text and len(response_text) > 100:
            return response_text

        return self._fallback_review(transcript_segments, chapters)

    def _fallback_review(self, segments: List[Dict[str, Any]], chapters: List[Dict[str, Any]]) -> str:
        """Generate a structural review from available data."""
        total_duration = segments[-1]["end"] if segments else 0
        hrs = int(total_duration // 3600)
        mins = int((total_duration % 3600) // 60)

        speakers = set()
        for seg in segments:
            speakers.add(seg.get("speaker", "Unknown"))

        review = "# 🎬 Movie Review\n\n"
        review += "---\n\n"
        review += "## 🎬 Plot Synopsis\n\n"

        for ch in chapters[:5]:
            review += f"**{ch['title']}** ({self._format_time(ch['start_time'])} - {self._format_time(ch['end_time'])}): "
            review += f"{ch['summary']}\n\n"

        review += "## 👥 Character Analysis\n\n"
        review += "The following voices/characters were identified in the movie:\n\n"
        for sp in speakers:
            review += f"- **{sp}**: Plays a significant role throughout the narrative.\n"

        review += f"\n## ⏱️ Pacing & Structure\n\n"
        review += f"The movie runs for **{hrs}h {mins}m** and is divided into **{len(chapters)} chapters**.\n\n"

        review += "## ⭐ Rating & Recommendation\n\n"
        review += "**Rating: 7.5 / 10**\n\n"
        review += "This movie offers an engaging narrative experience. Recommended for viewers interested in this genre.\n"

        return review

    # ─────────────────────────────────────────────────────────
    # EXECUTIVE SUMMARY
    # ─────────────────────────────────────────────────────────
    def generate_summary(self, transcript_segments: List[Dict[str, Any]]) -> str:
        """Generate a concise executive summary (300-500 words) of the entire movie."""
        transcript_text = self._build_timestamped_transcript(transcript_segments)

        prompt = (
            "You are a professional movie summarizer for busy professionals.\n\n"
            f"TRANSCRIPT:\n{transcript_text}\n\n"
            "TASK: Write a concise executive summary (300-500 words) of this entire movie.\n"
            "The summary should:\n"
            "- Cover the complete story arc from beginning to end\n"
            "- Mention all major characters and their roles\n"
            "- Highlight key plot twists and turning points\n"
            "- Be written in an engaging, narrative style\n"
            "- Be formatted in Markdown with a title and clean paragraphs\n\n"
            "Target audience: busy people who don't have time to watch the full movie but want to understand the complete story."
        )

        response_text = self._call_gemini(prompt)
        if response_text and len(response_text) > 100:
            return response_text

        return self._fallback_summary(transcript_segments)

    def _fallback_summary(self, segments: List[Dict[str, Any]]) -> str:
        """Generate a basic summary by combining segment highlights."""
        total_duration = segments[-1]["end"] if segments else 0
        hrs = int(total_duration // 3600)
        mins = int((total_duration % 3600) // 60)

        summary = "# 📋 Executive Movie Summary\n\n"
        summary += f"**Runtime:** {hrs}h {mins}m | **Scenes Analyzed:** {len(segments)}\n\n"
        summary += "---\n\n"

        # Take representative text from beginning, middle, and end
        key_indices = [0, len(segments) // 4, len(segments) // 2, 3 * len(segments) // 4, len(segments) - 1]
        seen = set()

        for idx in key_indices:
            if 0 <= idx < len(segments) and idx not in seen:
                seen.add(idx)
                seg = segments[idx]
                ts = self._format_time(seg["start"])
                summary += f"**[{ts}]** {seg['text']}\n\n"

        summary += "---\n\n"
        summary += "*This summary was generated from the movie transcript to help busy viewers understand the complete story.*\n"

        return summary

    # ─────────────────────────────────────────────────────────
    # SEARCH BY MOVIE NAME (No video file needed)
    # ─────────────────────────────────────────────────────────
    def search_movie_by_name(self, movie_name: str) -> Dict[str, Any]:
        """
        Search for a movie by name and generate full analysis using Gemini's knowledge.
        Returns dict with: title, year, genre, director, cast, duration, 
                          chapters, notes, review, summary, segments
        """
        # Step 1: Fetch movie details
        details = self._fetch_movie_details(movie_name)

        # Step 2: Generate chapters
        chapters = self._generate_chapters_from_name(movie_name, details)

        # Step 3: Generate notes
        notes = self._generate_notes_from_name(movie_name, details)

        # Step 4: Generate review
        review = self._generate_review_from_name(movie_name, details, chapters)

        # Step 5: Generate summary
        summary = self._generate_summary_from_name(movie_name, details)

        # Build pseudo-segments from chapters (for transcript tab and PDF)
        segments = []
        for ch in chapters:
            segments.append({
                "start": ch.get("start_time", 0.0),
                "end": ch.get("end_time", 0.0),
                "speaker": "Narrator",
                "text": f"[{ch.get('title', '')}] {ch.get('summary', '')}"
            })

        return {
            "details": details,
            "chapters": chapters,
            "notes": notes,
            "review": review,
            "summary": summary,
            "segments": segments,
            "duration": details.get("duration_seconds", 7200.0)
        }

    def _fetch_movie_details(self, movie_name: str) -> Dict[str, Any]:
        """Use Gemini to fetch movie metadata."""
        prompt = (
            f"Provide detailed information about the movie: \"{movie_name}\"\n\n"
            "Output ONLY a valid JSON object with these keys:\n"
            '- "title" (string, official title)\n'
            '- "year" (integer, release year)\n'
            '- "genre" (string, comma-separated genres)\n'
            '- "director" (string)\n'
            '- "cast" (string, top 5 cast members comma-separated)\n'
            '- "language" (string)\n'
            '- "duration_minutes" (integer, runtime in minutes)\n'
            '- "duration_seconds" (float, runtime in seconds)\n'
            '- "plot_brief" (string, 2-sentence plot overview)\n'
            '- "rating_imdb" (float, IMDB rating out of 10)\n\n'
            "If you don't know the exact details, provide your best estimate."
        )

        response_text = self._call_gemini(prompt)

        if response_text:
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    details = json.loads(match.group(0))
                    return details
                except json.JSONDecodeError:
                    pass

        # Fallback
        return {
            "title": movie_name,
            "year": 2024,
            "genre": "Drama",
            "director": "Unknown",
            "cast": "Unknown",
            "language": "English",
            "duration_minutes": 120,
            "duration_seconds": 7200.0,
            "plot_brief": f"A compelling film titled {movie_name}.",
            "rating_imdb": 7.0
        }

    def _generate_chapters_from_name(self, movie_name: str, details: Dict) -> List[Dict[str, Any]]:
        """Generate story chapters from movie name using Gemini's knowledge."""
        duration = details.get("duration_seconds", 7200.0)
        prompt = (
            f"You are a film analyst. For the movie \"{movie_name}\" "
            f"({details.get('year', '')}, directed by {details.get('director', 'unknown')}), "
            f"the movie has a runtime of approximately {details.get('duration_minutes', 120)} minutes.\n\n"
            "TASK: Break this movie's story into 10-15 sequential chapters that follow the narrative arc.\n\n"
            "Output ONLY a valid JSON array. Each object must have:\n"
            '- "chapter_num" (integer, starting from 1)\n'
            '- "title" (string, creative chapter title)\n'
            '- "start_time" (float, approximate seconds from start)\n'
            '- "end_time" (float, approximate seconds from start)\n'
            '- "summary" (string, 2-4 sentences about what happens)\n'
            '- "characters" (string, comma-separated characters involved)\n\n'
            f"Ensure chapters span the full {details.get('duration_minutes', 120)} minute runtime."
        )

        response_text = self._call_gemini(prompt)
        if response_text:
            match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return parsed
                except json.JSONDecodeError:
                    pass

        # Fallback: equal-length chapters
        num_ch = 10
        ch_len = duration / num_ch
        return [
            {
                "chapter_num": i + 1,
                "title": f"Part {i + 1}",
                "start_time": round(i * ch_len, 1),
                "end_time": round((i + 1) * ch_len, 1),
                "summary": f"Part {i + 1} of {movie_name}.",
                "characters": details.get("cast", "Main Cast")
            }
            for i in range(num_ch)
        ]

    def _generate_notes_from_name(self, movie_name: str, details: Dict) -> str:
        """Generate detailed scene notes from movie name."""
        prompt = (
            f"You are a film analyst. For the movie \"{movie_name}\" "
            f"({details.get('year', '')}, directed by {details.get('director', 'unknown')}), "
            f"starring {details.get('cast', 'unknown')}.\n\n"
            "TASK: Write comprehensive scene-by-scene notes covering EVERY important scene.\n"
            "Format in Markdown with:\n"
            "- ## headings for major story arcs\n"
            "- ### sub-headings for individual scenes\n"
            "- Approximate timestamps [HH:MM:SS]\n"
            "- Bullet points for key events, dialogue, character actions\n"
            "- Bold text for important plot points and character names\n\n"
            "Cover everything: settings, character arcs, plot twists, emotional beats, climax, resolution."
        )

        response_text = self._call_gemini(prompt)
        if response_text and len(response_text) > 100:
            return response_text

        return f"# Scene Notes — {movie_name}\n\nDetailed notes could not be generated. Please ensure the Gemini API key is configured."

    def _generate_review_from_name(self, movie_name: str, details: Dict, chapters: List) -> str:
        """Generate professional movie review from name."""
        prompt = (
            f"You are a professional film critic. Write a comprehensive review of \"{movie_name}\" "
            f"({details.get('year', '')}, directed by {details.get('director', 'unknown')}), "
            f"starring {details.get('cast', 'unknown')}. Genre: {details.get('genre', 'unknown')}.\n\n"
            "Write in Markdown with these sections:\n"
            "1. ## 🎬 Plot Synopsis (4-6 paragraphs, complete story)\n"
            "2. ## 👥 Character Analysis (each major character's arc)\n"
            "3. ## 🎭 Themes & Motifs (major themes explored)\n"
            "4. ## ⏱️ Pacing & Structure (narrative structure evaluation)\n"
            "5. ## ⭐ Rating & Recommendation (rating out of 10 with justification)\n\n"
            "Write for busy professionals who want to understand the movie without watching it."
        )

        response_text = self._call_gemini(prompt)
        if response_text and len(response_text) > 100:
            return response_text

        return (
            f"# Movie Review — {movie_name}\n\n"
            f"**Director:** {details.get('director', 'N/A')} | "
            f"**Year:** {details.get('year', 'N/A')} | "
            f"**Genre:** {details.get('genre', 'N/A')}\n\n"
            f"{details.get('plot_brief', '')}\n\n"
            f"**Rating:** {details.get('rating_imdb', 'N/A')}/10"
        )

    def _generate_summary_from_name(self, movie_name: str, details: Dict) -> str:
        """Generate executive summary from movie name."""
        prompt = (
            f"Write a concise executive summary (300-500 words) of the movie \"{movie_name}\" "
            f"({details.get('year', '')}, directed by {details.get('director', 'unknown')}).\n\n"
            "Cover the complete story arc, major characters, key turning points.\n"
            "Target audience: busy people who want to understand the story quickly.\n"
            "Format in Markdown with a title and clean paragraphs."
        )

        response_text = self._call_gemini(prompt)
        if response_text and len(response_text) > 100:
            return response_text

        return (
            f"# Executive Summary — {movie_name}\n\n"
            f"{details.get('plot_brief', 'Summary not available.')}\n"
        )

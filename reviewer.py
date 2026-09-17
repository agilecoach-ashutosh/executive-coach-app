"""Post-session metrics and developmental review for Coach Practice mode.

This module deliberately reviews only the visible transcript. It does not receive
hidden simulated-coachee context. Results are developmental guidance, not an ICF
credential decision, official score, pass/fail result, or assessor substitute.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from google import genai


REVIEW_MODEL = "gemini-3.8-flash"
FALLBACK_REVIEW_MODEL = "gemini-2.5-flash"


@dataclass
class SessionMetrics:
    duration_seconds: int
    coach_turns: int
    coachee_turns: int
    coach_words: int
    coachee_words: int
    coach_share_pct: int
    coachee_share_pct: int
    coach_questions: int
    stacked_question_turns: int
    average_coach_words: float
    longest_coach_turn_words: int
    interruptions: int


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w’'-]+\b", text or "", flags=re.UNICODE)


def _question_count(text: str) -> int:
    """Count explicit transcript questions conservatively.

    Provider punctuation is imperfect, so this remains a transcript heuristic rather
    than a semantic claim about the coach's intention.
    """
    return (text or "").count("?")


def calculate_metrics(rows: Iterable[tuple[str, str, str]], duration_seconds: float) -> SessionMetrics:
    rows = list(rows)
    coach_rows = [text for _, role, text in rows if role == "Coach"]
    coachee_rows = [text for _, role, text in rows if role == "Coachee"]

    coach_word_counts = [len(_words(text)) for text in coach_rows]
    coachee_word_counts = [len(_words(text)) for text in coachee_rows]
    coach_words = sum(coach_word_counts)
    coachee_words = sum(coachee_word_counts)
    total_words = coach_words + coachee_words

    if total_words:
        coach_share = round(coach_words * 100 / total_words)
    else:
        coach_share = 0
    coachee_share = 100 - coach_share if total_words else 0

    questions_per_turn = [_question_count(text) for text in coach_rows]
    interruptions = sum(
        1
        for _, role, text in rows
        if role == "Session note" and "interrupt" in (text or "").lower()
    )

    return SessionMetrics(
        duration_seconds=max(0, round(duration_seconds)),
        coach_turns=len(coach_rows),
        coachee_turns=len(coachee_rows),
        coach_words=coach_words,
        coachee_words=coachee_words,
        coach_share_pct=coach_share,
        coachee_share_pct=coachee_share,
        coach_questions=sum(questions_per_turn),
        stacked_question_turns=sum(1 for count in questions_per_turn if count > 1),
        average_coach_words=(coach_words / len(coach_rows)) if coach_rows else 0.0,
        longest_coach_turn_words=max(coach_word_counts, default=0),
        interruptions=interruptions,
    )


def format_duration(seconds: int) -> str:
    minutes, secs = divmod(max(0, int(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def transcript_for_review(rows: Iterable[tuple[str, str, str]]) -> str:
    parts = []
    for stamp, role, text in rows:
        if role not in ("Coach", "Coachee", "Session note"):
            continue
        parts.append(f"[{stamp}] {role}: {(text or '').strip()}")
    return "\n\n".join(parts)


def build_review_prompt(level: str, rows, metrics: SessionMetrics, scenario=None) -> str:
    level = (level or "PCC").upper()
    if level not in {"ACC", "PCC", "MCC"}:
        level = "PCC"

    scenario_text = "Practice workplace scenario"
    if scenario:
        scenario_text = (
            f"{scenario.get('title', 'Practice scenario')} — "
            f"{scenario.get('environment', '')}. Visible presenting topic: "
            f"{scenario.get('visible_problem', '')}"
        )

    transcript = transcript_for_review(rows)
    return f"""You are reviewing a simulated professional coaching practice transcript.
The human user is the COACH. The other speaker is a simulated COACHEE.

PURPOSE
Give rigorous developmental feedback against the current ICF coaching framework at
{level} practice level. Use the 2025 ICF Core Competencies and the updated Minimum
Skills Requirements in effect from January 1, 2026 as the conceptual reference.
This is NOT an official ICF assessment. Do not declare pass/fail, credential readiness,
or an official score. Do not claim to be an ICF assessor.

EVIDENCE BOUNDARY
Evaluate only what is observable in the transcript below. Do NOT infer body language,
intent, tone, hidden client context, or events not captured in the transcript. The
simulated client's private persona is deliberately not provided. Speech transcription
and punctuation may contain errors. If evidence is insufficient, explicitly say so.

LEVEL LENS
ACC: look for reliable foundational client-centered coaching, clear agreement,
listening, relevant questions/reflections, client ownership, and avoidance of advice.
PCC: look for consistent partnership, individualized listening, trust/safety,
presence, concise observations/questions, evoking the client's own awareness, and
client-led learning/action without steering.
MCC: look for seamless, nuanced, highly responsive partnership; spacious presence;
deep listening to the whole person and context; elegant use of the client's language;
and awareness/growth emerging primarily from the client's own thinking. Do not expect
MCC theatrics, excessive depth, or forced transformation.

CORE AREAS TO REVIEW
1. Establishes and Maintains Agreements
2. Cultivates Trust and Safety
3. Maintains Presence
4. Listens Actively
5. Evokes Awareness
6. Facilitates Client Growth
Also note any observable ethical/role-boundary concern. A transcript alone cannot
fully evidence every aspect of coaching mindset or ethics.

LOCAL SESSION METRICS (descriptive, not ICF scoring)
Duration: {format_duration(metrics.duration_seconds)}
Coach / coachee word share estimate: {metrics.coach_share_pct}% / {metrics.coachee_share_pct}%
Coach turns: {metrics.coach_turns}
Coach questions marked by transcript punctuation: {metrics.coach_questions}
Coach turns containing multiple question marks: {metrics.stacked_question_turns}
Average coach turn length: {metrics.average_coach_words:.1f} words
Longest coach turn: {metrics.longest_coach_turn_words} words
Recorded interruption notes: {metrics.interruptions}

SCENARIO VISIBLE TO THE COACH
{scenario_text}

OUTPUT FORMAT
Use these exact section headings:

DEVELOPMENTAL REVIEW — {level}

WHAT THE COACH DID WELL
Give 3-5 evidence-based observations. Include timestamp references when possible.
Do not praise vaguely.

COMPETENCY REVIEW
For each of the six core areas above, use:
Area name — Evidence strength: Strong / Developing / Limited evidence
Observed evidence: ...
Development opportunity: ...
Use transcript timestamps and short excerpts where they materially help.

PATTERNS TO WATCH
Identify up to 4 recurring patterns such as leading, stacked questions, long coach
turns, premature action, missed client language, advice, over-reflection, or weak
agreement. Mention only patterns actually supported by the transcript.

THREE HIGH-LEVERAGE PRACTICE EDGES
Give exactly three specific changes the coach could practice next time. Make each
one behaviorally observable, not generic.

MOMENTS WORTH REVISITING
Choose up to 3 coach turns. For each, show the timestamp, what happened, and one
alternative coaching move that preserves client ownership. Alternatives are examples,
not 'correct answers'.

BOTTOM LINE
Write 3-5 sentences describing the developmental picture at {level} without a score,
rank, pass/fail statement, or credential-readiness verdict. End with: "Developmental
AI review only — not an official ICF assessment."

TRANSCRIPT
{transcript}
"""


def generate_review(api_key: str, level: str, rows, metrics: SessionMetrics, scenario=None) -> str:
    prompt = build_review_prompt(level, rows, metrics, scenario)
    client = genai.Client(api_key=api_key)
    last_error = None
    try:
        for model in (REVIEW_MODEL, FALLBACK_REVIEW_MODEL):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                text = (getattr(response, "text", None) or "").strip()
                if text:
                    return text
            except Exception as exc:  # provider errors vary by SDK version/account
                last_error = exc
        if last_error:
            raise last_error
        raise RuntimeError("The review model returned no text.")
    finally:
        try:
            client.close()
        except Exception:
            pass

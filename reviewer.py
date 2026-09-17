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

from review_criteria import get_review_criteria


# Keep review models on current stable Gemini text models that are broadly available,
# including free-tier access where Google currently offers it. Avoid retired 2.5 IDs.
REVIEW_MODELS = (
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
)


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

    source_name, criteria = get_review_criteria(level)

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
Give rigorous developmental feedback at the {level} practice level using the exact
level-specific evidence framework supplied below. The assessment basis for this review is:
{source_name}

This is NOT an official ICF assessment. Do not declare pass/fail, credential readiness,
or an official score. Do not claim to be an ICF assessor. The framework is a developmental
reference, not a formulaic checklist.

EVIDENCE BOUNDARY
Evaluate only what is observable in the transcript and local metrics below. Do NOT infer
body language, tone, energy, intent, hidden client context, or events not captured in the
transcript. The simulated client's private persona is deliberately not provided. Speech
transcription and punctuation may contain errors. If a criterion depends on audio,
nonverbal behavior, silence quality, energy shift, or context that is unavailable, label
it NOT ASSESSABLE or LIMITED EVIDENCE rather than inventing evidence.

LEVEL-SPECIFIC REVIEW FRAMEWORK
{criteria}

HOW TO APPLY THE FRAMEWORK
- Review the whole coaching conversation first, then examine individual behavioral statements.
- Do not treat absence of a behavior as failure when there was no reasonable opportunity to demonstrate it.
- Distinguish NOT OBSERVED from NO OPPORTUNITY and NOT ASSESSABLE.
- Use the client's actual words and timestamps whenever evidence is available.
- Consider patterns across the session, not isolated coach sentences only.
- Do not reward performative depth, excessive questioning, forced action, or generic empathy.
- Do not infer that a behavior was demonstrated merely because the coach asked a question about it.
- When a behavior is only partially evidenced, explain exactly what was present and what was missing.
- Ethical/role concerns should be reported only when observable in the transcript.

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
ASSESSMENT BASIS: {source_name}

WHAT THE COACH DID WELL
Give 3-5 evidence-based observations with competency/behavior references and timestamps where possible.
Do not praise vaguely.

MARKER / BEHAVIORAL EVIDENCE
Review every current MSR behavioral statement in the selected framework that can reasonably
be evaluated from this session. For each item use this compact format:
[Competency + short behavior name] — OBSERVED / PARTIAL EVIDENCE / NOT OBSERVED / NO OPPORTUNITY / NOT ASSESSABLE
Evidence: timestamp(s) and a concise explanation.
Development note: only when useful.

Use the current MSR behavior descriptions supplied above. Do not invent or reintroduce
legacy ACC/PCC marker numbers unless an identifier is explicitly present in the current framework.

COMPETENCY SYNTHESIS
For Competencies 1 and 3-8, summarize the pattern of evidence using:
Competency name — Evidence strength: Strong / Developing / Limited evidence / Not assessable
Observed evidence: ...
Development opportunity: ...
For Competency 2, follow the selected framework's limitation on what one session can evidence.

PATTERNS TO WATCH
Identify up to 4 recurring patterns actually supported by the transcript, such as leading,
stacked questions, long coach turns, premature action, missed client language, advice,
over-reflection, weak agreement, or coach-controlled closure.

THREE HIGH-LEVERAGE PRACTICE EDGES
Give exactly three behaviorally observable changes the coach could practice next time.
Link each practice edge to one or more specific current MSR behavioral statements.

MOMENTS WORTH REVISITING
Choose up to 3 coach turns. For each, show timestamp, what happened, relevant MSR behavior,
and one alternative coaching move that preserves client ownership. Alternatives are examples,
not 'correct answers'.

BOTTOM LINE
Write 3-5 sentences describing the developmental picture at {level} without a score, rank,
pass/fail statement, or credential-readiness verdict. End with: "Developmental AI review only — not an official ICF assessment."

TRANSCRIPT
{transcript}
"""


def generate_review(api_key: str, level: str, rows, metrics: SessionMetrics, scenario=None) -> str:
    prompt = build_review_prompt(level, rows, metrics, scenario)
    client = genai.Client(api_key=api_key)
    errors = []
    try:
        for model in REVIEW_MODELS:
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                text = (getattr(response, "text", None) or "").strip()
                if text:
                    return text
                errors.append(f"{model}: returned no text")
            except Exception as exc:  # provider errors vary by SDK version/account
                errors.append(f"{model}: {exc}")

        detail = "\n\n".join(errors[-3:]) if errors else "No model returned text."
        raise RuntimeError(
            "Gemini coaching review could not be generated with the current stable review models.\n\n"
            + detail
        )
    finally:
        try:
            client.close()
        except Exception:
            pass

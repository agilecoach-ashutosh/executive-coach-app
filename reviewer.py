"""Post-session metrics and developmental review for Coach Practice mode.

The reviewer sees only the visible transcript, descriptive local metrics, and the
selected developmental framework. It never receives hidden simulated-coachee context.
Results are developmental guidance, not an official ICF assessment or credential decision.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable

from google import genai

from review_criteria import get_review_criteria


REVIEW_MODELS = (
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
)

FAST_GROQ_REVIEW_MODEL = "openai/gpt-oss-20b"


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

    coach_share = round(coach_words * 100 / total_words) if total_words else 0
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


def _review_json_contract(level: str) -> str:
    acc_rule = ""
    if level == "ACC":
        acc_rule = """
ACC REQUIREMENT:
- behaviors must contain EXACTLY these 20 references once each:
  A3.1, A3.2, A3.3, A3.4,
  A4.1, A4.2, A4.3,
  A5.1, A5.2, A5.3, A5.4,
  A6.1, A6.2, A6.3,
  A7.1, A7.2, A7.3,
  A8.1, A8.2, A8.3
- rating for each must be exactly one of:
  EXCEEDS THE STANDARD, MEETS THE STANDARD, BELOW THE STANDARD,
  DOES NOT MEET STANDARD, N/A
- competency_1.ethics and competency_1.coaching_role must each be OBSERVED or NOT OBSERVED.
- competency_2.status must be NOT_RATED_SINGLE_SESSION.
"""

    return f"""
Return ONE valid JSON object only. Do not use Markdown fences and do not add prose before or after it.
Keep evidence concise because Presence builds the final report locally.

{{
  "level": "{level}",
  "assessment_basis": "short source label",
  "competency_1": {{
    "ethics": "status",
    "coaching_role": "status",
    "evidence": "brief session-wide evidence"
  }},
  "competency_2": {{
    "status": "status",
    "note": "brief note"
  }},
  "behaviors": [
    {{
      "reference": "A3.1 or concise competency/behavior reference",
      "name": "short behavior name",
      "rating": "allowed rating/status",
      "timestamps": ["00:00:34"],
      "evidence": "max 28 words",
      "development": "max 22 words; blank when unnecessary"
    }}
  ],
  "competency_synthesis": [
    {{
      "competency": "Competency 3 - Establishes and Maintains Agreements",
      "strength": "Strong / Developing / Limited evidence / Not assessable",
      "evidence": "max 35 words",
      "development": "max 25 words"
    }}
  ],
  "strengths": [
    {{
      "reference": "behavior/competency reference",
      "timestamps": ["00:00:34"],
      "text": "max 30 words"
    }}
  ],
  "development_areas": [
    {{
      "reference": "behavior/competency reference",
      "timestamps": ["00:02:10"],
      "text": "max 30 words"
    }}
  ],
  "patterns": ["max 4 concise items"],
  "practice_edges": [
    {{
      "reference": "behavior reference",
      "text": "specific observable practice change"
    }}
  ],
  "moments": [
    {{
      "timestamp": "00:04:18",
      "reference": "behavior reference",
      "what_happened": "brief description",
      "alternative": "one client-owned alternative move"
    }}
  ],
  "bottom_line": "3-5 concise sentences, max 90 words"
}}

Rules:
- strengths: 2-4 items.
- development_areas: 2-4 items when evidence supports them.
- patterns: at most 4.
- practice_edges: exactly 3.
- moments: at most 3.
- timestamps must exactly match transcript timestamps. Use [] when no exact timestamp supports an absence-based finding.
- Do not invent tone, body language, energy, silence quality, or hidden context.
- Do not quote long passages; describe the evidence concisely.
- Do not repeat the same evidence in multiple fields unless needed for a different purpose.
{acc_rule}
"""


def build_review_prompt(level: str, rows, metrics: SessionMetrics, scenario=None) -> str:
    level = (level or "PCC").upper()
    if level not in {"ACC", "PCC", "MCC"}:
        level = "PCC"

    source_name, criteria = get_review_criteria(level)
    scenario_text = "Practice workplace scenario"
    if scenario:
        scenario_text = (
            f"{scenario.get('title', 'Practice scenario')} - "
            f"{scenario.get('environment', '')}. Visible presenting topic: "
            f"{scenario.get('visible_problem', '')}"
        )

    transcript = transcript_for_review(rows)
    contract = _review_json_contract(level)

    return f"""You are reviewing a simulated professional coaching practice transcript.
The human user is the COACH. The other speaker is a simulated COACHEE.

PURPOSE
Produce rigorous developmental feedback at the {level} practice level using the framework below.
This is not an official ICF assessment, score, pass/fail result, or credential-readiness decision.

EVIDENCE BOUNDARY
Use only the visible transcript and descriptive local metrics. Do not infer unavailable audio,
nonverbal, emotional, or hidden-context evidence. Treat transcript punctuation as imperfect.
When a behavior is absent, say what was not found rather than inventing a timestamp.

LEVEL FRAMEWORK
Assessment basis: {source_name}

{criteria}

SESSION METRICS
Duration: {format_duration(metrics.duration_seconds)}
Coach / Coachee word share: {metrics.coach_share_pct}% / {metrics.coachee_share_pct}%
Coach turns: {metrics.coach_turns}
Coach questions: {metrics.coach_questions}
Stacked-question turns: {metrics.stacked_question_turns}
Average coach turn: {metrics.average_coach_words:.1f} words
Longest coach turn: {metrics.longest_coach_turn_words} words
Interruption notes: {metrics.interruptions}

VISIBLE SCENARIO
{scenario_text}

STRUCTURED OUTPUT CONTRACT
{contract}

TRANSCRIPT
{transcript}
"""


def _extract_json_text(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if text.startswith("\`\`\`"):
        text = re.sub(r"^\`\`\`(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*\`\`\`$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Review model did not return a JSON object.")
    return text[start : end + 1]


def parse_structured_review(raw_text: str) -> dict:
    """Parse and minimally validate structured model output."""
    data = json.loads(_extract_json_text(raw_text))
    if not isinstance(data, dict):
        raise ValueError("Structured review must be a JSON object.")

    behaviors = data.get("behaviors")
    if not isinstance(behaviors, list):
        raise ValueError("Structured review is missing behaviors.")

    for key in (
        "strengths",
        "development_areas",
        "patterns",
        "practice_edges",
        "moments",
        "competency_synthesis",
    ):
        value = data.get(key)
        if value is None:
            data[key] = []
        elif not isinstance(value, list):
            raise ValueError(f"Structured review field '{key}' must be a list.")

    if not isinstance(data.get("competency_1", {}), dict):
        data["competency_1"] = {}
    if not isinstance(data.get("competency_2", {}), dict):
        data["competency_2"] = {}

    return data


def _stamp_text(values) -> str:
    stamps = [str(item).strip() for item in (values or []) if str(item).strip()]
    return ", ".join(f"[{stamp}]" for stamp in stamps)


def _bullet_reference(item: dict) -> str:
    reference = str(item.get("reference", "")).strip()
    stamp_text = _stamp_text(item.get("timestamps", []))
    text = str(item.get("text", "")).strip()
    prefix = " - ".join(part for part in (reference, stamp_text) if part)
    return f"- {prefix}: {text}" if prefix else f"- {text}"


def render_structured_review(data: dict, level: str, source_name: str) -> str:
    """Render compact JSON findings into the existing readable review format locally."""
    level = (level or data.get("level") or "PCC").upper()
    lines = [
        f"DEVELOPMENTAL REVIEW — {level}",
        f"ASSESSMENT BASIS: {data.get('assessment_basis') or source_name}",
        "",
        "WHAT THE COACH DID WELL",
    ]

    strengths = data.get("strengths", [])
    if strengths:
        lines.extend(_bullet_reference(item) for item in strengths if isinstance(item, dict))
    else:
        lines.append("- No specific strength statement was returned.")

    lines.extend(["", "MARKER / BEHAVIORAL EVIDENCE"])
    for item in data.get("behaviors", []):
        if not isinstance(item, dict):
            continue
        reference = str(item.get("reference", "")).strip()
        name = str(item.get("name", "")).strip()
        rating = str(item.get("rating", "")).strip()
        label = " — ".join(part for part in (reference, name, rating) if part)
        lines.append(label)
        stamp_text = _stamp_text(item.get("timestamps", []))
        evidence = str(item.get("evidence", "")).strip()
        evidence_text = " ".join(part for part in (stamp_text, evidence) if part)
        lines.append(f"Evidence: {evidence_text}".rstrip())
        development = str(item.get("development", "")).strip()
        if development:
            lines.append(f"Development note: {development}")
        lines.append("")

    lines.append("COMPETENCY SYNTHESIS")
    c1 = data.get("competency_1", {})
    if level == "ACC":
        ethics = c1.get("ethics", "")
        role = c1.get("coaching_role", "")
        evidence = str(c1.get("evidence", "")).strip()
        lines.append(f"Competency 1 — Evidence strength: {ethics or 'Not assessable'}")
        lines.append(
            f"Observed evidence: Q1 Ethics {ethics or 'N/A'}; "
            f"Q2 Coaching role {role or 'N/A'}. {evidence}".strip()
        )
        lines.append(
            "Development opportunity: Review any NOT OBSERVED qualifier with a qualified mentor coach."
        )
        c2 = data.get("competency_2", {})
        lines.append("Competency 2 — Evidence strength: Not assessable")
        lines.append(
            f"Observed evidence: {c2.get('status') or 'NOT_RATED_SINGLE_SESSION'}. "
            f"{c2.get('note', '')}".strip()
        )
        lines.append(
            "Development opportunity: Evaluate this competency across the coach's broader professional practice."
        )
    else:
        c1_evidence = str(c1.get("evidence", "")).strip()
        if c1_evidence:
            lines.append("Competency 1 — Evidence strength: Developing")
            lines.append(f"Observed evidence: {c1_evidence}")
            lines.append(
                "Development opportunity: Continue monitoring ethical role clarity across practice."
            )

    for item in data.get("competency_synthesis", []):
        if not isinstance(item, dict):
            continue
        competency = str(item.get("competency", "")).strip()
        strength = str(item.get("strength", "")).strip()
        evidence = str(item.get("evidence", "")).strip()
        development = str(item.get("development", "")).strip()
        if competency:
            lines.append(
                f"{competency} — Evidence strength: {strength or 'Limited evidence'}"
            )
            lines.append(f"Observed evidence: {evidence}")
            if development:
                lines.append(f"Development opportunity: {development}")

    lines.extend(["", "PATTERNS TO WATCH"])
    lines.extend(
        f"- {str(item).strip()}"
        for item in data.get("patterns", [])
        if str(item).strip()
    )

    lines.extend(["", "THREE HIGH-LEVERAGE PRACTICE EDGES"])
    for item in data.get("practice_edges", []):
        if isinstance(item, dict):
            reference = str(item.get("reference", "")).strip()
            text = str(item.get("text", "")).strip()
            lines.append(f"- {reference}: {text}" if reference else f"- {text}")
        elif str(item).strip():
            lines.append(f"- {str(item).strip()}")

    lines.extend(["", "MOMENTS WORTH REVISITING"])
    for item in data.get("moments", []):
        if not isinstance(item, dict):
            continue
        timestamp = str(item.get("timestamp", "")).strip()
        reference = str(item.get("reference", "")).strip()
        happened = str(item.get("what_happened", "")).strip()
        alternative = str(item.get("alternative", "")).strip()
        prefix = " ".join(
            part
            for part in (f"[{timestamp}]" if timestamp else "", reference)
            if part
        )
        text = f"{prefix} {happened}".strip()
        if alternative:
            text += f" Alternative: {alternative}"
        lines.append(f"- {text}")

    lines.extend(["", "BOTTOM LINE"])
    bottom = str(data.get("bottom_line", "")).strip()
    if bottom:
        lines.append(bottom)
    lines.append("Developmental AI review only — not an official ICF assessment.")
    return "\n".join(lines).strip()


def structured_model_output_to_text(raw_text: str, level: str) -> str:
    source_name, _ = get_review_criteria(level)
    data = parse_structured_review(raw_text)
    return render_structured_review(data, level, source_name)


def generate_review(api_key: str, level: str, rows, metrics: SessionMetrics, scenario=None) -> str:
    prompt = build_review_prompt(level, rows, metrics, scenario)
    client = genai.Client(api_key=api_key)
    errors = []
    try:
        for model in REVIEW_MODELS:
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                raw = (getattr(response, "text", None) or "").strip()
                if not raw:
                    raise RuntimeError("returned no text")
                return structured_model_output_to_text(raw, level)
            except Exception as exc:
                errors.append(f"{model}: {exc}")

        detail = "\n\n".join(errors[-3:]) if errors else "No model returned a valid structured review."
        raise RuntimeError(
            "Gemini coaching review could not be generated with the current review models.\n\n"
            + detail
        )
    finally:
        try:
            client.close()
        except Exception:
            pass

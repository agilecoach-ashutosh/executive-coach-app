"""Concise on-screen feedback; the complete report remains available for export."""
import re

GOAL_COMPETENCIES = {
    "Agreements": "3", "Trust & Safety": "4", "Presence": "5",
    "Active Listening": "6", "Evokes Awareness": "7", "Client Growth": "8",
}


def review_sections(report):
    headings = {"WHAT THE COACH DID WELL", "AREAS FOR DEVELOPMENT", "MARKER / BEHAVIORAL EVIDENCE",
                "COMPETENCY SYNTHESIS", "PATTERNS TO WATCH", "HIGH-LEVERAGE PRACTICE EDGES",
                "MOMENTS WORTH REVISITING", "BOTTOM LINE"}
    sections, current = {}, None
    for line in report.splitlines():
        if line.strip() in headings:
            current = line.strip()
            sections[current] = []
        elif current and line.strip():
            sections[current].append(line.strip())
    return sections


def concise_review(report, goal="Full session"):
    sections = review_sections(report)
    if not sections:
        return report  # Progress/error messages are already concise.
    result = []
    if goal in GOAL_COMPETENCIES:
        number = GOAL_COMPETENCIES[goal]
        result.extend([f"YOUR PRACTICE GOAL · {goal}"])
        lines = sections.get("MARKER / BEHAVIORAL EVIDENCE", [])
        matches = []
        for i, line in enumerate(lines):
            if re.match(rf"^(?:C{number}\b|A{number}\.\d+\b)", line):
                matches.append(line)
                if i+1 < len(lines) and lines[i+1].startswith("Evidence:"):
                    matches.append(lines[i+1])
                if len(matches) >= 4:
                    break
        result.extend(matches or ["No specific evidence was returned for this goal."])
        result.append("")
    for source, title, limit in (
        ("WHAT THE COACH DID WELL", "WHAT WORKED", 3),
        ("HIGH-LEVERAGE PRACTICE EDGES", "WHAT TO PRACTISE NEXT", 3),
        ("AREAS FOR DEVELOPMENT", "DEVELOPMENT OPPORTUNITIES", 3),
        ("MOMENTS WORTH REVISITING", "KEY MOMENTS · CLICK A TURN TO SEE THE EVIDENCE", 3),
    ):
        result.append(title)
        result.extend(sections.get(source, [])[:limit] or ["Insufficient evidence for a specific finding."])
        result.append("")
    result.extend(["Full competency evidence and the annotated transcript are included in the Word report.",
                   "AI practice feedback; discuss interpretations with your mentor coach."])
    return "\n".join(result)

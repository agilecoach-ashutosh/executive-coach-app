import tempfile
import unittest
from pathlib import Path

from docx import Document

from review_export import (
    export_review_docx,
    parse_behavior_evidence,
    parse_competency_synthesis,
    split_review_sections,
)
from reviewer import SessionMetrics


SAMPLE_REVIEW = """DEVELOPMENTAL REVIEW — PCC
ASSESSMENT BASIS: ICF PCC Minimum Skills Requirements, effective January 1, 2026

WHAT THE COACH DID WELL
- The coach stayed with the client's agenda at [00:00:18].

MARKER / BEHAVIORAL EVIDENCE
Competency 3 — Clear client-owned session outcome — OBSERVED
Evidence: [00:00:18] The coach asked what would make the conversation useful.
Development note: Reconfirm the outcome when the topic shifts.

Competency 5 — Creates reflective space — PARTIAL EVIDENCE
Evidence: [00:03:10] A pause was visible in the transcript flow, but audio nuance is unavailable.
Development note: Allow more space after emotionally significant statements.

COMPETENCY SYNTHESIS
Establishes and Maintains Agreements — Evidence strength: Strong
Observed evidence: The outcome was client-owned and revisited.
Development opportunity: Re-contract explicitly after a major shift.

PATTERNS TO WATCH
- Avoid stacked questions.

THREE HIGH-LEVERAGE PRACTICE EDGES
- Ask one question at a time.

MOMENTS WORTH REVISITING
- [00:02:20] One coach turn contained two questions.

BOTTOM LINE
The session shows a client-centered foundation. Developmental AI review only — not an official ICF assessment.
"""


class ReviewExportTests(unittest.TestCase):
    def test_sections_and_evidence_parse(self):
        sections = split_review_sections(SAMPLE_REVIEW)
        behavior = parse_behavior_evidence(sections["MARKER / BEHAVIORAL EVIDENCE"])
        synthesis = parse_competency_synthesis(sections["COMPETENCY SYNTHESIS"])

        self.assertEqual(len(behavior), 2)
        self.assertEqual(behavior[0]["status"], "OBSERVED")
        self.assertIn("00:00:18", behavior[0]["evidence"])
        self.assertEqual(len(synthesis), 1)
        self.assertEqual(synthesis[0]["strength"], "Strong")

    def test_word_review_contains_structured_tables(self):
        metrics = SessionMetrics(
            duration_seconds=240,
            coach_turns=8,
            coachee_turns=9,
            coach_words=120,
            coachee_words=310,
            coach_share_pct=28,
            coachee_share_pct=72,
            coach_questions=7,
            stacked_question_turns=1,
            average_coach_words=15.0,
            longest_coach_turn_words=28,
            interruptions=0,
        )
        scenario = {
            "title": "Leadership transition",
            "environment": "Technology",
            "visible_problem": "A new manager is struggling to delegate.",
        }

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "review.docx"
            export_review_docx(SAMPLE_REVIEW, path, "PCC", metrics, scenario)
            doc = Document(path)

            self.assertGreaterEqual(len(doc.tables), 3)
            metric_headers = [cell.text for cell in doc.tables[0].rows[0].cells]
            behavior_headers = [cell.text for cell in doc.tables[1].rows[0].cells]
            competency_headers = [cell.text for cell in doc.tables[2].rows[0].cells]

            self.assertEqual(metric_headers, ["Session metric", "Value"])
            self.assertEqual(
                behavior_headers,
                ["Competency / behavior", "Evidence status", "Timestamp / evidence", "Development note"],
            )
            self.assertEqual(
                competency_headers,
                ["Competency", "Evidence strength", "Observed evidence", "Development opportunity"],
            )
            self.assertIn("OBSERVED", [cell.text for cell in doc.tables[1].rows[1].cells])


if __name__ == "__main__":
    unittest.main()

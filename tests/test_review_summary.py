import unittest
from review_summary import concise_review

REPORT = """DEVELOPMENTAL REVIEW — PCC
WHAT THE COACH DID WELL
- C6: Listened closely [T0002] Coach: “What matters?”
AREAS FOR DEVELOPMENT
- C3: Agree a clearer outcome.
MARKER / BEHAVIORAL EVIDENCE
C6 — Active Listening — OBSERVED
Evidence: [T0002] Coach: “What matters?”
C7 — Awareness — NOT OBSERVED
Evidence: No opportunity
COMPETENCY SYNTHESIS
Detailed competency information only for the full report
PATTERNS TO WATCH
Some pattern
HIGH-LEVERAGE PRACTICE EDGES
- C3: Agree an outcome at the start.
MOMENTS WORTH REVISITING
- [00:00:12] C6 [T0002] Coach: “What matters?”
BOTTOM LINE
Full summary
"""


class ReviewSummaryTests(unittest.TestCase):
    def test_summary_keeps_actionable_feedback_and_citation_ids_without_full_detail(self):
        summary = concise_review(REPORT)
        self.assertIn("WHAT WORKED", summary)
        self.assertIn("WHAT TO PRACTISE NEXT", summary)
        self.assertIn("[T0002]", summary)
        self.assertNotIn("Detailed competency information", summary)
        self.assertNotIn("MARKER / BEHAVIORAL EVIDENCE", summary)
        self.assertIn("Word report", summary)
        self.assertIn("Detailed competency information", REPORT)

    def test_selected_goal_surfaces_evidence_without_inventing_feedback(self):
        summary = concise_review(REPORT, "Active Listening")
        self.assertIn("YOUR PRACTICE GOAL · Active Listening", summary)
        self.assertIn("C6 — Active Listening — OBSERVED", summary)
        self.assertNotIn("C7 — Awareness — NOT OBSERVED", summary)
        self.assertIn("No specific evidence", concise_review(REPORT, "Presence"))

    def test_progress_and_errors_remain_readable(self):
        for text in ("Gemini busy — trying another model", "Review generation failed"):
            self.assertEqual(concise_review(text), text)


if __name__ == "__main__": unittest.main()

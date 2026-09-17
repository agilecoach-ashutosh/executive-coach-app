import unittest

from reviewer import build_review_prompt, calculate_metrics, format_duration, transcript_for_review
from review_criteria import get_review_criteria


class ReviewerMetricsTests(unittest.TestCase):
    def test_metrics_from_visible_transcript(self):
        rows = [
            ("00:00:00", "Coachee", "I feel stuck and I am not sure what I want."),
            ("00:00:15", "Coach", "What would make this conversation useful for you?"),
            ("00:00:30", "Coachee", "I want to understand why I keep hesitating."),
            ("00:00:45", "Coach", "What feels important about the hesitation? And what are you noticing now?"),
            ("00:01:00", "Session note", "Coachee response was interrupted; transcript may include words not played."),
        ]

        metrics = calculate_metrics(rows, 92.4)

        self.assertEqual(metrics.duration_seconds, 92)
        self.assertEqual(metrics.coach_turns, 2)
        self.assertEqual(metrics.coachee_turns, 2)
        self.assertEqual(metrics.coach_questions, 3)
        self.assertEqual(metrics.stacked_question_turns, 1)
        self.assertEqual(metrics.interruptions, 1)
        self.assertGreater(metrics.longest_coach_turn_words, 0)
        self.assertEqual(metrics.coach_share_pct + metrics.coachee_share_pct, 100)

    def test_duration_format(self):
        self.assertEqual(format_duration(92), "1:32")
        self.assertEqual(format_duration(3723), "1:02:03")

    def test_review_transcript_excludes_unknown_roles(self):
        rows = [
            ("00:00:00", "Coach", "What matters today?"),
            ("00:00:01", "Debug", "internal detail"),
            ("00:00:02", "Coachee", "My role transition."),
        ]
        text = transcript_for_review(rows)
        self.assertIn("Coach", text)
        self.assertIn("Coachee", text)
        self.assertNotIn("internal detail", text)

    def test_all_lenses_use_current_minimum_skills_requirements(self):
        for level in ("ACC", "PCC", "MCC"):
            source, criteria = get_review_criteria(level)
            self.assertIn("Minimum Skills Requirements", source)
            self.assertIn("Competency 3", criteria)
            self.assertIn("Competency 8", criteria)
            self.assertIn("TRANSCRIPT LIMITATION", criteria)

        acc_source, _ = get_review_criteria("ACC")
        pcc_source, _ = get_review_criteria("PCC")
        mcc_source, _ = get_review_criteria("MCC")
        self.assertIn("2026", acc_source)
        self.assertIn("2025", pcc_source)
        self.assertIn("2026", mcc_source)
        self.assertNotIn("2022", acc_source)
        self.assertNotIn("2021", pcc_source)

    def test_review_prompt_includes_selected_level_framework(self):
        rows = [
            ("00:00:04", "Coach", "What would make this useful today?"),
            ("00:00:11", "Coachee", "I want clarity about delegation."),
        ]
        metrics = calculate_metrics(rows, 30)

        for level in ("ACC", "PCC", "MCC"):
            source, _ = get_review_criteria(level)
            prompt = build_review_prompt(level, rows, metrics)
            self.assertIn(source, prompt)
            self.assertIn("MARKER / BEHAVIORAL EVIDENCE", prompt)
            self.assertIn("NOT ASSESSABLE", prompt)


if __name__ == "__main__":
    unittest.main()

import unittest

from reviewer import calculate_metrics, format_duration, transcript_for_review


class ReviewerMetricsTests(unittest.TestCase):
    def test_metrics_from_visible_transcript(self):
        rows = [
            ("10:00:00", "Coachee", "I feel stuck and I am not sure what I want."),
            ("10:00:15", "Coach", "What would make this conversation useful for you?"),
            ("10:00:30", "Coachee", "I want to understand why I keep hesitating."),
            ("10:00:45", "Coach", "What feels important about the hesitation? And what are you noticing now?"),
            ("10:01:00", "Session note", "Coachee response was interrupted; transcript may include words not played."),
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
            ("10:00:00", "Coach", "What matters today?"),
            ("10:00:01", "Debug", "internal detail"),
            ("10:00:02", "Coachee", "My role transition."),
        ]
        text = transcript_for_review(rows)
        self.assertIn("Coach", text)
        self.assertIn("Coachee", text)
        self.assertNotIn("internal detail", text)


if __name__ == "__main__":
    unittest.main()

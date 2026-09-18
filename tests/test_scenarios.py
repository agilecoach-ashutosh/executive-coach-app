import unittest

from scenarios import (
    COACHEE_SCENARIOS,
    DIFFICULTY_LEVELS,
    PRACTICE_FOCI,
    SCENARIO_PACKS,
    build_coachee_prompt,
    prepare_scenario,
    scenario_matches,
)


class ScenarioLibraryTests(unittest.TestCase):
    def test_library_has_expanded_scenario_set(self):
        self.assertGreaterEqual(len(COACHEE_SCENARIOS), 20)
        self.assertGreaterEqual(len(SCENARIO_PACKS), 10)

    def test_every_scenario_has_library_metadata(self):
        for scenario in COACHEE_SCENARIOS:
            self.assertTrue(scenario.get("pack"))
            self.assertTrue(scenario.get("focus"))
            self.assertIn("id", scenario)
            self.assertIn("title", scenario)
            self.assertIn("visible_problem", scenario)

    def test_prepare_scenario_adds_difficulty_and_focus_without_mutating_source(self):
        original = COACHEE_SCENARIOS[0]
        prepared = prepare_scenario(
            original,
            difficulty="Advanced",
            practice_focus="Evokes Awareness",
        )

        self.assertEqual(prepared["difficulty"], "Advanced")
        self.assertEqual(prepared["practice_focus"], "Evokes Awareness")
        self.assertNotIn("difficulty", original)
        self.assertNotIn("practice_focus", original)

    def test_prepare_scenario_falls_back_to_safe_defaults(self):
        prepared = prepare_scenario(
            COACHEE_SCENARIOS[0],
            difficulty="Impossible",
            practice_focus="Unknown",
        )
        self.assertEqual(prepared["difficulty"], "Experienced")
        self.assertEqual(prepared["practice_focus"], "Full session")

    def test_search_and_pack_filters(self):
        merger = next(item for item in COACHEE_SCENARIOS if item["id"] == "merger_uncertainty")

        self.assertTrue(scenario_matches(merger, query="merger"))
        self.assertTrue(
            scenario_matches(
                merger,
                pack="Change & Transformation",
            )
        )
        self.assertFalse(
            scenario_matches(
                merger,
                pack="Leadership Transition",
            )
        )

    def test_focus_filter(self):
        scenario = next(item for item in COACHEE_SCENARIOS if item["id"] == "decision_paralysis")
        self.assertTrue(
            scenario_matches(
                scenario,
                practice_focus="Evokes Awareness",
            )
        )
        self.assertFalse(
            scenario_matches(
                scenario,
                practice_focus="Trust & Safety",
            )
        )

    def test_advanced_prompt_changes_client_behavior_without_exposing_focus(self):
        prepared = prepare_scenario(
            COACHEE_SCENARIOS[0],
            difficulty="Advanced",
            practice_focus="Active Listening",
        )
        prompt = build_coachee_prompt(prepared)

        self.assertIn("Advanced:", prompt)
        self.assertIn("more guarded, contradictory", prompt)
        self.assertIn("Active Listening", prompt)
        self.assertIn("never mention that focus", prompt)

    def test_library_choices_are_stable(self):
        self.assertEqual(
            DIFFICULTY_LEVELS,
            ("Foundation", "Experienced", "Advanced"),
        )
        self.assertIn("Full session", PRACTICE_FOCI)
        self.assertIn("Evokes Awareness", PRACTICE_FOCI)


if __name__ == "__main__":
    unittest.main()

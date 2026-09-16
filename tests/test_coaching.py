import unittest
from coaching import TurnGate, Transcript


class TurnTests(unittest.TestCase):
    def test_quiet_does_not_trigger_coach(self):
        gate = TurnGate()
        for now in range(120):
            self.assertIsNone(gate.feed(0, now))

    def test_waits_six_seconds_after_last_speech(self):
        gate = TurnGate()
        self.assertIsNone(gate.feed(.1, 0))
        self.assertIsNone(gate.feed(.1, .04))
        self.assertEqual(gate.feed(.1, .08), 'start')
        self.assertIsNone(gate.feed(0, 5))
        self.assertIsNone(gate.feed(.1, 5.5))
        self.assertIsNone(gate.feed(0, 11))
        self.assertEqual(gate.feed(0, 12), 'end')
        self.assertIsNone(gate.feed(0, 30))

    def test_hold_preserves_thinking_time(self):
        gate = TurnGate(active=True, last_voice=1)
        self.assertIsNone(gate.feed(0, 120, hold=True))
        self.assertTrue(gate.active)
        self.assertEqual(gate.feed(0, 121, hold=False), 'end')

    def test_short_noise_does_not_open_turn(self):
        gate = TurnGate()
        self.assertIsNone(gate.feed(.1, 0))
        self.assertIsNone(gate.feed(0, .04))
        self.assertFalse(gate.active)

    def test_transcript_unicode_and_boundaries(self):
        log = Transcript()
        log.add('Coachee', 'मुझे ')
        log.add('Coachee', 'सोचना है।')
        log.boundary = True
        log.add('Coachee', 'More')
        log.add('Coach', 'What matters?')
        self.assertEqual(len(log.rows), 3)
        self.assertIn('मुझे सोचना है।', log.export())
        self.assertNotIn('API', log.export())


if __name__ == '__main__':
    unittest.main()

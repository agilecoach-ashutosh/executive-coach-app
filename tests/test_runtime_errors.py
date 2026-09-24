import errno
import unittest

from runtime_errors import classify_export_error, classify_runtime_error


class RuntimeErrorClassificationTests(unittest.TestCase):
    def test_gemini_quota_error(self):
        issue = classify_runtime_error(
            "429 RESOURCE_EXHAUSTED: quota exceeded",
            "Google Gemini",
        )
        self.assertEqual(issue.code, "quota")
        self.assertIn("usage limit", issue.title.lower())
        self.assertIn("does not automatically enable billing", issue.message)

    def test_invalid_api_key(self):
        issue = classify_runtime_error(
            "401 UNAUTHENTICATED: API_KEY_INVALID",
            "Google Gemini",
        )
        self.assertEqual(issue.code, "auth")
        self.assertIn("API key not accepted", issue.title)

    def test_model_unavailable(self):
        issue = classify_runtime_error(
            "404 models/gemini-example is not found for API version v1beta",
            "Google Gemini",
        )
        self.assertEqual(issue.code, "model")

    def test_provider_access_denied(self):
        issue = classify_runtime_error(
            "403 PERMISSION_DENIED: project is not allowed to use this model",
            "Google Gemini",
        )
        self.assertEqual(issue.code, "access")

    def test_timeout(self):
        issue = classify_runtime_error("request timed out", "Groq")
        self.assertEqual(issue.code, "timeout")

    def test_provider_unavailable(self):
        issue = classify_runtime_error("503 Service Unavailable", "Groq")
        self.assertEqual(issue.code, "provider_unavailable")

    def test_network_failure(self):
        issue = classify_runtime_error(
            "Temporary failure in name resolution",
            "Google Gemini",
        )
        self.assertEqual(issue.code, "network")
        self.assertIn("VPN/proxy", issue.message)

    def test_microphone_permission_error(self):
        issue = classify_runtime_error(
            "MIC_DEVICE_ERROR: Unanticipated host error: Access is denied.",
            "Google Gemini",
        )
        self.assertEqual(issue.code, "mic_permission")

    def test_microphone_device_error(self):
        issue = classify_runtime_error(
            "MIC_DEVICE_ERROR: Device unavailable [PaErrorCode -9985]",
            "Groq",
        )
        self.assertEqual(issue.code, "mic_device")

    def test_speaker_device_error(self):
        issue = classify_runtime_error(
            "SPEAKER_DEVICE_ERROR: Invalid device [PaErrorCode -9996]",
            "Groq",
        )
        self.assertEqual(issue.code, "speaker_device")

    def test_audio_overload_error(self):
        issue = classify_runtime_error(
            "Audio input cannot keep up. Stop and reconnect.",
            "Groq",
        )
        self.assertEqual(issue.code, "audio_overload")

    def test_review_message_preserves_transcript(self):
        issue = classify_runtime_error(
            "429 rate_limit_exceeded",
            "Groq",
            context="review",
        )
        self.assertIn("transcript is unchanged", issue.message.lower())

    def test_unknown_error_does_not_echo_raw_provider_noise(self):
        raw = "OpaqueProviderException secret-internal-stack-fragment"
        issue = classify_runtime_error(raw, "Google Gemini")
        self.assertEqual(issue.code, "unknown")
        self.assertNotIn(raw, issue.message)


class ExportErrorClassificationTests(unittest.TestCase):
    def test_permission_error(self):
        issue = classify_export_error(
            PermissionError(errno.EACCES, "Access is denied"),
            artifact="session transcript",
        )
        self.assertEqual(issue.code, "export_permission")
        self.assertIn("another application", issue.message)

    def test_disk_full(self):
        issue = classify_export_error(
            OSError(errno.ENOSPC, "No space left on device"),
            artifact="session audio",
        )
        self.assertEqual(issue.code, "storage")

    def test_read_only_location(self):
        issue = classify_export_error(
            OSError(getattr(errno, "EROFS", 30), "Read-only file system"),
            artifact="coaching review",
        )
        self.assertEqual(issue.code, "read_only")

    def test_missing_folder(self):
        issue = classify_export_error(
            FileNotFoundError(errno.ENOENT, "No such file or directory"),
            artifact="session transcript",
        )
        self.assertEqual(issue.code, "folder_missing")


if __name__ == "__main__":
    unittest.main()

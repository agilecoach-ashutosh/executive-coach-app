"""Translate provider, audio, and export failures into useful Presence Coach messages.

The engines deliberately emit compact technical details. This module is the single
place where those details become stable, human-readable categories for the UI.
"""
from __future__ import annotations

import errno
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class UserFacingError:
    code: str
    title: str
    message: str


def _clean(detail: object, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(detail or "")).strip()
    return text[:limit]


def _contains(text: str, *markers: str) -> bool:
    return any(marker in text for marker in markers)


def classify_runtime_error(
    detail: object,
    provider: str | None = None,
    *,
    context: str = "session",
) -> UserFacingError:
    """Classify a provider/audio error without exposing raw API noise to the user."""
    clean = _clean(detail)
    text = clean.lower()
    provider_name = (provider or "AI provider").strip() or "AI provider"
    is_review = context == "review"
    preserved = (
        "Your transcript is still available."
        if not is_review
        else "Your transcript is unchanged and still available."
    )

    if text.startswith("mic_device_error:"):
        denied = _contains(
            text,
            "permission",
            "access is denied",
            "access denied",
            "not permitted",
            "not authorized",
        )
        if denied:
            return UserFacingError(
                "mic_permission",
                "Microphone access required",
                (
                    "Presence Coach could not access the selected microphone. Allow microphone "
                    "access for desktop apps in your computer's privacy settings, then choose the "
                    f"microphone again in Presence Settings. {preserved}"
                ),
            )
        return UserFacingError(
            "mic_device",
            "Microphone unavailable",
            (
                "Presence Coach could not open the selected microphone. Check that it is connected "
                "and not exclusively in use by another application, then select it again in "
                f"Settings → Audio devices. {preserved}"
            ),
        )

    if text.startswith("speaker_device_error:"):
        return UserFacingError(
            "speaker_device",
            "Audio output unavailable",
            (
                "Presence Coach could not open the selected speaker or headphones. Check that the "
                "device is connected, then select it again in Settings → Audio devices. "
                f"{preserved}"
            ),
        )

    if _contains(
        text,
        "audio input cannot keep up",
        "playback buffer exceeded",
        "input overflow",
        "output underflow",
    ):
        return UserFacingError(
            "audio_overload",
            "Audio couldn't keep up",
            (
                "Presence Coach could not process audio reliably on this device. Close other "
                "audio-heavy applications, check the selected devices, and reconnect. "
                f"{preserved}"
            ),
        )

    if _contains(
        text,
        "429",
        "resource_exhausted",
        "rate_limit_exceeded",
        "quota_exceeded",
        "quota exceeded",
        "rate limit",
        "too many requests",
    ):
        return UserFacingError(
            "quota",
            f"{provider_name} usage limit reached",
            (
                f"Your {provider_name} project has reached a current usage or rate limit. "
                "Please try again later or check the provider's quota/rate-limit page. "
                "Presence Coach does not automatically enable billing or switch a free project "
                f"to paid usage. {preserved}"
            ),
        )

    auth_markers = (
        "401",
        "unauthorized",
        "unauthenticated",
        "api_key_invalid",
        "invalid api key",
        "invalid_api_key",
        "authentication failed",
        "incorrect api key",
        "invalid x-api-key",
    )
    if _contains(text, *auth_markers):
        return UserFacingError(
            "auth",
            f"{provider_name} API key not accepted",
            (
                f"Presence Coach could not authenticate with {provider_name}. Open Settings and "
                "re-enter a valid API key, then try again. If the key is correct, confirm its "
                f"project has access to the selected model. {preserved}"
            ),
        )

    model_markers = (
        "model_not_found",
        "model not found",
        "model is not found",
        "model unavailable",
        "model is unavailable",
        "unsupported model",
        "does not exist",
        "not supported for",
    )
    if _contains(text, *model_markers) or (
        "404" in text and _contains(text, "model", "models/")
    ):
        return UserFacingError(
            "model",
            "Selected AI model is unavailable",
            (
                f"The selected {provider_name} model is not available to this project or is no "
                "longer available. Choose another model in Settings or update Presence Coach "
                f"if a newer configuration is available. {preserved}"
            ),
        )

    if _contains(
        text,
        "403",
        "permission_denied",
        "permission denied",
        "forbidden",
        "not allowed to use",
        "access denied",
    ):
        return UserFacingError(
            "access",
            f"{provider_name} access not permitted",
            (
                f"{provider_name} rejected this request. Check that the API project has access "
                "to the selected model and that any provider billing/region requirements for "
                f"your account are satisfied. {preserved}"
            ),
        )

    if _contains(
        text,
        "timeout",
        "timed out",
        "deadline exceeded",
        "deadline_exceeded",
    ):
        return UserFacingError(
            "timeout",
            f"{provider_name} took too long to respond",
            (
                "The request timed out before the AI provider responded. Check your internet "
                f"connection and try again. {preserved}"
            ),
        )

    if _contains(
        text,
        "503",
        "502",
        "504",
        "500",
        "service unavailable",
        "temporarily unavailable",
        "server overloaded",
        "overloaded",
        "internal server error",
        "internal_error",
    ):
        return UserFacingError(
            "provider_unavailable",
            f"{provider_name} is temporarily unavailable",
            (
                f"The {provider_name} service is having trouble responding right now. "
                f"Please wait a little and try again. {preserved}"
            ),
        )

    if _contains(
        text,
        "getaddrinfo",
        "name resolution",
        "temporary failure in name resolution",
        "dns",
        "certificate_verify_failed",
        "ssl error",
        "network is unreachable",
        "network unreachable",
        "connection refused",
        "connection reset",
        "connection aborted",
        "connection closed",
        "server disconnected",
        "websocket",
        "socket",
        "no route to host",
    ):
        return UserFacingError(
            "network",
            "Connection lost",
            (
                f"Presence Coach lost its connection to {provider_name}. Check your internet "
                f"connection, VPN/proxy if you use one, and reconnect when ready. {preserved}"
            ),
        )

    return UserFacingError(
        "unknown",
        "Presence Coach couldn't continue",
        (
            "Something unexpected interrupted this request. Please try again. If it happens "
            "again, check your API key, selected model, audio devices, and internet connection."
            f" {preserved}"
        ),
    )


def classify_export_error(exc: BaseException, *, artifact: str = "file") -> UserFacingError:
    """Translate local file-system failures for transcript/review/audio exports."""
    clean = _clean(exc)
    text = clean.lower()
    error_no = getattr(exc, "errno", None)

    if error_no in (errno.ENOSPC, getattr(errno, "EDQUOT", -1)) or _contains(
        text, "no space left", "disk full", "quota exceeded"
    ):
        return UserFacingError(
            "storage",
            "Not enough storage to export",
            (
                f"There is not enough free storage to save this {artifact}. Free some space "
                "or choose another drive/folder, then try again."
            ),
        )

    if isinstance(exc, PermissionError) or error_no in (errno.EACCES, errno.EPERM) or _contains(
        text, "permission denied", "access is denied", "access denied"
    ):
        return UserFacingError(
            "export_permission",
            "Can't save the file",
            (
                f"Presence Coach cannot write this {artifact} to the selected location. The file "
                "may already be open in another application, or the folder may not allow writes. "
                "Close the existing file or choose another folder and try again."
            ),
        )

    if error_no == getattr(errno, "EROFS", -1) or "read-only" in text or "read only" in text:
        return UserFacingError(
            "read_only",
            "Selected location is read-only",
            (
                f"The selected location does not allow files to be saved. Choose a writable "
                f"folder for the {artifact} and try again."
            ),
        )

    if isinstance(exc, FileNotFoundError) or error_no == errno.ENOENT:
        return UserFacingError(
            "folder_missing",
            "Save location unavailable",
            (
                "The selected folder is no longer available. It may have been moved, disconnected, "
                f"or removed. Choose another location for the {artifact}."
            ),
        )

    technical = f"\n\nTechnical detail: {clean}" if clean else ""
    return UserFacingError(
        "export_unknown",
        "Export failed",
        (
            f"Presence Coach could not save the {artifact}. Choose another location and try again."
            f"{technical}"
        ),
    )

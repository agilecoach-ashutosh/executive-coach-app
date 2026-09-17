"""Elapsed transcript + Word/MP3 export layer for Presence Coach."""
from __future__ import annotations

import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import provider_mode as provider
import practice_review as review
from review_export import export_review_docx
from session_export import export_transcript_docx, format_elapsed


base = provider.base
_original_app_init = base.App.__init__
_original_transcript = base.Transcript
_original_show_session_review = base.App.show_session_review
_original_make_sidebar = review._make_scrollable_review_sidebar


def _resource_path(relative: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / relative


def _branded_init(self):
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PresenceCoach.Desktop")
        except Exception:
            pass

    _original_app_init(self)

    try:
        icon = _resource_path("assets/presence.ico")
        if icon.exists():
            self.iconbitmap(default=str(icon))
    except (tk.TclError, OSError):
        # The app must remain usable if Windows rejects a custom icon for any reason.
        pass


class ElapsedTranscript(_original_transcript):
    """Transcript whose timestamps are elapsed session time rather than wall clock."""

    def __init__(self):
        super().__init__()
        self.started_at = time.monotonic()

    def add(self, role, text):
        if not text:
            return
        if self.rows and not self.boundary and self.rows[-1][1] == role:
            stamp, existing_role, previous = self.rows[-1]
            self.rows[-1] = (stamp, existing_role, previous + text)
        else:
            elapsed = time.monotonic() - self.started_at
            self.rows.append((format_elapsed(elapsed), role, text))
        self.boundary = False

    def export(self):
        # Kept for compatibility with tests/legacy callers. The application UI now
        # exports the transcript as a Word table via export_transcript_word().
        return (
            "PRESENCE COACH — AI conversation\n"
            "Timestamps are elapsed session time. Speech transcripts may contain errors.\n\n"
            + self.render()
            + "\n"
        )


def _capture_review_sidebar(self, parent):
    content = _original_make_sidebar(self, parent)
    self._review_sidebar = content
    return content


review._make_scrollable_review_sidebar = _capture_review_sidebar
base.Transcript = ElapsedTranscript


def _review_parent(self):
    parent = self
    if getattr(self, "_review_dialog", None) and self._review_dialog.winfo_exists():
        parent = self._review_dialog
    return parent


def export_transcript_word(self):
    if not self.transcript.rows:
        messagebox.showinfo("Transcript", "There is no conversation to export yet.")
        return False

    parent = _review_parent(self)
    filename = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".docx",
        initialfile="Presence-Coach-session-transcript.docx",
        filetypes=[("Word document", "*.docx")],
    )
    if not filename:
        return False

    try:
        export_transcript_docx(self.transcript.rows, filename)
    except Exception as exc:
        messagebox.showerror("Export failed", str(exc), parent=parent)
        return False

    self.dirty = False
    messagebox.showinfo(
        "Transcript exported",
        "The session transcript was saved as a Word document with Speaker, elapsed Timestamp, and Transcript columns.",
        parent=parent,
    )
    return True


def export_session_audio(self):
    engine = getattr(self, "engine", None)
    parent = _review_parent(self)
    if not engine or not hasattr(engine, "has_audio") or not engine.has_audio():
        messagebox.showinfo(
            "Session audio",
            "No recorded session audio is available. Audio export is available for sessions started after this feature was installed.",
            parent=parent,
        )
        return False

    filename = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".mp3",
        initialfile="Presence-Coach-session-audio.mp3",
        filetypes=[("MP3 audio", "*.mp3")],
    )
    if not filename:
        return False

    try:
        engine.export_audio(filename)
    except Exception as exc:
        messagebox.showerror("Audio export failed", str(exc), parent=parent)
        return False

    messagebox.showinfo(
        "Audio exported",
        "The coaching conversation was saved as an MP3 for reflection.",
        parent=parent,
    )
    return True


def export_coaching_review_word(self):
    if not getattr(self, "practice_review_text", ""):
        messagebox.showinfo("Review", "Generate a coaching review first.")
        return False

    level = self.practice_review_level.get().upper()
    parent = _review_parent(self)
    filename = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".docx",
        initialfile=f"Presence-Coach-{level}-practice-review.docx",
        filetypes=[("Word document", "*.docx")],
    )
    if not filename:
        return False

    try:
        metrics = review._current_metrics(self)
        export_review_docx(
            self.practice_review_text,
            filename,
            level,
            metrics,
            getattr(self, "current_scenario", None),
        )
    except Exception as exc:
        messagebox.showerror("Review export failed", str(exc), parent=parent)
        return False

    messagebox.showinfo(
        "Review exported",
        "The developmental review was saved as a structured Word report with session metrics and ICF behavior-evidence tables.",
        parent=parent,
    )
    return True


def show_session_review_with_exports(self):
    _original_show_session_review(self)

    sidebar = getattr(self, "_review_sidebar", None)
    if not sidebar or not sidebar.winfo_exists():
        return

    # Clarify Word export formats on the existing review controls.
    for child in sidebar.winfo_children():
        try:
            text = child.cget("text")
            if text == "Export transcript":
                child.configure(text="Export transcript (.docx)")
            elif text == "Export review":
                child.configure(text="Export review (.docx)")
        except (tk.TclError, AttributeError):
            pass

    existing = getattr(self, "_review_audio_button", None)
    if existing and existing.winfo_exists():
        engine = getattr(self, "engine", None)
        existing.configure(
            state="normal" if engine and hasattr(engine, "has_audio") and engine.has_audio() else "disabled"
        )
        return

    children = sidebar.winfo_children()
    before_widget = children[-1] if children else None
    self._review_audio_button = self.button(
        sidebar,
        "Export session audio (.mp3)",
        self.export_session_audio,
        compact=True,
    )
    pack_options = {"fill": "x", "pady": 3}
    if before_widget is not None:
        pack_options["before"] = before_widget
    self._review_audio_button.pack(**pack_options)

    engine = getattr(self, "engine", None)
    if not engine or not hasattr(engine, "has_audio") or not engine.has_audio():
        self._review_audio_button.configure(state="disabled")


base.App.__init__ = _branded_init
base.App.save = export_transcript_word
base.App.export_transcript_word = export_transcript_word
base.App.export_session_audio = export_session_audio
base.App.export_coaching_review = export_coaching_review_word
base.App.show_session_review = show_session_review_with_exports


if __name__ == "__main__":
    base.App().mainloop()

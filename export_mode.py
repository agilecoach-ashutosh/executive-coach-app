"""Session export layer for Presence Coach.

Adds elapsed-time transcript stamps, Word table export, and explicit two-sided MP3
export on top of the current Gemini/Groq + Coach Practice experience.
"""
from __future__ import annotations

import time
from tkinter import filedialog, messagebox

import provider_mode as provider
from session_export import export_transcript_docx, format_elapsed


base = provider.base
_original_transcript = base.Transcript
_original_show_session_review = base.App.show_session_review


class ElapsedTranscript(_original_transcript):
    """Transcript whose timestamps are elapsed session time, not wall-clock time."""

    def __init__(self):
        super().__init__()
        self.started_at = time.monotonic()

    def restart_clock(self):
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


# app.py and all layered modes resolve Transcript through the base app module.
base.Transcript = ElapsedTranscript


def export_word_transcript(self):
    if not self.transcript.rows:
        messagebox.showinfo("Transcript", "There is no conversation to export yet.")
        return False

    is_practice = getattr(self, "practice_mode", "coachee") == "coach"
    title = (
        "Presence Coach — Coach Practice Transcript"
        if is_practice
        else "Presence Coach — Coaching Session Transcript"
    )
    initial = (
        "Presence-Coach-practice-transcript.docx"
        if is_practice
        else "Presence-Coach-session-transcript.docx"
    )

    filename = filedialog.asksaveasfilename(
        parent=self._review_dialog
        if getattr(self, "_review_dialog", None) and self._review_dialog.winfo_exists()
        else self,
        defaultextension=".docx",
        initialfile=initial,
        filetypes=[("Word document", "*.docx")],
    )
    if not filename:
        return False

    try:
        export_transcript_docx(self.transcript.rows, filename, title=title)
    except Exception as exc:
        messagebox.showerror("Transcript export failed", str(exc))
        return False

    self.dirty = False
    return True


def export_session_audio(self):
    engine = getattr(self, "engine", None)
    if not engine or not hasattr(engine, "has_audio") or not engine.has_audio():
        messagebox.showinfo(
            "Audio export",
            "No recorded session audio is available yet. Audio becomes available after a voice session has started.",
        )
        return False

    if engine.is_alive():
        proceed = messagebox.askyesno(
            "Session still running",
            "The session is still live. Exporting now will save only the audio recorded so far. Continue?",
        )
        if not proceed:
            return False

    filename = filedialog.asksaveasfilename(
        parent=self._review_dialog
        if getattr(self, "_review_dialog", None) and self._review_dialog.winfo_exists()
        else self,
        defaultextension=".mp3",
        initialfile="Presence-Coach-session-audio.mp3",
        filetypes=[("MP3 audio", "*.mp3")],
    )
    if not filename:
        return False

    try:
        engine.export_audio(filename)
    except Exception as exc:
        messagebox.showerror("Audio export failed", str(exc))
        return False

    messagebox.showinfo(
        "Audio exported",
        "The session audio was saved as an MP3 for your reflection/review.",
    )
    return True


def show_session_review_with_audio(self):
    _original_show_session_review(self)

    export_review = getattr(self, "_review_export_button", None)
    dialog = getattr(self, "_review_dialog", None)
    if not export_review or not export_review.winfo_exists() or not dialog or not dialog.winfo_exists():
        return

    existing = getattr(self, "_review_audio_button", None)
    if existing and existing.winfo_exists():
        return

    parent = export_review.master
    self._review_audio_button = self.button(
        parent,
        "Export audio (.mp3)",
        self.export_session_audio,
        compact=True,
    )
    # Keep transcript and audio exports together, immediately before Export review.
    self._review_audio_button.pack(fill="x", pady=3, before=export_review)


base.App.save = export_word_transcript
base.App.export_session_audio = export_session_audio
base.App.show_session_review = show_session_review_with_audio


if __name__ == "__main__":
    base.App().mainloop()

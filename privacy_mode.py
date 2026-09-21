"""Privacy, consent, and session-data lifecycle controls for Presence Coach.

This layer adds:
- provider-specific, session-scoped authorization;
- a plain-language privacy and data-use dialog;
- an explicit in-memory session-data discard action;
- consent checks before post-session AI review;
- immediate session stop when provider authorization is withdrawn.
"""
from __future__ import annotations

import queue
import tkinter as tk
import webbrowser
from tkinter import messagebox

import provider_mode as provider

base = provider.base
_original_init = base.App.__init__
_original_poll = base.App.poll
_original_generate_review = base.App.generate_coaching_review

PRIVACY_NOTICE_URL = (
    "https://github.com/agilecoach-ashutosh/executive-coach-app/blob/main/PRIVACY.md"
)
GOOGLE_TERMS_URL = "https://ai.google.dev/gemini-api/terms"
GROQ_DATA_URL = "https://console.groq.com/docs/your-data"
GROQ_DPA_URL = "https://console.groq.com/docs/legal/customer-data-processing-addendum"


def _paragraph(parent, text, *, fg=None, size=9, bold=False, pady=(0, 8)):
    label = tk.Label(
        parent,
        text=text,
        bg=base.PANEL,
        fg=fg or base.MUTED,
        font=("Segoe UI", size, "bold" if bold else "normal"),
        justify="left",
        anchor="w",
        wraplength=610,
    )
    label.pack(fill="x", anchor="w", pady=pady)
    return label


def _provider_name(self):
    if hasattr(self, "provider"):
        return self.provider.get()
    return provider.GEMINI


def _provider_terms_url(self):
    return GROQ_DATA_URL if _provider_name(self) == provider.GROQ else GOOGLE_TERMS_URL


def _refresh_consent_copy(self):
    if not hasattr(self, "provider_consent_text"):
        return
    if _provider_name(self) == provider.GROQ:
        self.provider_consent_text.set(
            "I’m 18+ and allow this session’s voice/text to be processed by GroqCloud"
        )
    else:
        self.provider_consent_text.set(
            "I’m 18+ and allow this session’s voice/text to be processed by Google Gemini"
        )


def _provider_changed(self, *_):
    selected = _provider_name(self)
    previous = getattr(self, "_privacy_provider", None)
    self._privacy_provider = selected

    if previous is not None and previous != selected:
        self._privacy_resetting_consent = True
        try:
            self.consent.set(False)
        finally:
            self._privacy_resetting_consent = False

    # provider_mode also updates the checkbox text. Run after idle so this
    # privacy-specific wording is the final copy visible to the user.
    self.after_idle(lambda: _refresh_consent_copy(self))


def _consent_changed(self, *_):
    if getattr(self, "_privacy_resetting_consent", False) or self.consent.get():
        return

    engine = getattr(self, "engine", None)
    stopping = getattr(engine, "stopping", None) if engine else None
    is_stopping = bool(stopping and stopping.is_set())
    if engine and engine.is_alive() and not is_stopping:
        self.stop()
        messagebox.showinfo(
            "Provider permission withdrawn",
            "Presence is ending the live session so no further voice or text is sent to the AI provider.",
            parent=self,
        )


def _enhance_consent_bar(self):
    if not hasattr(self, "consent_bar"):
        return

    info_labels = [
        child
        for child in self.consent_bar.winfo_children()
        if isinstance(child, tk.Label)
    ]
    if info_labels:
        info_labels[0].configure(
            text=(
                "Session audio/transcript stay in app memory unless you export them. "
                "Cloud processing still occurs with the selected provider."
            )
        )

    privacy_row = tk.Frame(self.consent_bar, bg=base.BG)
    privacy_row.pack(pady=(3, 0))
    self.button(
        privacy_row,
        "Privacy & data use",
        self.open_privacy_notice,
        compact=True,
    ).pack(side="left", padx=3)


def privacy_init(self):
    _original_init(self)

    self._privacy_provider = _provider_name(self)
    self._privacy_resetting_consent = False
    self._privacy_last_state = self.state.get()

    _enhance_consent_bar(self)
    _refresh_consent_copy(self)

    if hasattr(self, "provider"):
        self.provider.trace_add("write", self._privacy_provider_trace)
    self.consent.trace_add("write", self._privacy_consent_trace)


def privacy_poll(self):
    previous = getattr(self, "_privacy_last_state", self.state.get())
    _original_poll(self)
    current = self.state.get()

    # Require fresh authorization for every completed voice session.
    if current == "Session complete" and previous != "Session complete":
        self._privacy_resetting_consent = True
        try:
            self.consent.set(False)
        finally:
            self._privacy_resetting_consent = False

    self._privacy_last_state = current


def clear_session_data(self, parent=None):
    parent = parent or self
    engine = getattr(self, "engine", None)

    if engine and engine.is_alive():
        messagebox.showinfo(
            "End the session first",
            "End the live session before discarding its in-memory transcript and audio.",
            parent=parent,
        )
        return False

    has_transcript = bool(getattr(self.transcript, "rows", []))
    recorder = getattr(engine, "recorder", None) if engine else None
    has_audio = bool(recorder and recorder.has_audio())
    has_review = bool(getattr(self, "practice_review_text", ""))

    if not has_transcript and not has_audio and not has_review:
        messagebox.showinfo(
            "Session data",
            "There is no in-memory session transcript or audio to discard.",
            parent=parent,
        )
        return True

    if not messagebox.askyesno(
        "Discard session data?",
        (
            "This clears the current in-memory transcript and session audio from Presence.\n\n"
            "It does not delete files you already exported or data retained by the selected AI provider."
        ),
        parent=parent,
    ):
        return False

    if recorder:
        recorder.clear()

    review_dialog = getattr(self, "_review_dialog", None)
    if review_dialog and review_dialog.winfo_exists():
        review_dialog.destroy()
    self._review_dialog = None

    self.transcript = base.Transcript()
    self.dirty = False
    self.audio_exported = True
    self.engine = None
    self.level = 0
    self.set_session_controls(False)
    self.state.set("Ready when you are")
    self.connection_state.set("●  Ready")

    self._privacy_resetting_consent = True
    try:
        self.consent.set(False)
    finally:
        self._privacy_resetting_consent = False

    try:
        provider.review._clear_review_state(self)
    except Exception:
        pass

    while True:
        try:
            self.events.get_nowait()
        except queue.Empty:
            break

    self.render()
    messagebox.showinfo(
        "Session data discarded",
        (
            "The current transcript and captured session audio were cleared from application memory. "
            "Exported files and provider-side records, if any, are outside this control."
        ),
        parent=parent,
    )
    return True


def open_privacy_notice(self):
    dialog = tk.Toplevel(self)
    dialog.title("Presence Coach • Privacy & data use")
    dialog.configure(bg=base.BG)
    dialog.geometry("700x760")
    dialog.minsize(650, 650)
    dialog.transient(self)

    self.label(dialog, "PRIVACY & DATA USE", 18, base.AMBER, "bold").pack(
        anchor="w", padx=26, pady=(22, 4)
    )
    self.label(
        dialog,
        "What happens to a coaching conversation in the current desktop build",
        9,
        base.MUTED,
    ).pack(anchor="w", padx=26, pady=(0, 12))

    canvas = tk.Canvas(dialog, bg=base.BG, highlightthickness=0, bd=0)
    scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y", pady=(0, 70))
    canvas.pack(fill="both", expand=True, padx=(26, 8), pady=(0, 8))

    content = tk.Frame(canvas, bg=base.BG)
    window_id = canvas.create_window((0, 0), window=content, anchor="nw")

    def sync(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def fit_width(event):
        canvas.itemconfigure(window_id, width=max(580, event.width))

    content.bind("<Configure>", sync)
    canvas.bind("<Configure>", fit_width)
    canvas.bind(
        "<MouseWheel>",
        lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
    )

    def card(title, body, accent=None):
        frame = tk.Frame(
            content,
            bg=base.PANEL,
            highlightbackground=base.BORDER,
            highlightthickness=1,
            padx=18,
            pady=14,
        )
        frame.pack(fill="x", pady=6)
        self.label(frame, title, 11, accent or base.INK, "bold").pack(anchor="w", pady=(0, 7))
        _paragraph(frame, body, pady=(0, 0))
        return frame

    card(
        "Local application behavior",
        (
            "Presence has no project-operated account system, session-content backend, or analytics/telemetry "
            "in the current code. The transcript and captured two-sided session audio are held in application "
            "memory. Nothing is written as a transcript or recording unless you explicitly export it. Saved API "
            "keys use the operating system credential store."
        ),
        base.CYAN,
    )

    selected = _provider_name(self)
    if selected == provider.GROQ:
        provider_text = (
            "For a Groq session, microphone turns are sent to Groq Whisper for speech-to-text, conversation "
            "text is sent to the selected Groq-hosted chat model, and reply text is sent to Groq Orpheus for "
            "speech generation. Groq documents default inference retention controls and optional Zero Data "
            "Retention. Check your current Groq account settings and terms before using real client information."
        )
    else:
        provider_text = (
            "For a Gemini session, live voice/text and model responses are processed by Google Gemini under "
            "your own API project. Google applies different data-use rules to unpaid and paid services, and its "
            "current terms require Paid Services when an API client is made available to users in the EEA, "
            "Switzerland, or the UK. Check your current project plan and terms before using real client information."
        )
    card(f"Cloud processing • {selected}", provider_text, base.AMBER)

    card(
        "Real people and sensitive information",
        (
            "The checkbox authorizes Presence to transmit this session to the selected provider. It is not a "
            "substitute for the legal basis, privacy notice, confidentiality agreement, recording permission, "
            "or special-category-data condition that may be required when you process another person’s data. "
            "For real coaching, use only information you are permitted to process and obtain appropriate consent "
            "to recording where required."
        ),
    )

    card(
        "Retention and deletion",
        (
            "You can discard the current in-memory transcript and captured audio below. Closing the application "
            "also ends the local in-memory session. Exported Word/MP3 files are controlled by you and are not "
            "encrypted by Presence. Provider-side retention and deletion are governed by the selected provider "
            "and your account settings."
        ),
    )

    card(
        "Age and purpose",
        (
            "Presence is intended for adults aged 18 or older and for professional coaching practice/reflection. "
            "It does not make employment, credential, medical, legal, financial, or other decisions about a person."
        ),
    )

    links = tk.Frame(content, bg=base.BG)
    links.pack(fill="x", pady=(8, 12))
    self.button(
        links,
        f"Open {selected} data terms ↗",
        lambda: webbrowser.open(_provider_terms_url(self)),
        compact=True,
    ).pack(side="left", padx=(0, 6))
    if selected == provider.GROQ:
        self.button(
            links,
            "Groq DPA ↗",
            lambda: webbrowser.open(GROQ_DPA_URL),
            compact=True,
        ).pack(side="left", padx=(0, 6))
    self.button(
        links,
        "Full project privacy notice ↗",
        lambda: webbrowser.open(PRIVACY_NOTICE_URL),
        compact=True,
    ).pack(side="left")

    footer = tk.Frame(dialog, bg=base.BG)
    footer.pack(fill="x", padx=26, pady=(6, 18))
    self.button(
        footer,
        "Discard current session data",
        lambda: self.clear_session_data(dialog),
        compact=True,
        danger=True,
    ).pack(side="left")
    self.button(footer, "Close", dialog.destroy, compact=True).pack(side="right")

    dialog.bind("<Escape>", lambda _: dialog.destroy())
    dialog.update_idletasks()
    dialog.lift()
    dialog.focus_force()


def privacy_generate_review(self):
    if not self.consent.get():
        parent = getattr(self, "_review_dialog", None) or self
        allowed = messagebox.askyesno(
            "Send transcript for AI review?",
            (
                "Generating the coaching review sends the visible transcript and descriptive session metrics "
                "to the selected AI provider.\n\nAllow this one review request?"
            ),
            parent=parent,
        )
        if not allowed:
            return
    return _original_generate_review(self)


# Keep trace callbacks as bound methods so Tkinter can safely call them.
base.App._privacy_provider_trace = _provider_changed
base.App._privacy_consent_trace = _consent_changed
base.App.__init__ = privacy_init
base.App.poll = privacy_poll
base.App.open_privacy_notice = open_privacy_notice
base.App.clear_session_data = clear_session_data
base.App.generate_coaching_review = privacy_generate_review


if __name__ == "__main__":
    base.App().mainloop()

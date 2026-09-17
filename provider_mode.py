"""Multi-provider layer for Presence Coach.

Adds Google Gemini and Groq without changing the coaching/scenario/review layers.
Gemini continues to use the realtime Live API. Groq uses a turn-based pipeline:
Whisper STT -> chat completion -> Orpheus TTS.
"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from groq import Groq

import practice_review as review
from coaching import SYSTEM_PROMPT
from groq_engine import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_STT_MODEL,
    DEFAULT_TTS_MODEL,
    DEFAULT_VOICE,
    GroqEngine,
)
from reviewer import build_review_prompt
from scenarios import build_coachee_prompt, scenario_kickoff


base = review.base
_original_init = base.App.__init__
_original_start = base.App.start
_original_api_help = base.App.api_help
_original_forget_key = base.App.forget_key
_original_generate_review = base.App.generate_coaching_review

GEMINI = "Google Gemini"
GROQ = "Groq"
GROQ_KEY_URL = "https://console.groq.com/keys"
GEMINI_KEY_URL = "https://aistudio.google.com/apikey"


def provider_init(self):
    _original_init(self)

    self.provider = tk.StringVar(master=self, value=GEMINI)
    self.groq_key = tk.StringVar(master=self)
    self.groq_model = tk.StringVar(master=self, value=DEFAULT_CHAT_MODEL)
    self.groq_stt_model = tk.StringVar(master=self, value=DEFAULT_STT_MODEL)
    self.groq_voice = tk.StringVar(master=self, value=DEFAULT_VOICE)
    self.provider_consent_text = tk.StringVar(master=self)

    try:
        self.groq_key.set(base.keyring.get_password("PresenceCoach", "groq") or "")
    except Exception:
        pass

    _inject_provider_settings(self)
    _wire_provider_consent(self)
    self.provider.trace_add("write", lambda *_: _update_provider_ui(self))
    _update_provider_ui(self)


def _settings_content(self):
    wraps = [
        child for child in self.settings.grid_slaves(row=1, column=0)
        if isinstance(child, tk.Frame)
    ]
    if not wraps:
        return None
    wrap = wraps[0]
    canvas = next((c for c in wrap.winfo_children() if isinstance(c, tk.Canvas)), None)
    if not canvas:
        return None
    return next((c for c in canvas.winfo_children() if isinstance(c, tk.Frame)), None)


def _inject_provider_settings(self):
    content = _settings_content(self)
    if content is None:
        return

    frames = [child for child in content.winfo_children() if isinstance(child, tk.Frame)]
    if len(frames) < 2:
        return
    self._gemini_connection_frame = frames[0]
    self._settings_session_frame = frames[1]

    provider_card = tk.Frame(
        content,
        bg=base.PANEL,
        highlightbackground=base.BORDER,
        highlightthickness=1,
        padx=18,
        pady=16,
    )
    provider_card.pack(
        fill="x",
        padx=22,
        pady=(6, 12),
        before=self._gemini_connection_frame,
    )
    self.label(provider_card, "AI provider", 12, base.INK, "bold").pack(anchor="w")
    self.label(
        provider_card,
        "Choose the cloud provider for the next session.",
        8,
        base.MUTED,
    ).pack(anchor="w", pady=(2, 8))
    provider_combo = ttk.Combobox(
        provider_card,
        textvariable=self.provider,
        values=[GEMINI, GROQ],
        state="readonly",
        style="Presence.TCombobox",
    )
    provider_combo.pack(fill="x")
    self._provider_combo = provider_combo

    groq_card = tk.Frame(
        content,
        bg=base.PANEL,
        highlightbackground=base.BORDER,
        highlightthickness=1,
        padx=18,
        pady=16,
    )
    self._groq_connection_frame = groq_card

    head = tk.Frame(groq_card, bg=base.PANEL)
    head.pack(fill="x", pady=(0, 8))
    self.label(head, "Groq connection", 12, base.INK, "bold").pack(side="left")
    self.button(head, "How to get a key ↗", self.api_help, compact=True).pack(side="right")

    self.label(groq_card, "Groq API key", 9, base.MUTED).pack(anchor="w")
    self._groq_key_entry = ttk.Entry(
        groq_card,
        textvariable=self.groq_key,
        show="•",
        style="Presence.TEntry",
    )
    self._groq_key_entry.pack(fill="x", pady=(4, 10))

    for label, variable, values in [
        (
            "Conversation model",
            self.groq_model,
            ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"],
        ),
        (
            "Speech recognition",
            self.groq_stt_model,
            ["whisper-large-v3-turbo", "whisper-large-v3"],
        ),
        (
            "English voice",
            self.groq_voice,
            ["troy", "austin", "daniel", "autumn", "diana", "hannah"],
        ),
    ]:
        self.label(groq_card, label, 9, base.MUTED).pack(anchor="w", pady=(5, 0))
        combo = ttk.Combobox(
            groq_card,
            textvariable=variable,
            values=values,
            state="readonly",
            style="Presence.TCombobox",
        )
        combo.pack(fill="x", pady=(3, 5))

    self.label(
        groq_card,
        "Groq Whisper and the LLM are multilingual. Current Orpheus voice output is English-only. "
        "The existing ‘Remember key’ option stores the selected provider key in Windows Credential Manager.",
        8,
        base.MUTED,
    ).pack(anchor="w", pady=(9, 0))


def _wire_provider_consent(self):
    if not hasattr(self, "consent_bar"):
        return
    check = next(
        (child for child in self.consent_bar.winfo_children() if isinstance(child, tk.Checkbutton)),
        None,
    )
    if check:
        check.configure(textvariable=self.provider_consent_text)


def _update_provider_ui(self):
    selected = self.provider.get() if hasattr(self, "provider") else GEMINI
    if selected == GROQ:
        self.provider_consent_text.set(
            "Allow this session to use GroqCloud  •  API usage is subject to your Groq plan and limits"
        )
        if hasattr(self, "_gemini_connection_frame"):
            self._gemini_connection_frame.pack_forget()
        if hasattr(self, "_groq_connection_frame") and not self._groq_connection_frame.winfo_manager():
            self._groq_connection_frame.pack(
                fill="x",
                padx=22,
                pady=(6, 12),
                before=self._settings_session_frame,
            )
    else:
        self.provider_consent_text.set(
            "Allow this session to use Google Gemini  •  API usage may be billed"
        )
        if hasattr(self, "_groq_connection_frame"):
            self._groq_connection_frame.pack_forget()
        if hasattr(self, "_gemini_connection_frame") and not self._gemini_connection_frame.winfo_manager():
            self._gemini_connection_frame.pack(
                fill="x",
                padx=22,
                pady=(6, 12),
                before=self._settings_session_frame,
            )


def provider_forget_key(self):
    if hasattr(self, "provider") and self.provider.get() == GROQ:
        try:
            base.keyring.delete_password("PresenceCoach", "groq")
        except base.keyring.errors.PasswordDeleteError:
            pass
        except Exception:
            messagebox.showerror(
                "Key storage",
                "Could not delete the saved Groq key. Check Windows Credential Manager.",
            )
            return
        self.groq_key.set("")
        self.remember.set(False)
        return
    return _original_forget_key(self)


def provider_api_help(self):
    settings_visible = (
        hasattr(self, "settings")
        and self.settings.winfo_exists()
        and self.settings.state() != "withdrawn"
    )
    parent = self.settings if settings_visible else self

    dialog = tk.Toplevel(parent)
    dialog.title("Connect Presence to an AI provider")
    dialog.configure(bg=base.BG)
    dialog.geometry("650x620")
    dialog.resizable(False, False)
    dialog.transient(parent)

    self.label(dialog, "Connect Presence", 19, base.INK, "bold").pack(
        anchor="w", padx=24, pady=(22, 4)
    )
    self.label(
        dialog,
        "Presence supports Google Gemini and Groq. Keep both keys private.",
        9,
        base.MUTED,
    ).pack(anchor="w", padx=24, pady=(0, 14))

    def key_card(title, subtitle, steps, button_text, url, accent):
        card = tk.Frame(
            dialog,
            bg=base.PANEL,
            highlightbackground=base.BORDER,
            highlightthickness=1,
            padx=16,
            pady=13,
        )
        card.pack(fill="x", padx=24, pady=6)
        self.label(card, title, 12, accent, "bold").pack(anchor="w")
        self.label(card, subtitle, 8, base.MUTED).pack(anchor="w", pady=(2, 8))
        for number, text in enumerate(steps, 1):
            row = tk.Frame(card, bg=base.PANEL)
            row.pack(fill="x", pady=2)
            tk.Label(
                row,
                text=str(number),
                width=2,
                bg=base.SURFACE_2,
                fg=accent,
                font=("Segoe UI", 8, "bold"),
            ).pack(side="left", padx=(0, 8))
            self.label(row, text, 9, base.INK).pack(side="left")
        self.button(
            card,
            button_text,
            lambda: webbrowser.open(url),
            primary=(title == "Google Gemini"),
            compact=True,
        ).pack(fill="x", pady=(10, 0))

    key_card(
        "Google Gemini",
        "Gemini Live provides native realtime audio in and out.",
        [
            "Sign in to Google AI Studio.",
            "Open the API Keys page and create a key.",
            "Copy the key and paste it into Presence → Settings.",
        ],
        "Open Gemini API Keys ↗",
        GEMINI_KEY_URL,
        base.AMBER,
    )
    key_card(
        "Groq",
        "Groq uses Whisper STT, a Groq-hosted LLM, and Orpheus TTS.",
        [
            "Sign in to GroqCloud Console.",
            "Open API Keys and choose Create API Key.",
            "Name it Presence Coach, copy it, and paste it into Settings.",
        ],
        "Open Groq API Keys ↗",
        GROQ_KEY_URL,
        base.CYAN,
    )

    self.label(
        dialog,
        "Never place API keys in GitHub, screenshots, transcripts, or shared messages.",
        8,
        base.MUTED,
    ).pack(pady=(8, 4))
    self.button(dialog, "Close", dialog.destroy, compact=True).pack(pady=(5, 16))
    dialog.bind("<Escape>", lambda _: dialog.destroy())
    dialog.update_idletasks()
    dialog.lift()
    dialog.focus_force()


def provider_start(self):
    if not hasattr(self, "provider") or self.provider.get() != GROQ:
        return _original_start(self)

    if self.engine and self.engine.is_alive():
        return
    key = self.groq_key.get().strip()
    if not key:
        self.open_settings()
        messagebox.showinfo(
            "Connect Groq",
            "Enter your Groq API key in Settings. Use ‘How to get a key’ for the direct GroqCloud link.",
            parent=self.settings,
        )
        return
    if not self.consent.get():
        messagebox.showinfo(
            "Before we begin",
            "Enable the GroqCloud consent checkbox below the session controls.",
        )
        return

    try:
        pause, threshold = float(self.pause.get()), float(self.threshold.get())
        if not 1 <= pause <= 60 or not .001 <= threshold <= .5:
            raise ValueError()
    except ValueError:
        messagebox.showerror("Settings", "Use a pause from 1–60 seconds and threshold from 0.001–0.5.")
        return

    if not self.confirm_unsaved():
        return

    if getattr(self, "practice_mode", "coachee") == "coach":
        review._clear_review_state(self)

    if self.remember.get():
        try:
            base.keyring.set_password("PresenceCoach", "groq", key)
        except Exception:
            messagebox.showwarning(
                "Key storage",
                "Could not remember the Groq key securely. It will remain in memory for this run.",
            )

    self.transcript = base.Transcript()
    self.dirty = False
    self.render()
    self.muted.set(False)
    self.hold.set(False)
    self.state.set("Connecting…")
    self.connection_state.set("●  Connecting · Groq")

    english_voice_constraint = (
        "\n\nPROVIDER VOICE CONSTRAINT\nThis Groq session currently uses English-only Orpheus TTS. "
        "Understand multilingual user speech when possible, but produce spoken responses in natural English."
    )

    if getattr(self, "practice_mode", "coachee") == "coach":
        if not self.current_scenario:
            self.open_scenario_chooser()
            return
        prompt = build_coachee_prompt(self.current_scenario) + english_voice_constraint
        input_role = "Coach"
        output_role = "Coachee"
        kickoff = scenario_kickoff(self.current_scenario)
        response_status = f"{self.ai_speaker_name} is thinking"
        self.display_state.set(f"Connecting to {self.ai_speaker_name}")
        self.display_hint.set("Preparing the Groq practice conversation.")
    else:
        prompt = SYSTEM_PROMPT + english_voice_constraint
        input_role = "Coachee"
        output_role = "Coach"
        kickoff = None
        response_status = "Reflecting"
        self.display_state.set("Connecting")
        self.display_hint.set("Preparing your coaching space with Groq.")

    self.engine = GroqEngine(
        key,
        self.groq_model.get(),
        self.groq_voice.get(),
        self.devices.get(self.mic.get()),
        self.devices.get(self.speaker.get()),
        self.events,
        pause,
        threshold,
        system_prompt=prompt,
        input_role=input_role,
        output_role=output_role,
        kickoff=kickoff,
        response_status=response_status,
        stt_model=self.groq_stt_model.get(),
        tts_model=DEFAULT_TTS_MODEL,
    )
    self.start_button.configure(state="disabled")
    self.end_button.configure(state="normal")
    self.engine.start()


def provider_generate_review(self):
    if not hasattr(self, "provider") or self.provider.get() != GROQ:
        return _original_generate_review(self)

    if not self.transcript.rows:
        messagebox.showinfo("Review", "There is no practice transcript to review.")
        return
    key = self.groq_key.get().strip()
    if not key:
        messagebox.showinfo("Review", "A Groq API key is required to generate the review.")
        return

    level = self.practice_review_level.get().upper()
    metrics = review._current_metrics(self)
    rows = list(self.transcript.rows)
    scenario = self.current_scenario
    model = self.groq_model.get()
    prompt = build_review_prompt(level, rows, metrics, scenario)

    self._review_generate_button.configure(state="disabled", text="Reviewing…")
    review._set_review_output(
        self,
        f"Reviewing this transcript against the {level} developmental lens using Groq…\n\n"
        "The live coachee session is already closed; the reviewer is a separate model call.",
    )

    def worker():
        try:
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a rigorous developmental reviewer of professional coaching practice. Follow the requested evidence boundaries exactly.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=.2,
                max_completion_tokens=5000,
            )
            text = (response.choices[0].message.content or "").strip()
            if not text:
                raise RuntimeError("Groq returned an empty review.")
            self._review_queue.put(("ok", text))
        except Exception as exc:
            self._review_queue.put(("error", str(exc)))

    threading.Thread(target=worker, daemon=True).start()
    self.after(120, self._poll_review_result)


base.App.__init__ = provider_init
base.App.start = provider_start
base.App.api_help = provider_api_help
base.App.forget_key = provider_forget_key
base.App.generate_coaching_review = provider_generate_review


if __name__ == "__main__":
    base.App().mainloop()

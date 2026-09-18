"""Post-session review UI layered on top of Coach Practice mode."""
from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

import practice_mode as practice
from reviewer import calculate_metrics, format_duration, generate_review


base = practice.base
_original_init = base.App.__init__
_original_start = base.App.start
_original_animate = base.App.animate
_original_select_coachee_mode = base.App.select_coachee_mode
_original_select_scenario = base.App.select_scenario


def review_init(self):
    # Build the real Tk root first; Tk variables cannot safely exist before this.
    _original_init(self)

    self.practice_session_started_at = None
    self.practice_session_ended_at = None
    self.practice_review_shown = False
    self.practice_review_text = ""
    self.practice_review_level = tk.StringVar(master=self, value="PCC")
    self._review_queue = queue.Queue()
    self._review_dialog = None
    self._review_output = None
    self._review_generate_button = None
    self._review_export_button = None
    self._review_started_at = None
    self._review_last_elapsed = -1

    self.review_button = self.button(
        self.header,
        "Review",
        self.show_session_review,
        compact=True,
    )
    self.review_button.pack(side="right", padx=(4, 0), pady=8)
    self.review_button.configure(state="disabled")


def _clear_review_state(self):
    self.practice_session_started_at = None
    self.practice_session_ended_at = None
    self.practice_review_shown = False
    self.practice_review_text = ""
    self._review_started_at = None
    self._review_last_elapsed = -1
    if hasattr(self, "review_button"):
        self.review_button.configure(state="disabled")


def review_select_coachee_mode(self, dialog=None):
    result = _original_select_coachee_mode(self, dialog)
    _clear_review_state(self)
    return result


def review_select_scenario(self, scenario, dialog=None):
    result = _original_select_scenario(self, scenario, dialog)
    _clear_review_state(self)
    return result


def review_start(self):
    if getattr(self, "practice_mode", "coachee") == "coach":
        _clear_review_state(self)
    return _original_start(self)


def _current_metrics(self):
    end = self.practice_session_ended_at or time.monotonic()
    start = self.practice_session_started_at or end
    return calculate_metrics(self.transcript.rows, max(0, end - start))


def review_animate(self):
    _original_animate(self)

    if getattr(self, "practice_mode", "coachee") != "coach":
        return

    engine = self.engine
    live = bool(engine and engine.is_alive() and not engine.stopping.is_set())
    if live and self.practice_session_started_at is None:
        self.practice_session_started_at = time.monotonic()

    if (
        self.state.get() == "Session complete"
        and self.transcript.rows
        and not self.practice_review_shown
    ):
        self.practice_session_ended_at = time.monotonic()
        self.practice_review_shown = True
        if hasattr(self, "review_button"):
            self.review_button.configure(state="normal")
        self.after(300, self.show_session_review)


def _metric_row(self, parent, label, value, note=None):
    row = tk.Frame(parent, bg=base.PANEL)
    row.pack(fill="x", pady=2)
    self.label(row, label, 9, base.MUTED).pack(side="left")
    self.label(row, value, 10, base.INK, "bold").pack(side="right")
    if note:
        tk.Label(
            parent,
            text=note,
            bg=base.PANEL,
            fg="#61748b",
            font=("Segoe UI", 7),
            justify="left",
            anchor="w",
            wraplength=238,
        ).pack(fill="x", anchor="w", pady=(0, 2))


def _close_review_dialog(self):
    dialog = self._review_dialog
    if dialog and dialog.winfo_exists():
        dialog.destroy()
    self._review_dialog = None
    self._review_output = None
    self._review_generate_button = None
    self._review_export_button = None


def _make_scrollable_review_sidebar(self, parent):
    """Create a fixed-width review sidebar that can scroll on scaled/small displays."""
    shell = tk.Frame(
        parent,
        bg=base.PANEL,
        highlightbackground=base.BORDER,
        highlightthickness=1,
        width=315,
    )
    shell.pack(side="left", fill="y", padx=(0, 12))
    shell.pack_propagate(False)

    canvas = tk.Canvas(
        shell,
        bg=base.PANEL,
        highlightthickness=0,
        bd=0,
        width=289,
    )
    scrollbar = tk.Scrollbar(shell, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    content = tk.Frame(canvas, bg=base.PANEL, padx=18, pady=14)
    window_id = canvas.create_window((0, 0), window=content, anchor="nw")

    def sync_scrollregion(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def fit_width(event):
        # Keep a little room for the vertical scrollbar.
        canvas.itemconfigure(window_id, width=max(250, event.width))

    content.bind("<Configure>", sync_scrollregion)
    canvas.bind("<Configure>", fit_width)

    # Mouse wheel works when the pointer is over the sidebar itself. The visible
    # scrollbar remains available at all times for child widgets and high DPI setups.
    canvas.bind(
        "<MouseWheel>",
        lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
    )

    return content


def show_session_review(self):
    if getattr(self, "practice_mode", "coachee") != "coach" or not self.transcript.rows:
        return

    if self._review_dialog and self._review_dialog.winfo_exists():
        self._review_dialog.deiconify()
        self._review_dialog.lift()
        self._review_dialog.focus_force()
        return

    metrics = _current_metrics(self)
    dialog = tk.Toplevel(self)
    self._review_dialog = dialog
    dialog.title("Coach Practice • Session Review")
    dialog.configure(bg=base.BG)
    dialog.geometry("940x820")
    dialog.minsize(800, 680)
    dialog.transient(self)

    header = tk.Frame(dialog, bg=base.BG)
    header.pack(fill="x", padx=26, pady=(22, 8))
    self.label(header, "SESSION COMPLETE", 18, base.AMBER, "bold").pack(side="left")
    self.button(header, "Close", self._close_review_dialog, compact=True).pack(side="right")

    scenario = getattr(self, "current_scenario", None)
    if scenario:
        name = getattr(self, "ai_speaker_name", "Practice client")
        self.label(
            dialog,
            f"Coach Practice with {name}  •  {scenario.get('environment', '')}",
            9,
            base.MUTED,
        ).pack(anchor="w", padx=26, pady=(0, 12))

    body = tk.Frame(dialog, bg=base.BG)
    body.pack(fill="both", expand=True, padx=26, pady=(0, 18))

    # The left sidebar used to be a fixed non-scrollable frame. At 125%/150%
    # Windows scaling its lower controls were clipped. Keep the same visual style
    # but make the content independently scrollable.
    left = _make_scrollable_review_sidebar(self, body)

    self.label(left, "Session metrics", 12, base.INK, "bold").pack(anchor="w", pady=(0, 8))
    _metric_row(self, left, "Duration", format_duration(metrics.duration_seconds))
    _metric_row(
        self,
        left,
        "Coach / Coachee share",
        f"{metrics.coach_share_pct}% / {metrics.coachee_share_pct}%",
        "Estimated from transcript word count, not measured audio time.",
    )
    _metric_row(self, left, "Coach turns", str(metrics.coach_turns))
    _metric_row(self, left, "Coachee turns", str(metrics.coachee_turns))
    _metric_row(
        self,
        left,
        "Coach questions",
        str(metrics.coach_questions),
        "Based on question marks in provider transcription.",
    )
    _metric_row(self, left, "Stacked-question turns", str(metrics.stacked_question_turns))
    _metric_row(self, left, "Avg coach turn", f"{metrics.average_coach_words:.1f} words")
    _metric_row(self, left, "Longest coach turn", f"{metrics.longest_coach_turn_words} words")
    _metric_row(self, left, "Interruption notes", str(metrics.interruptions))

    tk.Frame(left, bg=base.BORDER, height=1).pack(fill="x", pady=(10, 10))
    self.label(left, "Review against", 10, base.INK, "bold").pack(anchor="w", pady=(0, 5))

    for level in ("ACC", "PCC", "MCC"):
        tk.Radiobutton(
            left,
            text=level,
            value=level,
            variable=self.practice_review_level,
            bg=base.PANEL,
            fg=base.INK,
            selectcolor=base.SURFACE_2,
            activebackground=base.PANEL,
            activeforeground=base.INK,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=1)

    # Keep the actions together and above the disclaimer so they stay easy to find.
    self._review_generate_button = self.button(
        left,
        "Generate coaching review",
        self.generate_coaching_review,
        True,
    )
    self._review_generate_button.pack(fill="x", pady=(10, 5))

    self.button(left, "Export transcript", self.save, compact=True).pack(fill="x", pady=3)

    self._review_export_button = self.button(
        left,
        "Export review",
        self.export_coaching_review,
        compact=True,
    )
    self._review_export_button.pack(fill="x", pady=3)
    self._review_export_button.configure(state="normal" if self.practice_review_text else "disabled")

    tk.Label(
        left,
        text=(
            "Developmental AI review only — not an official ICF score, assessment, "
            "credential-readiness decision, or pass/fail result."
        ),
        bg=base.PANEL,
        fg="#71849a",
        font=("Segoe UI", 7),
        justify="left",
        anchor="w",
        wraplength=238,
    ).pack(fill="x", anchor="w", pady=(9, 4))

    right = tk.Frame(
        body,
        bg=base.PANEL,
        highlightbackground=base.BORDER,
        highlightthickness=1,
    )
    right.pack(side="left", fill="both", expand=True)

    review_header = tk.Frame(right, bg=base.PANEL)
    review_header.pack(fill="x", padx=16, pady=(14, 6))
    self.label(review_header, "Coaching review", 12, base.INK, "bold").pack(side="left")
    self.label(review_header, "2025 competencies • 2026 MSR lens", 7, base.MUTED).pack(side="right")

    text_wrap = tk.Frame(right, bg=base.PANEL)
    text_wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    scroll = tk.Scrollbar(text_wrap)
    scroll.pack(side="right", fill="y")
    output = tk.Text(
        text_wrap,
        bg=base.PANEL,
        fg=base.INK,
        insertbackground=base.INK,
        font=("Segoe UI", 9),
        wrap="word",
        relief="flat",
        padx=10,
        pady=10,
        spacing3=4,
        yscrollcommand=scroll.set,
    )
    output.pack(fill="both", expand=True)
    scroll.configure(command=output.yview)
    self._review_output = output

    if self.practice_review_text:
        output.insert("1.0", self.practice_review_text)
    else:
        output.insert(
            "1.0",
            "Choose ACC, PCC, or MCC and generate a developmental review.\n\n"
            "The reviewer receives only the visible Coach/Coachee transcript and local session metrics. "
            "It does not receive the simulated client's hidden scenario context.\n\n"
            "Use the output as practice feedback and discussion material with a qualified mentor coach, "
            "not as a credential result.",
        )
    output.configure(state="disabled")

    dialog.protocol("WM_DELETE_WINDOW", self._close_review_dialog)
    dialog.bind("<Escape>", lambda _: self._close_review_dialog())
    dialog.update_idletasks()
    dialog.lift()
    dialog.focus_force()


def _set_review_output(self, text):
    output = self._review_output
    if not output or not output.winfo_exists():
        return
    output.configure(state="normal")
    output.delete("1.0", "end")
    output.insert("1.0", text)
    output.configure(state="disabled")
    output.see("1.0")


def generate_coaching_review(self):
    if not self.transcript.rows:
        messagebox.showinfo("Review", "There is no practice transcript to review.")
        return

    # Capture all Tk-backed values on the UI thread before starting the worker.
    api_key = self.key.get().strip()
    if not api_key:
        messagebox.showinfo("Review", "A Gemini API key is required to generate the review.")
        return

    level = self.practice_review_level.get().upper()
    metrics = _current_metrics(self)
    rows = list(self.transcript.rows)
    scenario = self.current_scenario

    self._review_started_at = time.monotonic()
    self._review_last_elapsed = -1
    if self._review_generate_button and self._review_generate_button.winfo_exists():
        self._review_generate_button.configure(state="disabled", text="Reviewing… 0s")
    _set_review_output(
        self,
        f"Reviewing this transcript against the {level} developmental lens…\n\n"
        "Presence is asking the reviewer for compact structured findings, then it will build the readable review locally. "
        "Longer transcripts and deeper evidence checks can still take a little time.",
    )

    def worker():
        try:
            result = generate_review(api_key, level, rows, metrics, scenario)
            self._review_queue.put(("ok", result))
        except Exception as exc:
            self._review_queue.put(("error", str(exc)))

    threading.Thread(target=worker, daemon=True).start()
    self.after(120, self._poll_review_result)


def _poll_review_result(self):
    try:
        status, value = self._review_queue.get_nowait()
    except queue.Empty:
        started = getattr(self, "_review_started_at", None)
        if started:
            elapsed = int(max(0, time.monotonic() - started))
            if elapsed != getattr(self, "_review_last_elapsed", -1):
                self._review_last_elapsed = elapsed
                if self._review_generate_button and self._review_generate_button.winfo_exists():
                    self._review_generate_button.configure(text=f"Reviewing… {elapsed}s")
        self.after(120, self._poll_review_result)
        return

    self._review_started_at = None
    self._review_last_elapsed = -1
    if self._review_generate_button and self._review_generate_button.winfo_exists():
        self._review_generate_button.configure(state="normal", text="Generate coaching review")

    if status == "ok":
        self.practice_review_text = value
        _set_review_output(self, value)
        if self._review_export_button and self._review_export_button.winfo_exists():
            self._review_export_button.configure(state="normal")
    else:
        _set_review_output(
            self,
            "Review generation failed. Your transcript is still available.\n\n" + value,
        )
        parent = self
        if self._review_dialog and self._review_dialog.winfo_exists():
            parent = self._review_dialog
        messagebox.showerror(
            "Review generation failed",
            value + "\n\nCheck API key, quota, internet access, and model availability.",
            parent=parent,
        )


def export_coaching_review(self):
    if not self.practice_review_text:
        messagebox.showinfo("Review", "Generate a coaching review first.")
        return

    level = self.practice_review_level.get().upper()
    parent = self
    if self._review_dialog and self._review_dialog.winfo_exists():
        parent = self._review_dialog
    filename = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".txt",
        initialfile=f"Presence-Coach-{level}-practice-review.txt",
        filetypes=[("Text file", "*.txt")],
    )
    if not filename:
        return

    header = (
        "PRESENCE COACH — PRACTICE REVIEW\n"
        f"Developmental lens: {level}\n"
        "AI-generated developmental feedback; not an official ICF assessment or pass/fail result.\n\n"
    )
    try:
        Path(filename).write_text(header + self.practice_review_text + "\n", encoding="utf-8")
    except OSError as exc:
        messagebox.showerror("Export failed", str(exc), parent=parent)


base.App.__init__ = review_init
base.App.start = review_start
base.App.animate = review_animate
base.App.select_coachee_mode = review_select_coachee_mode
base.App.select_scenario = review_select_scenario
base.App.show_session_review = show_session_review
base.App._close_review_dialog = _close_review_dialog
base.App.generate_coaching_review = generate_coaching_review
base.App._poll_review_result = _poll_review_result
base.App.export_coaching_review = export_coaching_review


if __name__ == "__main__":
    base.App().mainloop()

"""A manual session-history screen; saving is always an explicit user action."""
import time
import tkinter as tk
from tkinter import ttk, messagebox

from session_history import SessionHistory
from ui_helpers import fit_window
from reviewer import calculate_metrics


def install(self):
    self.session_history = SessionHistory()
    self.history_button = self.button(self.mode_toolbar, "History", lambda: show_history(self), compact=True)
    self.history_button.pack(side="right", padx=4)


def current_record(self):
    snapshot = getattr(self, "_review_snapshot", None)
    has_review = bool(getattr(self, "practice_review_text", "") and snapshot)
    rows = snapshot["rows"] if has_review else list(self.transcript.rows)
    scenario = snapshot["scenario"] if has_review else getattr(self, "current_scenario", None)
    if has_review:
        duration = snapshot["metrics"].duration_seconds
    else:
        start = getattr(self, "practice_session_started_at", None) or getattr(self.transcript, "started_at", time.monotonic())
        end = getattr(self, "practice_session_ended_at", None) or time.monotonic()
        duration = max(0, round(end-start))
    return dict(mode=getattr(self, "practice_mode", "coachee"), rows=rows,
                review=self.practice_review_text if has_review else "",
                level=self.practice_review_generated_level if has_review else None,
                duration_seconds=duration, scenario=scenario)


def restore_session(self, data):
    import session_export_mode as exports
    review = exports.review
    review._clear_review_state(self)
    self.engine = None
    self.transcript = exports.base.Transcript()
    self.transcript.rows = [tuple(row) for row in data["rows"]]
    self.transcript.boundary = True
    self.practice_mode = data["mode"]
    from scenarios import SCENARIO_BY_ID, prepare_scenario
    saved_scenario = data["scenario"] or {}
    template = SCENARIO_BY_ID.get(saved_scenario.get("id"))
    self.current_scenario = prepare_scenario(template, saved_scenario.get("difficulty", "Experienced"),
                                              saved_scenario.get("practice_focus", "Full session")) if template else None
    self.ai_speaker_name = (data["scenario"] or {}).get("persona", "Practice client").split(",")[0] if data["mode"] == "coach" else "Presence"
    self.mode_button.configure(text="Practise coaching" if data["mode"] == "coach" else "Receive coaching")
    self.practice_session_ended_at = time.monotonic()
    self.practice_session_started_at = self.practice_session_ended_at - data["duration_seconds"]
    if data["level"]:
        self.practice_review_level.set(data["level"])
    self.practice_review_text = data["review"]
    self.practice_review_generated_level = data["level"]
    if data["review"]:
        self._review_snapshot = {"rows": list(self.transcript.rows), "scenario": data["scenario"],
                                   "metrics": calculate_metrics(self.transcript.rows, data["duration_seconds"])}
    self.practice_review_shown = True
    self.dirty = False
    self.audio_exported = True
    self._runtime_error_active = False
    self._safety_alerted = False
    self.muted.set(False)
    self.hold.set(False)
    self.state.set("Saved session")
    self.connection_state.set("●  Saved locally")
    self.consent.set(False)
    self.set_session_controls(False)
    self.review_button.configure(state="normal" if data["mode"] == "coach" and data["rows"] else "disabled")
    self.render()
    if data["mode"] == "coach":
        self.show_session_review()


def show_history(self):
    if getattr(self, "_history_dialog", None) and self._history_dialog.winfo_exists():
        self._history_dialog.lift()
        return
    dialog = tk.Toplevel(self)
    self._history_dialog = dialog
    dialog.title("Presence · Saved sessions")
    dialog.configure(bg="#07111e")
    fit_window(dialog, 900, 620)
    dialog.transient(self)
    self.label(dialog, "Your saved sessions", 22, "#eef5ff", "bold").pack(anchor="w", padx=24, pady=(22, 8))
    tk.Label(dialog, text="Nothing is saved automatically. Save text and reviews on this device; audio is excluded.\n"
        "Local files are readable by people with access to your device. Delete them here when no longer needed.",
        bg=dialog["bg"], fg="#a8b8cc", font=("Segoe UI", 10), justify="left", wraplength=800).pack(anchor="w", padx=24, pady=(0,16))
    wrap = tk.Frame(dialog, bg=dialog["bg"])
    wrap.pack(fill="both", expand=True, padx=24)
    tree = ttk.Treeview(wrap, columns=("date", "title", "mode", "level"), show="headings", selectmode="browse")
    for key, title, width in (("date", "Saved", 180), ("title", "Session", 300), ("mode", "Mode", 160), ("level", "Review", 80)):
        tree.heading(key, text=title)
        tree.column(key, width=width, minwidth=60)
    scroll = ttk.Scrollbar(wrap, command=tree.yview, style="Presence.Vertical.TScrollbar")
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)
    status = tk.StringVar(master=dialog)
    tk.Label(dialog, textvariable=status, bg=dialog["bg"], fg="#a8b8cc", font=("Segoe UI", 10)).pack(anchor="w", padx=24, pady=8)

    def refresh():
        tree.delete(*tree.get_children())
        for item in self.session_history.list_sessions():
            tree.insert("", "end", iid=item["id"], values=(item["saved_at"].replace("T"," ").replace("+00:00", " UTC"), item["title"],
                "Practise coaching" if item["mode"] == "coach" else "Receive coaching", item["level"] or "—"))
        status.set(f"{len(tree.get_children())} saved sessions")

    def unavailable():
        if self.engine and self.engine.is_alive() or getattr(self, "_review_started_at", None) or getattr(self, "_audio_export_in_progress", False):
            messagebox.showinfo("Session in progress", "End the session and wait for review or export to finish first.", parent=dialog)
            return True
        return False

    def save():
        if unavailable(): return
        record = current_record(self)
        if not record["rows"]:
            messagebox.showinfo("Save session", "There is no transcript to save yet.", parent=dialog)
            return
        try:
            identifier = self.session_history.save(**record)
            refresh()
            tree.selection_set(identifier)
            status.set("Saved locally. Your transcript and review can be reopened here.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not save session", str(exc), parent=dialog)

    def open_selected():
        selected = tree.selection()
        if not selected or unavailable(): return
        try:
            data = self.session_history.load(selected[0])
            if not self.confirm_unsaved(): return
            restore_session(self, data)
            dialog.destroy()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not open session", str(exc), parent=dialog)

    def delete():
        selected = tree.selection()
        if selected and messagebox.askyesno("Delete saved session?", "Delete this saved text and review from this device? Exported files are unaffected.", parent=dialog):
            try:
                self.session_history.delete(selected[0])
                refresh()
            except OSError as exc:
                messagebox.showerror("Could not delete session", str(exc), parent=dialog)

    actions = tk.Frame(dialog, bg=dialog["bg"])
    actions.pack(fill="x", padx=24, pady=(4,20))
    self.button(actions, "Save current session locally", save, True).pack(side="left", padx=(0,8))
    self.button(actions, "Open selected", open_selected).pack(side="left", padx=4)
    self.button(actions, "Delete selected", delete, danger=True).pack(side="left", padx=4)
    self.button(actions, "Close", dialog.destroy).pack(side="right")
    tree.bind("<Double-1>", lambda _: open_selected())
    dialog.bind("<Escape>", lambda _: dialog.destroy())
    refresh()

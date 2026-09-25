"""Role-selection and AI coachee practice mode for Presence Coach.

This layer builds on the optimized UI launcher without changing the coaching or
audio transport. It adds two explicit experiences:
- I am a Coachee: existing Presence-as-coach behavior.
- I am a Coach: the user coaches a simulated professional client.
"""
import random
import time
import tkinter as tk
from tkinter import messagebox, ttk

import launch as performance
from scenarios import (
    COACHEE_SCENARIOS,
    DIFFICULTY_LEVELS,
    PRACTICE_FOCI,
    SCENARIO_PACKS,
    build_coachee_prompt,
    prepare_scenario,
    scenario_kickoff,
    scenario_matches,
)

base = performance.base

_original_init = base.App.__init__
_original_start = base.App.start
_original_render = base.App.render
_original_animate = base.App.animate


def _client_name(scenario):
    persona = scenario.get('persona', 'Practice client')
    return persona.split(',', 1)[0].strip() or 'Practice client'


def _center(window, parent, width, height):
    parent.update_idletasks()
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')


def _reset_for_mode(self):
    self.transcript = base.Transcript()
    self.dirty = False
    self.audio_exported = True
    self._safety_alerted = False
    self.level = 0
    self.envelope = 0.0
    self.muted.set(False)
    self.hold.set(False)
    self.connection_state.set('●  Ready')
    self.state.set('Ready when you are')
    self.set_session_controls(False)
    self.render()


def practice_init(self):
    # These must exist before the base constructor calls render/animate-related setup.
    self.practice_mode = 'coachee'
    self.current_scenario = None
    self.ai_speaker_name = 'Presence'

    _original_init(self)

    self.mode_button = self.button(
        self.header,
        'Mode · Coachee',
        self.show_role_chooser,
        compact=True,
    )
    self.mode_button.pack(side='right', padx=(8, 0), pady=8)

    # Make the two-mode choice the first intentional interaction without delaying startup.
    self.after(180, self.show_role_chooser)


def show_role_chooser(self):
    if self.engine and self.engine.is_alive():
        messagebox.showinfo(
            'End the current session first',
            'Finish or end this session before switching between Coach and Coachee modes.',
        )
        return

    dialog = tk.Toplevel(self)
    dialog.title('Choose your Presence mode')
    dialog.configure(bg=base.BG)
    dialog.resizable(False, False)
    dialog.transient(self)
    _center(dialog, self, 780, 520)

    self.label(dialog, 'How would you like to use Presence?', 23, base.INK, 'bold').pack(
        pady=(34, 5)
    )
    self.label(
        dialog,
        'Choose your role for this session.',
        10,
        base.MUTED,
    ).pack(pady=(0, 24))

    cards = tk.Frame(dialog, bg=base.BG)
    cards.pack(fill='both', expand=True, padx=34)

    left = tk.Frame(
        cards,
        bg=base.PANEL,
        highlightbackground=base.BORDER,
        highlightthickness=1,
        padx=24,
        pady=22,
        width=330,
        height=300,
    )
    left.pack(side='left', fill='both', expand=True, padx=(0, 9))
    left.pack_propagate(False)

    self.label(left, 'I AM A COACHEE', 14, base.AMBER, 'bold').pack(anchor='w')
    self.label(left, 'Get coached by Presence', 13, base.INK, 'bold').pack(anchor='w', pady=(14, 8))
    tk.Label(
        left,
        text=(
            'Bring a real topic you want to think through. Presence listens, reflects, '
            'and coaches you using the current professional-coaching experience.'
        ),
        bg=base.PANEL,
        fg=base.MUTED,
        font=('Segoe UI', 10),
        justify='left',
        wraplength=280,
    ).pack(anchor='w')
    self.button(
        left,
        'Continue as Coachee',
        lambda: self.select_coachee_mode(dialog),
        True,
    ).pack(side='bottom', fill='x', pady=(18, 0))

    right = tk.Frame(
        cards,
        bg=base.PANEL,
        highlightbackground=base.AMBER_SOFT,
        highlightthickness=1,
        padx=24,
        pady=22,
        width=330,
        height=300,
    )
    right.pack(side='left', fill='both', expand=True, padx=(9, 0))
    right.pack_propagate(False)

    self.label(right, 'I AM A COACH', 14, base.CYAN, 'bold').pack(anchor='w')
    self.label(right, 'Practice with an AI coachee', 13, base.INK, 'bold').pack(anchor='w', pady=(14, 8))
    tk.Label(
        right,
        text=(
            'Choose a realistic workplace client. The client has hidden context and '
            'reveals it gradually while you conduct the coaching conversation.'
        ),
        bg=base.PANEL,
        fg=base.MUTED,
        font=('Segoe UI', 10),
        justify='left',
        wraplength=280,
    ).pack(anchor='w')
    tk.Label(
        right,
        text='Practice simulation · not a genuine credential-submission client',
        bg=base.PANEL,
        fg='#71849a',
        font=('Segoe UI', 8),
        justify='left',
        wraplength=280,
    ).pack(anchor='w', pady=(12, 0))
    self.button(
        right,
        'Choose a Practice Client',
        lambda: self.open_scenario_chooser(dialog),
        True,
    ).pack(side='bottom', fill='x', pady=(18, 0))

    self.label(
        dialog,
        'You can switch modes later from the Mode button in the top bar.',
        8,
        '#61748b',
    ).pack(pady=(8, 20))

    dialog.bind('<Escape>', lambda _: dialog.destroy())
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)
    dialog.update_idletasks()
    dialog.lift()
    dialog.focus_force()


def select_coachee_mode(self, dialog=None):
    if self.dirty and not self.confirm_unsaved():
        return

    self.practice_mode = 'coachee'
    self.current_scenario = None
    self.ai_speaker_name = 'Presence'
    if hasattr(self, 'mode_button'):
        self.mode_button.configure(text='Mode · Coachee')
    _reset_for_mode(self)

    if dialog and dialog.winfo_exists():
        dialog.destroy()


def open_scenario_chooser(self, role_dialog=None):
    if role_dialog and role_dialog.winfo_exists():
        role_dialog.destroy()

    dialog = tk.Toplevel(self)
    dialog.title('Presence Coach • Scenario Library')
    dialog.configure(bg=base.BG)
    dialog.transient(self)
    dialog.minsize(900, 650)
    _center(dialog, self, 1120, 780)

    search_var = tk.StringVar(master=dialog)
    pack_var = tk.StringVar(master=dialog, value='All packs')
    difficulty_var = tk.StringVar(master=dialog, value='Experienced')
    focus_var = tk.StringVar(master=dialog, value='Full session')
    count_var = tk.StringVar(master=dialog)
    difficulty_note = tk.StringVar(master=dialog)

    difficulty_notes = {
        'Foundation': 'Clearer topic • more openness • lower resistance',
        'Experienced': 'Realistic ambiguity • mixed self-awareness • natural resistance',
        'Advanced': 'Guarded • contradictory • deeper context must be earned',
    }

    header = tk.Frame(dialog, bg=base.BG)
    header.pack(fill='x', padx=28, pady=(22, 8))

    title_wrap = tk.Frame(header, bg=base.BG)
    title_wrap.pack(side='left', fill='x', expand=True)
    self.label(title_wrap, 'Scenario Library', 22, base.INK, 'bold').pack(anchor='w')
    self.label(
        title_wrap,
        'Choose the situation. The client keeps the deeper story hidden.',
        9,
        base.MUTED,
    ).pack(anchor='w', pady=(3, 0))

    self.button(
        header,
        '🎲  Surprise Me',
        lambda: choose_surprise(),
        True,
        compact=True,
    ).pack(side='right', padx=(14, 0))

    filters = tk.Frame(
        dialog,
        bg=base.PANEL,
        highlightbackground=base.BORDER,
        highlightthickness=1,
        padx=16,
        pady=13,
    )
    filters.pack(fill='x', padx=28, pady=(6, 10))

    search_col = tk.Frame(filters, bg=base.PANEL)
    search_col.grid(row=0, column=0, sticky='ew', padx=(0, 10))
    self.label(search_col, 'Search', 8, base.MUTED, 'bold').pack(anchor='w', pady=(0, 4))
    search_entry = ttk.Entry(
        search_col,
        textvariable=search_var,
        style='Presence.TEntry',
    )
    search_entry.pack(fill='x')

    pack_col = tk.Frame(filters, bg=base.PANEL)
    pack_col.grid(row=0, column=1, sticky='ew', padx=5)
    self.label(pack_col, 'Scenario pack', 8, base.MUTED, 'bold').pack(anchor='w', pady=(0, 4))
    pack_combo = ttk.Combobox(
        pack_col,
        textvariable=pack_var,
        values=('All packs',) + SCENARIO_PACKS,
        state='readonly',
        style='Presence.TCombobox',
    )
    pack_combo.pack(fill='x')

    difficulty_col = tk.Frame(filters, bg=base.PANEL)
    difficulty_col.grid(row=0, column=2, sticky='ew', padx=5)
    self.label(difficulty_col, 'Difficulty', 8, base.MUTED, 'bold').pack(anchor='w', pady=(0, 4))
    difficulty_combo = ttk.Combobox(
        difficulty_col,
        textvariable=difficulty_var,
        values=DIFFICULTY_LEVELS,
        state='readonly',
        style='Presence.TCombobox',
    )
    difficulty_combo.pack(fill='x')

    focus_col = tk.Frame(filters, bg=base.PANEL)
    focus_col.grid(row=0, column=3, sticky='ew', padx=(10, 0))
    self.label(focus_col, 'Practice focus', 8, base.MUTED, 'bold').pack(anchor='w', pady=(0, 4))
    focus_combo = ttk.Combobox(
        focus_col,
        textvariable=focus_var,
        values=PRACTICE_FOCI,
        state='readonly',
        style='Presence.TCombobox',
    )
    focus_combo.pack(fill='x')

    for column, weight in enumerate((3, 2, 2, 2)):
        filters.grid_columnconfigure(column, weight=weight)

    meta = tk.Frame(dialog, bg=base.BG)
    meta.pack(fill='x', padx=30, pady=(0, 7))
    self.label(meta, '', 8, base.CYAN).pack_forget()
    count_label = tk.Label(
        meta,
        textvariable=count_var,
        bg=base.BG,
        fg=base.CYAN,
        font=('Segoe UI', 8, 'bold'),
    )
    count_label.pack(side='left')
    difficulty_label = tk.Label(
        meta,
        textvariable=difficulty_note,
        bg=base.BG,
        fg=base.MUTED,
        font=('Segoe UI', 8),
    )
    difficulty_label.pack(side='right')

    wrap = tk.Frame(dialog, bg=base.BG)
    wrap.pack(fill='both', expand=True, padx=20, pady=(0, 18))

    canvas = tk.Canvas(wrap, bg=base.BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(
        wrap,
        orient='vertical',
        command=canvas.yview,
        style='Presence.Vertical.TScrollbar',
    )
    scrollbar.pack(side='right', fill='y')
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side='left', fill='both', expand=True)

    content = tk.Frame(canvas, bg=base.BG)
    window_id = canvas.create_window((0, 0), window=content, anchor='nw')
    canvas.bind('<Configure>', lambda event: canvas.itemconfigure(window_id, width=event.width))
    content.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))

    def filtered_scenarios():
        return [
            scenario
            for scenario in COACHEE_SCENARIOS
            if scenario_matches(
                scenario,
                search_var.get(),
                pack_var.get(),
                focus_var.get(),
            )
        ]

    def session_scenario(scenario):
        return prepare_scenario(
            scenario,
            difficulty=difficulty_var.get(),
            practice_focus=focus_var.get(),
        )

    def choose_scenario(scenario):
        self.select_scenario(session_scenario(scenario), dialog)

    def choose_surprise():
        options = filtered_scenarios()
        if not options:
            options = list(COACHEE_SCENARIOS)
        choose_scenario(random.choice(options))

    def tag(parent, text, accent=False):
        return tk.Label(
            parent,
            text=text,
            bg=base.SURFACE_2,
            fg=base.CYAN if accent else '#8da0b5',
            font=('Segoe UI', 7, 'bold'),
            padx=7,
            pady=3,
        )

    def refresh_cards(*_):
        difficulty_note.set(difficulty_notes.get(difficulty_var.get(), ''))
        for child in content.winfo_children():
            child.destroy()

        scenarios = filtered_scenarios()
        packs = {scenario.get('pack') for scenario in scenarios}
        count_var.set(
            f'{len(scenarios)} scenario{"s" if len(scenarios) != 1 else ""}'
            + (f'  •  {len(packs)} pack{"s" if len(packs) != 1 else ""}' if scenarios else '')
        )

        if not scenarios:
            empty = tk.Frame(
                content,
                bg=base.PANEL,
                highlightbackground=base.BORDER,
                highlightthickness=1,
                padx=24,
                pady=28,
            )
            empty.grid(row=0, column=0, columnspan=2, sticky='ew', padx=8, pady=8)
            self.label(empty, 'No scenarios match these filters.', 12, base.INK, 'bold').pack(anchor='w')
            self.label(
                empty,
                'Try another pack, practice focus, or a broader search.',
                9,
                base.MUTED,
            ).pack(anchor='w', pady=(5, 0))
            return

        for column in range(2):
            content.grid_columnconfigure(column, weight=1, uniform='scenario')

        for index, scenario in enumerate(scenarios):
            row, column = divmod(index, 2)
            card = tk.Frame(
                content,
                bg=base.PANEL,
                highlightbackground=base.BORDER,
                highlightthickness=1,
                padx=17,
                pady=14,
                height=220,
            )
            card.grid(
                row=row,
                column=column,
                sticky='nsew',
                padx=8,
                pady=8,
            )
            card.grid_propagate(False)
            card.grid_columnconfigure(0, weight=1)
            card.grid_rowconfigure(3, weight=1)

            tags = tk.Frame(card, bg=base.PANEL)
            tags.grid(row=0, column=0, sticky='ew')
            tag(tags, scenario.get('pack', 'Professional Coaching'), True).pack(side='left')
            self.label(
                tags,
                scenario['environment'],
                7,
                base.MUTED,
            ).pack(side='right')

            self.label(card, scenario['title'], 12, base.INK, 'bold').grid(
                row=1,
                column=0,
                sticky='w',
                pady=(10, 5),
            )

            problem = tk.Label(
                card,
                text=scenario['visible_problem'],
                bg=base.PANEL,
                fg=base.MUTED,
                font=('Segoe UI', 9),
                justify='left',
                anchor='nw',
                wraplength=430,
            )
            problem.grid(row=2, column=0, sticky='new')

            footer = tk.Frame(card, bg=base.PANEL)
            footer.grid(row=4, column=0, sticky='ew', pady=(10, 0))

            focus_tags = scenario.get('focus', ())[:3]
            focus_wrap = tk.Frame(footer, bg=base.PANEL)
            focus_wrap.pack(side='left', fill='x', expand=True)
            for focus_name in focus_tags:
                tag(focus_wrap, focus_name).pack(side='left', padx=(0, 5))

            self.button(
                footer,
                'Practice',
                lambda s=scenario: choose_scenario(s),
                compact=True,
            ).pack(side='right', padx=(10, 0))

    search_var.trace_add('write', refresh_cards)
    pack_var.trace_add('write', refresh_cards)
    difficulty_var.trace_add('write', refresh_cards)
    focus_var.trace_add('write', refresh_cards)

    def wheel(event):
        units = base.mousewheel_units(event)
        if units:
            canvas.yview_scroll(units, 'units')
            return 'break'
        return None

    # Bind on the dialog rather than globally so scrolling works over cards,
    # labels and controls without leaking the binding into the rest of the app.
    for sequence in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
        dialog.bind(sequence, wheel, add='+')

    def close_dialog():
        dialog.destroy()

    dialog.protocol('WM_DELETE_WINDOW', close_dialog)
    dialog.bind('<Escape>', lambda _: close_dialog())

    refresh_cards()
    dialog.update_idletasks()
    dialog.lift()
    dialog.focus_force()
    search_entry.focus_set()

def select_scenario(self, scenario, dialog=None):
    if self.dirty and not self.confirm_unsaved():
        return

    self.practice_mode = 'coach'
    self.current_scenario = scenario
    self.ai_speaker_name = _client_name(scenario)
    if hasattr(self, 'mode_button'):
        self.mode_button.configure(text='Mode · Coach')

    _reset_for_mode(self)
    self.display_state.set(f'Ready to coach {self.ai_speaker_name}')
    self.display_hint.set(scenario['visible_problem'])

    if dialog and dialog.winfo_exists():
        dialog.destroy()


def practice_start(self):
    if self.practice_mode != 'coach':
        return _original_start(self)

    if self.engine and self.engine.is_alive():
        return

    if not self.current_scenario:
        self.open_scenario_chooser()
        return

    if not self.key.get().strip():
        self.open_settings()
        messagebox.showinfo(
            'Connect your practice client',
            'Enter your Gemini API key in Settings. Use “How to get a key” for step-by-step help.',
            parent=self.settings,
        )
        return

    if not self.consent.get():
        messagebox.showinfo(
            'Before we begin',
            'Enable “Allow this session to use Google Gemini” below the session controls.',
        )
        return

    try:
        pause, threshold = float(self.pause.get()), float(self.threshold.get())
        if not 1 <= pause <= 60 or not .001 <= threshold <= .5:
            raise ValueError()
    except ValueError:
        messagebox.showerror('Settings', 'Use a pause from 1–60 seconds and threshold from 0.001–0.5.')
        return

    if not self.confirm_unsaved():
        return

    if self.remember.get():
        try:
            base.keyring.set_password('PresenceCoach', 'gemini', self.key.get().strip())
        except Exception:
            messagebox.showwarning(
                'Key storage',
                'Could not remember the key securely. It will remain in memory for this run.',
            )

    self.transcript = base.Transcript()
    self.dirty = False
    self.audio_exported = False
    self._safety_alerted = False
    self.render()
    self.muted.set(False)
    self.hold.set(False)
    self.state.set('Connecting…')
    self.connection_state.set('●  Connecting')
    self.display_state.set(f'Connecting to {self.ai_speaker_name}')
    self.display_hint.set('Preparing the practice conversation.')

    scenario = self.current_scenario
    self.engine = base.LiveEngine(
        self.key.get().strip(),
        self.model.get().strip(),
        self.voice.get(),
        self.devices.get(self.mic.get()),
        self.devices.get(self.speaker.get()),
        self.events,
        pause,
        threshold,
        system_prompt=build_coachee_prompt(scenario),
        input_role='Coach',
        output_role='Coachee',
        kickoff=scenario_kickoff(scenario),
        response_status=f'{self.ai_speaker_name} is thinking',
    )
    self.start_button.configure(state='disabled')
    self.end_button.configure(state='normal')
    self.engine.start()


def practice_render(self):
    if getattr(self, 'practice_mode', 'coachee') != 'coach':
        return _original_render(self)

    bottom = self.log.yview()[1] >= .98
    position = self.log.yview()[0]
    self.log.configure(state='normal')
    self.log.delete('1.0', 'end')

    scenario = self.current_scenario
    if not self.transcript.rows:
        if scenario:
            name = _client_name(scenario)
            self.log.insert('end', 'PRACTICE CLIENT\n', 'Coachee')
            self.log.insert('end', f'{name}  ·  {scenario["environment"]}\n', 'body')
            library_meta = (
                f'{scenario.get("pack", "Professional Coaching")}  ·  '
                f'{scenario.get("difficulty", "Experienced")}'
            )
            if scenario.get("practice_focus", "Full session") != "Full session":
                library_meta += f'  ·  Focus: {scenario["practice_focus"]}'
            self.log.insert('end', library_meta + '\n\n', 'body')
            self.log.insert('end', scenario['visible_problem'] + '\n\n', 'body')
            self.log.insert(
                'end',
                'You are the coach. The client has additional private context that is not shown to you. '
                'Begin naturally and establish the coaching conversation.\n',
                'body',
            )
        else:
            self.log.insert('end', 'Choose a practice client to begin.\n', 'body')

    for stamp, role, text in self.transcript.rows:
        if role == 'Coach':
            name = 'YOU · COACH'
        elif role == 'Coachee':
            name = _client_name(scenario).upper() if scenario else 'COACHEE'
        else:
            name = role.upper()
        self.log.insert('end', f'{name}   {stamp}\n', role)
        self.log.insert('end', text.strip() + '\n\n', 'body')

    self.log.configure(state='disabled')
    if bottom:
        self.log.see('end')
    else:
        self.log.yview_moveto(position)


def practice_animate(self):
    # The optimized animation does the graphics and schedules the next frame.
    _original_animate(self)

    if getattr(self, 'practice_mode', 'coachee') != 'coach' or not self.current_scenario:
        return

    name = self.ai_speaker_name
    engine = self.engine
    live = bool(engine and engine.is_alive() and not engine.stopping.is_set())
    playing = bool(live and getattr(engine, 'playback_until', 0) > time.monotonic())
    raw_state = self.state.get()

    if playing:
        self.display_state.set(f'{name} is speaking')
        self.display_hint.set('Listen for the person, not just the problem.')
    elif live and self.muted.get():
        self.display_state.set('Microphone muted')
        self.display_hint.set('Unmute when you are ready to continue coaching.')
    elif live and raw_state.startswith('Listening'):
        self.display_state.set(f'{name} is listening')
        self.display_hint.set('You are the coach. Stay with the client’s agenda.')
    elif live:
        self.display_state.set(f'{name} is thinking')
        self.display_hint.set('Give the client space to think.')
    elif raw_state.startswith('Connecting'):
        self.display_state.set(f'Connecting to {name}')
        self.display_hint.set('Preparing the practice conversation.')
    elif raw_state == 'Session complete':
        self.display_state.set('Practice session complete')
        self.display_hint.set('Your Coach / Coachee transcript is ready to review or export.')
    else:
        self.display_state.set(f'Ready to coach {name}')
        self.display_hint.set(self.current_scenario['visible_problem'])


base.App.__init__ = practice_init
base.App.show_role_chooser = show_role_chooser
base.App.select_coachee_mode = select_coachee_mode
base.App.open_scenario_chooser = open_scenario_chooser
base.App.select_scenario = select_scenario
base.App.start = practice_start
base.App.render = practice_render
base.App.animate = practice_animate


if __name__ == '__main__':
    base.App().mainloop()

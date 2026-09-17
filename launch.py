"""Presence Coach launcher with responsive orb and two-sided practice modes."""
import math
import time
import webbrowser
import tkinter as tk
from tkinter import messagebox

import app as base
from coaching import SYSTEM_PROMPT
from scenarios import COACHEE_SCENARIOS, build_coachee_prompt, scenario_kickoff


class PresenceApp(base.App):
    def make_ui(self):
        base.App.make_ui(self)

        self.mode = tk.StringVar(value='coachee')
        self.active_scenario = COACHEE_SCENARIOS[0]
        self._coach_mode_seen = False

        mode_wrap = tk.Frame(self.header, bg=base.BG)
        mode_wrap.pack(side='left', padx=(34, 0), pady=(4, 0))

        tk.Label(
            mode_wrap,
            text='ROLE',
            bg=base.BG,
            fg=base.MUTED,
            font=('Segoe UI', 8, 'bold'),
        ).pack(side='left', padx=(0, 8))

        self.coachee_mode_button = self.button(
            mode_wrap,
            'I am a Coachee',
            lambda: self.select_mode('coachee'),
            compact=True,
        )
        self.coachee_mode_button.pack(side='left', padx=2)

        self.coach_mode_button = self.button(
            mode_wrap,
            'I am a Coach',
            lambda: self.select_mode('coach'),
            compact=True,
        )
        self.coach_mode_button.pack(side='left', padx=2)

        self.case_title = tk.StringVar()
        self.case_detail = tk.StringVar()
        self.case_bar = tk.Frame(
            self.stage,
            bg=base.PANEL,
            highlightbackground=base.BORDER,
            highlightthickness=1,
            padx=14,
            pady=10,
        )

        case_text = tk.Frame(self.case_bar, bg=base.PANEL)
        case_text.pack(side='left', fill='x', expand=True)
        tk.Label(
            case_text,
            text='SIMULATED COACHEE • PRACTICE',
            bg=base.PANEL,
            fg=base.CYAN,
            font=('Segoe UI', 8, 'bold'),
        ).pack(anchor='w')
        tk.Label(
            case_text,
            textvariable=self.case_title,
            bg=base.PANEL,
            fg=base.INK,
            font=('Segoe UI', 10, 'bold'),
        ).pack(anchor='w', pady=(2, 0))
        tk.Label(
            case_text,
            textvariable=self.case_detail,
            bg=base.PANEL,
            fg=base.MUTED,
            font=('Segoe UI', 8),
            wraplength=650,
            justify='left',
        ).pack(anchor='w', pady=(2, 0))

        self.button(
            self.case_bar,
            'Change scenario',
            self.show_scenario_picker,
            compact=True,
        ).pack(side='right', padx=(12, 0))

        self._refresh_scenario_text()
        self._update_mode_visuals()

    def _set_segment_style(self, button, selected):
        if selected:
            button.configure(
                bg=base.AMBER,
                fg=base.BG,
                activebackground='#ffd094',
                activeforeground=base.BG,
            )
        else:
            button.configure(
                bg=base.SURFACE_2,
                fg=base.INK,
                activebackground='#172a40',
                activeforeground=base.INK,
            )

    def _update_mode_visuals(self):
        coach_mode = self.mode.get() == 'coach'
        self._set_segment_style(self.coachee_mode_button, not coach_mode)
        self._set_segment_style(self.coach_mode_button, coach_mode)

        if coach_mode and not self.focused:
            if not self.case_bar.winfo_manager():
                self.case_bar.pack(
                    fill='x',
                    before=self.orb,
                    padx=(0, 12),
                    pady=(0, 8),
                )
            self.display_state.set('Ready to practice')
            self.display_hint.set('Coach the person behind the presenting problem.')
        else:
            self.case_bar.pack_forget()
            self.display_state.set('Ready when you are')
            self.display_hint.set('A quiet space for whatever matters.')

    def _refresh_scenario_text(self):
        scenario = self.active_scenario
        self.case_title.set(f"{scenario['title']}  •  {scenario['environment']}")
        self.case_detail.set(scenario['visible_problem'])

    def select_mode(self, mode):
        if mode not in ('coach', 'coachee') or mode == self.mode.get():
            return

        if self.engine and self.engine.is_alive():
            messagebox.showinfo(
                'End the current session first',
                'Your role cannot be changed while a coaching session is live.',
                parent=self,
            )
            return

        if self.transcript.rows:
            if not self.confirm_unsaved():
                return
            self.transcript = base.Transcript()
            self.dirty = False

        self.mode.set(mode)
        self._update_mode_visuals()
        self.render()

        if mode == 'coach' and not self._coach_mode_seen:
            self._coach_mode_seen = True
            self.after(80, self.show_scenario_picker)

    def show_scenario_picker(self):
        if self.engine and self.engine.is_alive():
            messagebox.showinfo(
                'Session in progress',
                'End the current session before changing the simulated coachee.',
                parent=self,
            )
            return

        dialog = tk.Toplevel(self)
        dialog.title('Choose a simulated coachee')
        dialog.configure(bg=base.BG)
        dialog.geometry('820x590')
        dialog.minsize(760, 540)
        dialog.transient(self)

        top = tk.Frame(dialog, bg=base.BG)
        top.pack(fill='x', padx=24, pady=(22, 12))
        self.label(top, 'Choose a practice scenario', 18, base.INK, 'bold').pack(anchor='w')
        self.label(
            top,
            'The coach sees the presenting situation. The simulated coachee keeps deeper '
            'tensions private until your coaching creates space for them.',
            9,
            base.MUTED,
        ).pack(anchor='w', pady=(5, 0))

        body = tk.Frame(dialog, bg=base.BG)
        body.pack(fill='both', expand=True, padx=24, pady=(0, 16))

        left = tk.Frame(
            body,
            bg=base.PANEL,
            highlightbackground=base.BORDER,
            highlightthickness=1,
            width=300,
        )
        left.pack(side='left', fill='y')
        left.pack_propagate(False)

        listbox = tk.Listbox(
            left,
            bg=base.PANEL,
            fg=base.INK,
            selectbackground=base.SURFACE_2,
            selectforeground=base.AMBER,
            activestyle='none',
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            font=('Segoe UI', 10),
            exportselection=False,
        )
        listbox.pack(fill='both', expand=True, padx=10, pady=10)

        for scenario in COACHEE_SCENARIOS:
            listbox.insert('end', scenario['title'])

        right = tk.Frame(
            body,
            bg=base.PANEL,
            highlightbackground=base.BORDER,
            highlightthickness=1,
            padx=20,
            pady=18,
        )
        right.pack(side='left', fill='both', expand=True, padx=(12, 0))

        preview_env = tk.StringVar()
        preview_title = tk.StringVar()
        preview_problem = tk.StringVar()
        preview_opening = tk.StringVar()

        tk.Label(
            right,
            textvariable=preview_env,
            bg=base.PANEL,
            fg=base.CYAN,
            font=('Segoe UI', 8, 'bold'),
        ).pack(anchor='w')
        tk.Label(
            right,
            textvariable=preview_title,
            bg=base.PANEL,
            fg=base.INK,
            font=('Segoe UI', 16, 'bold'),
            wraplength=430,
            justify='left',
        ).pack(anchor='w', pady=(6, 14))

        self.label(right, 'Presenting situation', 8, base.MUTED, 'bold').pack(anchor='w')
        tk.Label(
            right,
            textvariable=preview_problem,
            bg=base.PANEL,
            fg=base.INK,
            font=('Segoe UI', 10),
            wraplength=430,
            justify='left',
        ).pack(anchor='w', pady=(5, 18))

        self.label(right, 'How the session may open', 8, base.MUTED, 'bold').pack(anchor='w')
        tk.Label(
            right,
            textvariable=preview_opening,
            bg=base.PANEL,
            fg='#b7c6d8',
            font=('Segoe UI', 10, 'italic'),
            wraplength=430,
            justify='left',
        ).pack(anchor='w', pady=(5, 18))

        tk.Label(
            right,
            text='Practice simulation only • not a substitute for a genuine client session '
                 'where credential rules require one.',
            bg=base.PANEL,
            fg='#61748b',
            font=('Segoe UI', 8),
            wraplength=430,
            justify='left',
        ).pack(anchor='w', side='bottom')

        selected = {'scenario': self.active_scenario}

        def show_preview(_=None):
            indices = listbox.curselection()
            index = indices[0] if indices else 0
            scenario = COACHEE_SCENARIOS[index]
            selected['scenario'] = scenario
            preview_env.set(scenario['environment'].upper())
            preview_title.set(scenario['title'])
            preview_problem.set(scenario['visible_problem'])
            preview_opening.set('“' + scenario['opening'] + '”')

        listbox.bind('<<ListboxSelect>>', show_preview)

        current_index = next(
            (
                i
                for i, scenario in enumerate(COACHEE_SCENARIOS)
                if scenario['id'] == self.active_scenario['id']
            ),
            0,
        )
        listbox.selection_set(current_index)
        listbox.see(current_index)
        show_preview()

        footer = tk.Frame(dialog, bg=base.BG)
        footer.pack(fill='x', padx=24, pady=(0, 20))

        def use_scenario():
            if self.transcript.rows:
                if not self.confirm_unsaved():
                    return
                self.transcript = base.Transcript()
                self.dirty = False
            self.active_scenario = selected['scenario']
            self._refresh_scenario_text()
            self.render()
            dialog.destroy()

        self.button(
            footer,
            'Use this scenario',
            use_scenario,
            True,
        ).pack(side='right')
        self.button(
            footer,
            'Cancel',
            dialog.destroy,
            compact=True,
        ).pack(side='right', padx=(0, 8))

        dialog.bind('<Escape>', lambda _: dialog.destroy())
        dialog.update_idletasks()
        dialog.lift()
        dialog.focus_force()

    def toggle_focus(self):
        self.focused = not self.focused

        if self.focused:
            if self.conversation_visible:
                self.conversation_panel.pack_forget()
            self.consent_bar.pack_forget()
            self.case_bar.pack_forget()
            self.focus_button.configure(text='Exit focus')
            self.conversation_button.configure(state='disabled')
        else:
            self.consent_bar.pack(fill='x')
            if self.mode.get() == 'coach':
                self.case_bar.pack(
                    fill='x',
                    before=self.orb,
                    padx=(0, 12),
                    pady=(0, 8),
                )
            if self.conversation_visible:
                self.conversation_panel.pack(
                    side='right',
                    fill='y',
                    padx=(10, 0),
                )
            self.focus_button.configure(text='Focus')
            self.conversation_button.configure(state='normal')

    def start(self):
        if self.engine and self.engine.is_alive():
            return

        if not self.key.get().strip():
            self.open_settings()
            messagebox.showinfo(
                'Connect your coach',
                'Enter your Gemini API key in Settings. Use “How to get a key” '
                'for step-by-step help.',
                parent=self.settings,
            )
            return

        if not self.consent.get():
            messagebox.showinfo(
                'Before we begin',
                'Enable “Allow this session to use Google Gemini” below the session controls.',
                parent=self,
            )
            return

        try:
            pause = float(self.pause.get())
            threshold = float(self.threshold.get())
            if not 1 <= pause <= 60 or not .001 <= threshold <= .5:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                'Settings',
                'Use a pause from 1–60 seconds and threshold from 0.001–0.5.',
                parent=self,
            )
            return

        if not self.confirm_unsaved():
            return

        if self.remember.get():
            try:
                base.keyring.set_password(
                    'PresenceCoach',
                    'gemini',
                    self.key.get().strip(),
                )
            except Exception:
                messagebox.showwarning(
                    'Key storage',
                    'Could not remember the key securely. It will remain in memory for this run.',
                    parent=self,
                )

        self.transcript = base.Transcript()
        self.dirty = False
        self.render()
        self.muted.set(False)
        self.hold.set(False)
        self.state.set('Connecting…')
        self.connection_state.set('●  Connecting')

        coach_mode = self.mode.get() == 'coach'
        if coach_mode:
            system_prompt = build_coachee_prompt(self.active_scenario)
            input_role = 'Coach'
            output_role = 'Coachee'
            kickoff = scenario_kickoff(self.active_scenario)
            response_status = 'Thinking'
            self.display_state.set('Preparing coachee')
            self.display_hint.set('The simulated client will open the conversation.')
        else:
            system_prompt = SYSTEM_PROMPT
            input_role = 'Coachee'
            output_role = 'Coach'
            kickoff = None
            response_status = 'Reflecting'
            self.display_state.set('Connecting')
            self.display_hint.set('Preparing your coaching space.')

        self.engine = base.LiveEngine(
            self.key.get().strip(),
            self.model.get().strip(),
            self.voice.get(),
            self.devices.get(self.mic.get()),
            self.devices.get(self.speaker.get()),
            self.events,
            pause,
            threshold,
            system_prompt=system_prompt,
            input_role=input_role,
            output_role=output_role,
            kickoff=kickoff,
            response_status=response_status,
        )
        self.start_button.configure(state='disabled')
        self.end_button.configure(state='normal')
        self.engine.start()

    def render(self):
        bottom = self.log.yview()[1] >= .98
        position = self.log.yview()[0]
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')

        coach_mode = self.mode.get() == 'coach'

        if not self.transcript.rows:
            if coach_mode:
                scenario = self.active_scenario
                text = (
                    'Coach-practice mode\n\n'
                    f"Scenario: {scenario['title']}\n"
                    f"{scenario['environment']}\n\n"
                    'When you begin, the simulated coachee will introduce the presenting '
                    'situation in their own words. Coach naturally; deeper context is not '
                    'shown here and must emerge through the conversation.\n\n'
                    'This is a practice simulation, not an official credential-submission client.'
                )
            else:
                text = (
                    'Your conversation will appear here.\n\n'
                    'Presence is designed to keep the visual focus on the coaching space '
                    'rather than the transcript.\n\n'
                    'Speak naturally, or type below when you prefer.\n'
                )
            self.log.insert('end', text, 'body')

        for stamp, role, text in self.transcript.rows:
            if coach_mode:
                name = {
                    'Coach': 'YOU · COACH',
                    'Coachee': 'SIMULATED COACHEE',
                }.get(role, role.upper())
            else:
                name = {
                    'Coachee': 'YOU',
                    'Coach': 'PRESENCE',
                }.get(role, role.upper())

            self.log.insert('end', f'{name}   {stamp}\n', role)
            self.log.insert('end', text.strip() + '\n\n', 'body')

        self.log.configure(state='disabled')
        if bottom:
            self.log.see('end')
        else:
            self.log.yview_moveto(position)

    def build_orb(self):
        self._animation_frame = 0
        self._star_layout_size = None

        self.stars = []
        for i in range(42):
            x = ((i * 37) % 101) / 100
            y = ((i * 61 + 17) % 97) / 96
            size = 1 if i % 4 else 2
            item = self.orb.create_oval(0, 0, 1, 1, outline='', fill='#132134')
            self.stars.append((item, x, y, size))

        self.halos = [
            self.orb.create_oval(0, 0, 1, 1, outline='#101c2b', width=22),
            self.orb.create_oval(0, 0, 1, 1, outline='#14243a', width=8),
            self.orb.create_oval(0, 0, 1, 1, outline='#1d3147', width=2),
        ]
        self.orbit_arcs = [
            self.orb.create_arc(0, 0, 1, 1, start=18, extent=220, style=tk.ARC, outline='#16283d', width=1),
            self.orb.create_arc(0, 0, 1, 1, start=168, extent=165, style=tk.ARC, outline='#1b2c40', width=1),
            self.orb.create_arc(0, 0, 1, 1, start=285, extent=110, style=tk.ARC, outline='#18273a', width=1),
        ]

        particle_count = 380
        self.particles = []
        for i in range(particle_count):
            y = 1 - 2 * (i + .5) / particle_count
            angle = i * math.pi * (3 - math.sqrt(5))
            ring = math.sqrt(1 - y * y)
            point = (ring * math.cos(angle), y, ring * math.sin(angle))
            item = self.orb.create_oval(0, 0, 1, 1, outline='', fill=base.AMBER)
            self.particles.append((item, point, i))

        self.filaments = [
            self.orb.create_line(0, 0, 1, 1, fill='#744622', width=1)
            for _ in range(8)
        ]
        self.core = [
            self.orb.create_oval(0, 0, 1, 1, outline=color, width=width)
            for color, width in [
                ('#241d17', 16),
                ('#58391f', 8),
                ('#a86829', 4),
                ('#ffd694', 1),
            ]
        ]

    def animate(self):
        self._animation_frame = getattr(self, '_animation_frame', 0) + 1
        frame = self._animation_frame

        engine = self.engine
        live = bool(engine and engine.is_alive() and not engine.stopping.is_set())
        now = time.monotonic()
        playing = bool(live and getattr(engine, 'playback_until', 0) > now)
        talking = getattr(engine, 'output_level', 0) if playing else 0
        listening = live and self.state.get().startswith('Listening') and not self.muted.get()

        target = min(1.0, talking * 8 if playing else self.level * 10 if listening else 0)
        self.envelope += (target - self.envelope) * (.4 if target > self.envelope else .12)
        power = self.envelope
        gentle = self.reduced_motion.get()
        self.phase += .007 if gentle else .014 + power * .034
        t = self.phase

        c = self.orb
        w, h = max(1, c.winfo_width()), max(1, c.winfo_height())
        radius = min(w, h) * .39
        shake = 0 if gentle else power * 3
        cx = w / 2 + math.sin(t * 17) * shake
        cy = h / 2 + math.cos(t * 21) * shake
        ca, sa = math.cos(t), math.sin(t)
        tilt = .28 * math.sin(t * .7)
        ct, st = math.cos(tilt), math.sin(tilt)

        layout_size = (w, h)
        if self._star_layout_size != layout_size:
            for item, fx, fy, size in self.stars:
                px, py = fx * w, fy * h
                c.coords(item, px - size, py - size, px + size, py + size)
            self._star_layout_size = layout_size

        halo_scales = (1.34, 1.18, 1.05)
        halo_color = '#15313a' if listening else '#2a2119' if playing else '#101c2b'
        for index, (item, scale) in enumerate(zip(self.halos, halo_scales)):
            r = radius * scale * (1 + power * (.035 if index else .055))
            c.coords(item, cx - r, cy - r, cx + r, cy + r)
            if index == 1 and frame % 3 == 0:
                c.itemconfigure(item, outline=halo_color)

        for j, item in enumerate(self.orbit_arcs):
            rx = radius * (1.45 + j * .17)
            ry = radius * (.74 + j * .08)
            c.coords(item, cx - rx, cy - ry, cx + rx, cy + ry)
            if frame % 2 == 0:
                c.itemconfigure(
                    item,
                    start=(18 + j * 122 + math.degrees(t * (.18 + j * .03))) % 360,
                    outline=base.CYAN if listening and j == 0 else '#21344a',
                )

        recolor = frame % 4 == 0
        for item, (x, y, z), i in self.particles:
            xr, zr = x * ca + z * sa, z * ca - x * sa
            yr, depth = y * ct - zr * st, y * st + zr * ct
            ripple = 1 + power * (.025 if gentle else .13) * math.sin(i * .43 + t * 14)
            perspective = 2.8 / (2.8 - depth * .45)
            px = cx + xr * radius * ripple * perspective
            py = cy + yr * radius * ripple * perspective
            bright = (depth + 1) / 2
            size = .7 + bright * 1.35 + power * .55
            c.coords(item, px - size, py - size, px + size, py + size)

            if recolor:
                color = '#%02x%02x%02x' % (
                    int(95 + 160 * bright),
                    int(52 + 139 * bright),
                    int(24 + 78 * bright),
                )
                c.itemconfigure(item, fill=color)

        for j, item in enumerate(self.filaments):
            points = []
            for k in range(41):
                a = k * math.tau / 40
                rr = radius * (
                    1
                    + .035 * math.sin(a * 9 + t * 4 + j)
                    + power * .09 * math.sin(a * 17 - t * 9 + j)
                )
                x = math.cos(a)
                y = math.sin(a) * math.cos(j * .48 + t * .16)
                z = math.sin(a) * math.sin(j * .48 + t * .16)
                xr, zr = x * ca + z * sa, z * ca - x * sa
                yr = y * ct - zr * st
                points.extend((cx + xr * rr, cy + yr * rr))
            c.coords(item, *points)

        for j, item in enumerate(self.core):
            r = radius * (.13 + (3 - j) * .035 + power * .08)
            c.coords(item, cx - r, cy - r, cx + r, cy + r)

        coach_mode = hasattr(self, 'mode') and self.mode.get() == 'coach'
        raw_state = self.state.get()

        if playing:
            if coach_mode:
                label = 'Simulated coachee is speaking'
                hint = 'Stay with the person, not only the problem.'
            else:
                label = 'Presence is speaking'
                hint = 'Notice what lands.'
        elif live and self.muted.get():
            label = 'Microphone muted'
            hint = 'Unmute when you’re ready to continue.'
        elif listening and self.hold.get():
            label = 'Listening to you' if coach_mode else 'Listening'
            hint = 'Take all the time you need. I’ll wait.'
        elif listening:
            label = 'Listening to you' if coach_mode else 'Listening'
            hint = 'You are the coach.' if coach_mode else 'I’m here.'
        elif raw_state.startswith('Connecting'):
            label = 'Preparing coachee' if coach_mode else 'Connecting'
            hint = 'Loading the selected practice scenario.' if coach_mode else 'Preparing your coaching space.'
        elif raw_state.startswith('Stopping'):
            label = 'Closing the session'
            hint = 'Your transcript will remain available.'
        elif raw_state == 'Session complete':
            label = 'Session complete'
            hint = 'Review the transcript for your coaching practice.' if coach_mode else 'Keep what is useful. Leave what is not.'
        elif live:
            if coach_mode and raw_state in ('Thinking', 'Reflecting'):
                label = 'Coachee is thinking'
                hint = 'Give the client room to form their response.'
            else:
                label = raw_state.replace('…', '').strip() or 'Thinking'
                hint = 'Stay curious about what emerges.' if coach_mode else 'Presence is with your last thought.'
        else:
            if coach_mode:
                label = 'Ready to practice'
                hint = 'Choose a case, then begin coaching.'
            else:
                label = 'Ready when you are'
                hint = 'A quiet space for whatever matters.'

        if self.display_state.get() != label:
            self.display_state.set(label)
        if self.display_hint.get() != hint:
            self.display_hint.set(hint)

        self.after(50, self.animate)

    def api_help(self):
        settings_visible = (
            hasattr(self, 'settings')
            and self.settings.winfo_exists()
            and self.settings.state() != 'withdrawn'
        )
        parent = self.settings if settings_visible else self

        dialog = tk.Toplevel(parent)
        dialog.title('Connect Presence to Gemini')
        dialog.configure(bg=base.BG)
        dialog.geometry('520x500')
        dialog.resizable(False, False)
        dialog.transient(parent)

        self.label(dialog, 'Connect Presence to Gemini', 18, base.INK, 'bold').pack(
            anchor='w', padx=24, pady=(24, 4)
        )
        self.label(
            dialog,
            'You only need to do this once if you choose to remember the key.',
            9,
            base.MUTED,
        ).pack(anchor='w', padx=24, pady=(0, 18))

        card = tk.Frame(
            dialog,
            bg=base.PANEL,
            highlightbackground=base.BORDER,
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        card.pack(fill='both', expand=True, padx=24, pady=(0, 14))

        for number, text in [
            ('1', 'Open Google AI Studio and sign in.'),
            ('2', 'Open Gemini API Keys and create a key.'),
            ('3', 'Copy the key.'),
            ('4', 'Paste it into Presence → Settings.'),
        ]:
            row = tk.Frame(card, bg=base.PANEL)
            row.pack(fill='x', pady=7)
            tk.Label(
                row,
                text=number,
                width=3,
                bg=base.SURFACE_2,
                fg=base.AMBER,
                font=('Segoe UI', 9, 'bold'),
                padx=4,
                pady=4,
            ).pack(side='left', padx=(0, 10))
            self.label(row, text, 10, base.INK).pack(side='left')

        self.label(
            card,
            'Keep your API key private. Usage and quotas are controlled by Google.',
            8,
            base.MUTED,
        ).pack(anchor='w', pady=(12, 0))

        self.button(
            dialog,
            'Open AI Studio home ↗',
            lambda: webbrowser.open('https://aistudio.google.com/'),
            True,
        ).pack(fill='x', padx=24, pady=4)
        self.button(
            dialog,
            'Open Gemini API Keys ↗',
            lambda: webbrowser.open('https://aistudio.google.com/apikey'),
        ).pack(fill='x', padx=24, pady=4)
        self.button(dialog, 'Close', dialog.destroy, compact=True).pack(pady=(8, 18))
        dialog.bind('<Escape>', lambda _: dialog.destroy())
        dialog.update_idletasks()
        dialog.lift()
        dialog.focus_force()


if __name__ == '__main__':
    PresenceApp().mainloop()

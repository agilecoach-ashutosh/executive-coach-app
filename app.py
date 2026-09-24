"""Presence Coach desktop application. Run with Python 3.12+."""
import math
import queue
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import keyring
import sounddevice as sd

from coaching import IMMINENT_DANGER_RESPONSE, Transcript, detects_imminent_danger
from engine import LiveEngine

BG = '#050810'
PANEL = '#0a111c'
SURFACE = '#0d1724'
SURFACE_2 = '#111f30'
BORDER = '#1b2a3c'
AMBER = '#ffb454'
AMBER_SOFT = '#d89243'
CYAN = '#66d9ef'
INK = '#eef5ff'
MUTED = '#7f92aa'
DANGER = '#ff7d7d'

PARTICLE_COUNT = 180
FILAMENT_COUNT = 8
FILAMENT_STEPS = 40
ANIMATION_DELAY_MS = 50
REDUCED_MOTION_DELAY_MS = 100


API_HELP = """GET YOUR GEMINI API KEY

1. Sign in to Google AI Studio.
2. Open API keys.
3. Create a key and choose a project if Google asks.
4. Copy the key.
5. Paste it into Presence → Settings.

Gemini offers a Free Tier. No paid Gemini subscription is required to get started.
Free usage is subject to Google's current project-specific limits.
Keep your key private."""
GEMINI_RATE_LIMIT_URL = "https://aistudio.google.com/rate-limit?timeRange=last-28-days"


def _is_usage_limit_error(detail):
    text = (detail or "").lower()
    markers = (
        "429",
        "resource_exhausted",
        "rate_limit_exceeded",
        "quota_exceeded",
        "rate limit",
        "quota exceeded",
        "too many requests",
    )
    return any(marker in text for marker in markers)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Presence Coach • A space to think')
        self.geometry('1360x840')
        self.minsize(1100, 720)
        self.configure(bg=BG)

        self.events, self.engine = queue.Queue(), None
        self.transcript = Transcript()
        self.dirty = False
        self.phase, self.level = 0, 0
        self.envelope = 0.0
        self.conversation_visible = True
        self.focused = False
        self._safety_alerted = False
        self.audio_exported = True

        self.display_state = tk.StringVar(value='Ready when you are')
        self.display_hint = tk.StringVar(value='A quiet space for whatever matters.')
        self.connection_state = tk.StringVar(value='●  Ready')
        self.reduced_motion = tk.BooleanVar(value=False)
        self.state = tk.StringVar(value='Ready when you are')
        self.key = tk.StringVar()
        try:
            self.key.set(keyring.get_password('PresenceCoach', 'gemini') or '')
        except Exception:
            pass

        self.model = tk.StringVar(value='gemini-3.8-live')
        self.voice = tk.StringVar(value='Kore')
        self.pause = tk.StringVar(value='6')
        self.threshold = tk.StringVar(value='0.018')
        self.remember = tk.BooleanVar(value=False)
        self.consent = tk.BooleanVar(value=False)
        self.hold, self.muted = tk.BooleanVar(), tk.BooleanVar()

        self.configure_ttk()
        self.make_ui()
        self.make_settings()
        self.render()
        self.set_session_controls(False)

        self.bind('<F9>', lambda _: self.toggle_focus())
        self.bind('<Escape>', self.on_escape)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(40, self.poll)
        self.after(ANIMATION_DELAY_MS, self.animate)

    def configure_ttk(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure(
            'Presence.TEntry',
            fieldbackground=SURFACE_2,
            foreground=INK,
            insertcolor=INK,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=9,
        )
        style.configure(
            'Presence.TCombobox',
            fieldbackground=SURFACE_2,
            foreground=INK,
            background=SURFACE_2,
            arrowcolor=MUTED,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=7,
        )
        style.map(
            'Presence.TCombobox',
            fieldbackground=[('readonly', SURFACE_2)],
            foreground=[('readonly', INK)],
            selectbackground=[('readonly', SURFACE_2)],
            selectforeground=[('readonly', INK)],
        )
        style.configure(
            'Presence.Vertical.TScrollbar',
            background=SURFACE_2,
            troughcolor=PANEL,
            bordercolor=PANEL,
            arrowcolor=MUTED,
        )

    def label(self, parent, text, size=11, color=INK, weight='normal'):
        return tk.Label(
            parent,
            text=text,
            font=('Segoe UI', size, weight),
            bg=parent['bg'],
            fg=color,
        )

    def button(self, parent, text, command, primary=False, compact=False, danger=False):
        bg = AMBER if primary else SURFACE_2
        fg = BG if primary else (DANGER if danger else INK)
        active = '#ffd094' if primary else '#172a40'
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=('Segoe UI', 9 if compact else 10, 'bold'),
            bg=bg,
            fg=fg,
            activebackground=active,
            activeforeground=BG if primary else INK,
            disabledforeground='#526277',
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=10 if compact else 15,
            pady=7 if compact else 10,
            cursor='hand2',
        )

    def make_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.header = tk.Frame(self, bg=BG, height=68)
        self.header.grid(row=0, column=0, sticky='ew', padx=24, pady=(14, 8))
        self.header.pack_propagate(False)

        brand = tk.Frame(self.header, bg=BG)
        brand.pack(side='left', fill='y')
        self.label(brand, 'PRESENCE', 18, AMBER, 'bold').pack(anchor='w')
        self.label(brand, 'a space to think', 9, MUTED).pack(anchor='w', pady=(0, 2))

        actions = tk.Frame(self.header, bg=BG)
        actions.pack(side='right', fill='y')
        tk.Label(
            actions,
            textvariable=self.connection_state,
            bg=BG,
            fg=MUTED,
            font=('Segoe UI', 9, 'bold'),
        ).pack(side='left', padx=(0, 12))
        self.focus_button = self.button(actions, 'Focus', self.toggle_focus, compact=True)
        self.focus_button.pack(side='left', padx=3)
        self.conversation_button = self.button(actions, '◫  Conversation', self.toggle_conversation, compact=True)
        self.conversation_button.pack(side='left', padx=3)
        self.button(actions, 'ⓘ', self.api_help, compact=True).pack(side='left', padx=3)
        self.button(actions, '⚙', self.open_settings, compact=True).pack(side='left', padx=3)

        self.body = tk.Frame(self, bg=BG)
        self.body.grid(row=1, column=0, sticky='nsew', padx=24, pady=(0, 16))

        self.stage = tk.Frame(self.body, bg=BG)
        self.stage.pack(side='left', fill='both', expand=True)

        self.orb = tk.Canvas(
            self.stage,
            bg=BG,
            highlightthickness=0,
            borderwidth=0,
            cursor='arrow',
        )
        self.orb.pack(fill='both', expand=True, padx=(0, 12), pady=(0, 2))
        self.build_orb()

        state_wrap = tk.Frame(self.stage, bg=BG, height=62)
        state_wrap.pack(fill='x', pady=(0, 8))
        state_wrap.pack_propagate(False)
        tk.Label(
            state_wrap,
            textvariable=self.display_state,
            bg=BG,
            fg=INK,
            font=('Segoe UI', 15, 'bold'),
        ).pack()
        tk.Label(
            state_wrap,
            textvariable=self.display_hint,
            bg=BG,
            fg=MUTED,
            font=('Segoe UI', 10),
        ).pack(pady=(3, 0))

        self.session_dock = tk.Frame(
            self.stage,
            bg=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        self.session_dock.pack(pady=(0, 8))

        self.start_button = self.button(self.session_dock, 'Begin', self.start, True)
        self.start_button.pack(side='left', padx=4)

        self.interrupt_button = self.button(
            self.session_dock, '↯  Interrupt', lambda: self.command('interrupt'), compact=True
        )
        self.interrupt_button.pack(side='left', padx=4)

        self.ready_button = self.button(
            self.session_dock, '✓  I’m ready', lambda: self.command('finish'), compact=True
        )
        self.ready_button.pack(side='left', padx=4)

        self.end_button = self.button(self.session_dock, '■  End', self.stop, compact=True, danger=True)
        self.end_button.pack(side='left', padx=4)

        hold = tk.Checkbutton(
            self.session_dock,
            text='Take your time',
            variable=self.hold,
            command=lambda: self.command('hold', self.hold.get()),
            bg=SURFACE,
            fg=INK,
            selectcolor=SURFACE_2,
            activebackground=SURFACE,
            activeforeground=INK,
            font=('Segoe UI', 9),
            cursor='hand2',
        )
        hold.pack(side='left', padx=(10, 4))

        mute = tk.Checkbutton(
            self.session_dock,
            text='Mute',
            variable=self.muted,
            command=lambda: self.command('mute', self.muted.get()),
            bg=SURFACE,
            fg=MUTED,
            selectcolor=SURFACE_2,
            activebackground=SURFACE,
            activeforeground=INK,
            font=('Segoe UI', 9),
            cursor='hand2',
        )
        mute.pack(side='left', padx=4)

        self.consent_bar = tk.Frame(self.stage, bg=BG)
        self.consent_bar.pack(fill='x')
        tk.Checkbutton(
            self.consent_bar,
            text='Allow this session to use Google Gemini',
            variable=self.consent,
            bg=BG,
            fg=MUTED,
            selectcolor=SURFACE,
            activebackground=BG,
            activeforeground=INK,
            font=('Segoe UI', 8),
            cursor='hand2',
        ).pack()
        self.label(
            self.consent_bar,
            'Your transcript stays in the app unless you export it.',
            8,
            '#61748b',
        ).pack(pady=(1, 0))

        self.make_conversation_panel()

    def make_conversation_panel(self):
        self.conversation_panel = tk.Frame(
            self.body,
            bg=PANEL,
            width=360,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.conversation_panel.pack(side='right', fill='y', padx=(10, 0))
        self.conversation_panel.pack_propagate(False)

        panel_header = tk.Frame(self.conversation_panel, bg=PANEL)
        panel_header.pack(fill='x', padx=18, pady=(16, 10))
        self.label(panel_header, 'Conversation', 12, INK, 'bold').pack(side='left')
        self.button(panel_header, '×', self.toggle_conversation, compact=True).pack(side='right')
        self.button(panel_header, 'Export', self.save, compact=True).pack(side='right', padx=(0, 6))

        self.label(
            self.conversation_panel,
            'Private coaching transcript',
            8,
            MUTED,
        ).pack(anchor='w', padx=18, pady=(0, 10))

        textframe = tk.Frame(self.conversation_panel, bg=PANEL)
        textframe.pack(fill='both', expand=True, padx=(8, 2))

        self.log = tk.Text(
            textframe,
            bg=PANEL,
            fg=INK,
            font=('Segoe UI', 10),
            wrap='word',
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            pady=12,
            state='disabled',
            spacing1=2,
            spacing3=9,
            width=1,
        )
        scrollbar = ttk.Scrollbar(
            textframe,
            command=self.log.yview,
            style='Presence.Vertical.TScrollbar',
        )
        scrollbar.pack(side='right', fill='y')
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(fill='both', expand=True)
        self.log.tag_configure('Coach', foreground=AMBER, font=('Segoe UI', 8, 'bold'))
        self.log.tag_configure('Coachee', foreground=CYAN, font=('Segoe UI', 8, 'bold'))
        self.log.tag_configure('Session note', foreground=MUTED, font=('Segoe UI', 8, 'italic'))
        self.log.tag_configure('body', foreground=INK, font=('Segoe UI', 10), lmargin1=0, lmargin2=0)

        composer = tk.Frame(
            self.conversation_panel,
            bg=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        composer.pack(fill='x', padx=14, pady=14)

        self.message = tk.StringVar()
        entry = ttk.Entry(
            composer,
            textvariable=self.message,
            font=('Segoe UI', 10),
            style='Presence.TEntry',
        )
        entry.pack(side='left', fill='x', expand=True, padx=(4, 0), pady=4)
        entry.bind('<Return>', lambda _: self.send())
        self.button(composer, 'Send', self.send, compact=True).pack(side='right', padx=5, pady=4)

    def toggle_conversation(self):
        if self.focused:
            return
        if self.conversation_visible:
            self.conversation_panel.pack_forget()
            self.conversation_visible = False
            self.conversation_button.configure(text='◫  Conversation')
        else:
            self.conversation_panel.pack(side='right', fill='y', padx=(10, 0))
            self.conversation_visible = True
            self.conversation_button.configure(text='◫  Hide')

    def toggle_focus(self):
        self.focused = not self.focused
        if self.focused:
            if self.conversation_visible:
                self.conversation_panel.pack_forget()
            self.consent_bar.pack_forget()
            self.focus_button.configure(text='Exit focus')
            self.conversation_button.configure(state='disabled')
        else:
            self.consent_bar.pack(fill='x')
            if self.conversation_visible:
                self.conversation_panel.pack(side='right', fill='y', padx=(10, 0))
            self.focus_button.configure(text='Focus')
            self.conversation_button.configure(state='normal')

    def on_escape(self, _=None):
        if self.focused:
            self.toggle_focus()
        elif hasattr(self, 'settings') and self.settings.state() != 'withdrawn':
            self.settings.withdraw()

    def make_settings(self):
        self.settings = tk.Toplevel(self)
        self.settings.title('Presence • Settings')
        self.settings.configure(bg=BG)
        self.settings.geometry('600x760')
        self.settings.minsize(520, 560)
        self.settings.protocol('WM_DELETE_WINDOW', self.settings.withdraw)
        self.settings.bind('<Escape>', lambda _: self.settings.withdraw())
        self.settings.rowconfigure(1, weight=1)
        self.settings.columnconfigure(0, weight=1)

        top = tk.Frame(self.settings, bg=BG)
        top.grid(row=0, column=0, sticky='ew', padx=24, pady=(20, 10))
        self.label(top, 'Settings', 20, INK, 'bold').pack(side='left')
        self.button(top, 'Done', self.settings.withdraw, compact=True).pack(side='right')

        wrap = tk.Frame(self.settings, bg=BG)
        wrap.grid(row=1, column=0, sticky='nsew')
        canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        bar = ttk.Scrollbar(wrap, command=canvas.yview, style='Presence.Vertical.TScrollbar')
        bar.pack(side='right', fill='y')
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(fill='both', expand=True)

        content = tk.Frame(canvas, bg=BG)
        window = canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window, width=e.width))
        content.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))

        connection = tk.Frame(
            content,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        connection.pack(fill='x', padx=22, pady=(6, 12))

        head = tk.Frame(connection, bg=PANEL)
        head.pack(fill='x', pady=(0, 8))
        self.label(head, 'Gemini connection', 12, INK, 'bold').pack(side='left')
        self.button(head, 'How to get a key ↗', self.api_help, compact=True).pack(side='right')

        self.label(connection, 'Gemini API key', 9, MUTED).pack(anchor='w')
        key_entry = ttk.Entry(
            connection,
            textvariable=self.key,
            show='•',
            style='Presence.TEntry',
        )
        key_entry.pack(fill='x', pady=(4, 8))

        tk.Label(
            connection,
            text=(
                'Free tier available • No paid Gemini subscription is required to get started. '
                'Free usage is subject to Google’s current project-specific limits.'
            ),
            bg=PANEL,
            fg=MUTED,
            font=('Segoe UI', 8),
            justify='left',
            anchor='w',
            wraplength=500,
        ).pack(fill='x', anchor='w', pady=(0, 5))
        self.button(
            connection,
            'Check Gemini quota ↗',
            lambda: webbrowser.open(GEMINI_RATE_LIMIT_URL),
            compact=True,
        ).pack(anchor='w', pady=(0, 8))

        tk.Checkbutton(
            connection,
            text='Remember key securely in this device’s credential store',
            variable=self.remember,
            bg=PANEL,
            fg=MUTED,
            selectcolor=SURFACE,
            activebackground=PANEL,
            activeforeground=INK,
            font=('Segoe UI', 8),
        ).pack(anchor='w')
        self.button(connection, 'Forget saved key', self.forget_key, compact=True).pack(anchor='w', pady=(8, 0))

        session = tk.Frame(
            content,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        session.pack(fill='x', padx=22, pady=12)
        self.label(session, 'Voice & session', 12, INK, 'bold').pack(anchor='w', pady=(0, 10))

        self.settings_widgets = [key_entry]
        for label, variable, choices in [
            ('Live model', self.model, ['gemini-3.8-live', 'gemini-3.1-flash-live-preview']),
            ('Voice', self.voice, ['Kore', 'Aoede', 'Puck', 'Charon', 'Fenrir']),
            ('Silence before reply', self.pause, ['3', '6', '10', '15']),
            ('Mic threshold', self.threshold, ['0.008', '0.018', '0.035', '0.06']),
        ]:
            self.label(session, label, 9, MUTED).pack(anchor='w', pady=(5, 0))
            widget = ttk.Combobox(
                session,
                textvariable=variable,
                values=choices,
                style='Presence.TCombobox',
            )
            widget.pack(fill='x', pady=(3, 5))
            self.settings_widgets.append(widget)

        audio = tk.Frame(
            content,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        audio.pack(fill='x', padx=22, pady=12)
        self.label(audio, 'Audio devices', 12, INK, 'bold').pack(anchor='w', pady=(0, 10))

        self.devices = {'System default': None}
        try:
            devices = sd.query_devices()
        except Exception:
            devices = []

        inputs, outputs = ['System default'], ['System default']
        for index, device in enumerate(devices):
            name = f'{index}: {device["name"]}'
            self.devices[name] = index
            if device['max_input_channels']:
                inputs.append(name)
            if device['max_output_channels']:
                outputs.append(name)

        self.mic, self.speaker = tk.StringVar(value=inputs[0]), tk.StringVar(value=outputs[0])
        for label, variable, values in [
            ('Microphone', self.mic, inputs),
            ('Speaker / headphones', self.speaker, outputs),
        ]:
            self.label(audio, label, 9, MUTED).pack(anchor='w', pady=(5, 0))
            widget = ttk.Combobox(
                audio,
                textvariable=variable,
                values=values,
                state='readonly',
                style='Presence.TCombobox',
            )
            widget.pack(fill='x', pady=(3, 5))
            self.settings_widgets.append(widget)

        motion = tk.Frame(
            content,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        motion.pack(fill='x', padx=22, pady=(12, 22))
        self.label(motion, 'Experience', 12, INK, 'bold').pack(anchor='w', pady=(0, 8))
        tk.Checkbutton(
            motion,
            text='Gentle motion / reduced animation',
            variable=self.reduced_motion,
            bg=PANEL,
            fg=MUTED,
            selectcolor=SURFACE,
            activebackground=PANEL,
            activeforeground=INK,
            font=('Segoe UI', 9),
        ).pack(anchor='w')
        self.label(motion, 'Changes apply immediately where possible; audio settings apply next session.', 8, MUTED).pack(
            anchor='w', pady=(8, 0)
        )

        self.settings.withdraw()

    def open_settings(self):
        self.settings.deiconify()
        self.settings.lift()
        self.settings.focus_set()

    def api_help(self):
        parent = self.settings if hasattr(self, 'settings') else self
        dialog = tk.Toplevel(parent)
        dialog.title('Connect Presence to Gemini')
        dialog.configure(bg=BG)
        dialog.geometry('520x610')
        dialog.resizable(False, False)
        dialog.transient(parent)

        self.label(dialog, 'Connect Presence to Gemini', 18, INK, 'bold').pack(
            anchor='w', padx=24, pady=(24, 4)
        )
        self.label(dialog, 'You only need to do this once if you choose to remember the key.', 9, MUTED).pack(
            anchor='w', padx=24, pady=(0, 18)
        )

        card = tk.Frame(
            dialog,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        card.pack(fill='both', expand=True, padx=24, pady=(0, 14))

        steps = [
            ('1', 'Open Google AI Studio and sign in.'),
            ('2', 'Open API keys and create a key.'),
            ('3', 'Copy the key.'),
            ('4', 'Paste it into Presence → Settings.'),
        ]
        for number, text in steps:
            row = tk.Frame(card, bg=PANEL)
            row.pack(fill='x', pady=7)
            tk.Label(
                row,
                text=number,
                width=3,
                bg=SURFACE_2,
                fg=AMBER,
                font=('Segoe UI', 9, 'bold'),
                padx=4,
                pady=4,
            ).pack(side='left', padx=(0, 10))
            self.label(row, text, 10, INK).pack(side='left')

        self.label(
            card,
            'Gemini offers a Free Tier, so no paid Gemini subscription is required to get started.',
            8,
            MUTED,
        ).pack(anchor='w', pady=(12, 3))
        self.label(
            card,
            'Free usage is subject to Google’s current project-specific rate and quota limits. '
            'Presence Coach does not automatically enable paid billing.',
            8,
            MUTED,
        ).pack(anchor='w', pady=(0, 3))
        self.label(card, 'Keep your API key private.', 8, MUTED).pack(anchor='w', pady=(0, 0))

        self.button(
            dialog,
            'Open Google AI Studio ↗',
            lambda: webbrowser.open('https://aistudio.google.com/'),
            True,
        ).pack(fill='x', padx=24, pady=4)
        self.button(
            dialog,
            'Open API keys ↗',
            lambda: webbrowser.open('https://aistudio.google.com/api-keys'),
        ).pack(fill='x', padx=24, pady=4)
        self.button(
            dialog,
            'Check Gemini quota & rate limits ↗',
            lambda: webbrowser.open(GEMINI_RATE_LIMIT_URL),
        ).pack(fill='x', padx=24, pady=4)
        self.button(dialog, 'Close', dialog.destroy, compact=True).pack(pady=(8, 18))
        dialog.bind('<Escape>', lambda _: dialog.destroy())

    def set_session_controls(self, live):
        normal = 'normal' if live else 'disabled'
        self.interrupt_button.configure(state=normal)
        self.ready_button.configure(state=normal)
        self.end_button.configure(state=normal)
        self.start_button.configure(state='disabled' if live else 'normal')

    def start(self):
        if self.engine and self.engine.is_alive():
            return
        if not self.key.get().strip():
            self.open_settings()
            messagebox.showinfo(
                'Connect your coach',
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
                keyring.set_password('PresenceCoach', 'gemini', self.key.get().strip())
            except Exception:
                messagebox.showwarning(
                    'Key storage',
                    'Could not remember the key securely. It will remain in memory for this run.',
                )

        self.transcript = Transcript()
        self.dirty = False
        self.audio_exported = False
        self._safety_alerted = False
        self.render()
        self.muted.set(False)
        self.hold.set(False)
        self.state.set('Connecting…')
        self.connection_state.set('●  Connecting')
        self.display_state.set('Connecting')
        self.display_hint.set('Preparing your coaching space.')

        self.engine = LiveEngine(
            self.key.get().strip(),
            self.model.get().strip(),
            self.voice.get(),
            self.devices.get(self.mic.get()),
            self.devices.get(self.speaker.get()),
            self.events,
            pause,
            threshold,
        )
        self.start_button.configure(state='disabled')
        self.end_button.configure(state='normal')
        self.engine.start()

    def command(self, name, value=None):
        if self.engine and self.engine.is_alive():
            self.engine.command(name, value)

    def send(self):
        text = self.message.get().strip()
        if not text:
            return
        if not self.engine or not self.engine.is_alive() or self.state.get() == 'Connecting…':
            messagebox.showinfo('Start a session', 'Begin and connect before sending a message.')
            return
        if (
            getattr(self, 'practice_mode', 'coachee') != 'coach'
            and detects_imminent_danger(text)
        ):
            self.transcript.boundary = True
            self.transcript.add('Coachee', text)
            self.message.set('')
            self._show_safety_alert(IMMINENT_DANGER_RESPONSE)
            self.render()
            return
        self.command('text', text)
        self.message.set('')

    def stop(self):
        if self.engine and self.engine.is_alive():
            self.engine.stop()
            self.state.set('Stopping…')
            self.connection_state.set('●  Ending')

    def _show_safety_alert(self, text):
        if self._safety_alerted:
            return
        self._safety_alerted = True
        if self.engine and self.engine.is_alive():
            self.engine.stop()
        self.transcript.boundary = True
        self.transcript.add('Session note', text)
        self.transcript.boundary = True
        self.dirty = True
        self.state.set('Safety support needed')
        self.connection_state.set('●  Session ending')
        if self.consent.get():
            self.consent.set(False)
        messagebox.showwarning('Immediate safety support', text, parent=self)

    def forget_key(self):
        try:
            keyring.delete_password('PresenceCoach', 'gemini')
        except keyring.errors.PasswordDeleteError:
            pass
        except Exception:
            messagebox.showerror(
                'Key storage',
                'Could not delete the saved key. Check this device’s credential store.',
            )
            return
        self.key.set('')
        self.remember.set(False)

    def poll(self):
        changed = False
        for _ in range(400):
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break

            if kind in ('Coach', 'Coachee', 'user_text'):
                if kind == 'user_text':
                    self.transcript.boundary = True
                self.transcript.add('Coachee' if kind == 'user_text' else kind, value)
                self.dirty, changed = True, True
            elif kind == 'boundary':
                self.transcript.boundary = True
            elif kind == 'level':
                self.level = value
            elif kind == 'status':
                self.state.set(value)
            elif kind == 'connected':
                self.state.set('Listening')
                self.connection_state.set('●  Live')
                self.set_session_controls(True)
            elif kind == 'disconnected':
                self.state.set(
                    'Safety support needed' if self._safety_alerted else 'Session complete'
                )
                self.connection_state.set('●  Ready')
                self.set_session_controls(False)
                self.level = 0
            elif kind == 'notice':
                self.transcript.boundary = True
                self.transcript.add('Session note', value)
                self.transcript.boundary = True
                self.dirty, changed = True, True
            elif kind == 'safety':
                self._show_safety_alert(value)
                changed = True
            elif kind == 'error':
                self.connection_state.set('●  Needs attention')
                provider_var = getattr(self, 'provider', None)
                provider_name = provider_var.get() if provider_var is not None else 'Google Gemini'
                if provider_name == 'Google Gemini' and _is_usage_limit_error(value):
                    messagebox.showerror(
                        'Gemini usage limit reached',
                        (
                            'Your Google Gemini project has reached its current usage or rate limit.\n\n'
                            'Please try again later or check your quota in Google AI Studio. '
                            'If you are using the Free Tier, Presence Coach will not automatically '
                            'enable billing or switch your project to paid usage.\n\n'
                            'Your transcript is still available.'
                        ),
                    )
                else:
                    messagebox.showerror(
                        'Connection or audio issue',
                        value
                        + '\n\nCheck API key, quota, model access, and audio devices. '
                          'Your transcript is still available.',
                    )

        if changed:
            self.render()
        self.after(40, self.poll)

    def render(self):
        bottom = self.log.yview()[1] >= .98
        position = self.log.yview()[0]
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')

        if not self.transcript.rows:
            self.log.insert(
                'end',
                'Your conversation will appear here.\n\n'
                'Presence is designed to keep the visual focus on the coaching space rather than the transcript.\n\n'
                'Speak naturally, or type below when you prefer.\n',
                'body',
            )

        for stamp, role, text in self.transcript.rows:
            name = dict(Coachee='YOU', Coach='PRESENCE').get(role, role.upper())
            self.log.insert('end', f'{name}   {stamp}\n', role)
            self.log.insert('end', text.strip() + '\n\n', 'body')

        self.log.configure(state='disabled')
        if bottom:
            self.log.see('end')
        else:
            self.log.yview_moveto(position)

    def build_orb(self):
        self.stars = []
        for i in range(58):
            # Deterministic positions keep the backdrop calm instead of randomising every launch.
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

        self.particles = []
        for i in range(PARTICLE_COUNT):
            y = 1 - 2 * (i + .5) / PARTICLE_COUNT
            angle = i * math.pi * (3 - math.sqrt(5))
            ring = math.sqrt(1 - y * y)
            point = (ring * math.cos(angle), y, ring * math.sin(angle))
            item = self.orb.create_oval(0, 0, 1, 1, outline='', fill=AMBER)
            self.particles.append((item, point, i))

        self.filaments = [
            self.orb.create_line(0, 0, 1, 1, fill='#744622', width=1)
            for _ in range(FILAMENT_COUNT)
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
        self.phase += .006 if gentle else .012 + power * .032
        t = self.phase

        c = self.orb
        w, h = max(1, c.winfo_width()), max(1, c.winfo_height())
        # Leave enough breathing room for the outer halo at peak animation.
        radius = min(w, h) * .33
        shake = 0 if gentle else power * 3
        cx = w / 2 + math.sin(t * 17) * shake
        cy = h / 2 + math.cos(t * 21) * shake
        ca, sa = math.cos(t), math.sin(t)
        tilt = .28 * math.sin(t * .7)
        ct, st = math.cos(tilt), math.sin(tilt)

        for item, fx, fy, size in self.stars:
            px, py = fx * w, fy * h
            c.coords(item, px - size, py - size, px + size, py + size)

        halo_scales = (1.34, 1.18, 1.05)
        halo_color = '#15313a' if listening else '#2a2119' if playing else '#101c2b'
        for index, (item, scale) in enumerate(zip(self.halos, halo_scales)):
            r = radius * scale * (1 + power * (.035 if index else .055))
            c.coords(item, cx - r, cy - r, cx + r, cy + r)
            if index == 1:
                c.itemconfigure(item, outline=halo_color)

        for j, item in enumerate(self.orbit_arcs):
            rx = radius * (1.45 + j * .17)
            ry = radius * (.74 + j * .08)
            c.coords(item, cx - rx, cy - ry, cx + rx, cy + ry)
            c.itemconfigure(
                item,
                start=(18 + j * 122 + math.degrees(t * (.18 + j * .03))) % 360,
                outline=CYAN if listening and j == 0 else '#21344a',
            )

        for item, (x, y, z), i in self.particles:
            xr, zr = x * ca + z * sa, z * ca - x * sa
            yr, depth = y * ct - zr * st, y * st + zr * ct
            ripple = 1 + power * (.025 if gentle else .13) * math.sin(i * .43 + t * 14)
            perspective = 2.8 / (2.8 - depth * .45)
            px = cx + xr * radius * ripple * perspective
            py = cy + yr * radius * ripple * perspective
            bright = (depth + 1) / 2
            size = .6 + bright * 1.35 + power * .55
            color = '#%02x%02x%02x' % (
                int(95 + 160 * bright),
                int(52 + 139 * bright),
                int(24 + 78 * bright),
            )
            c.coords(item, px - size, py - size, px + size, py + size)
            c.itemconfigure(item, fill=color)

        for j, item in enumerate(self.filaments):
            points = []
            for k in range(FILAMENT_STEPS + 1):
                a = k * math.tau / FILAMENT_STEPS
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

        raw_state = self.state.get()
        if playing:
            label = 'Presence is speaking'
            hint = 'Notice what lands.'
        elif live and self.muted.get():
            label = 'Microphone muted'
            hint = 'Unmute when you’re ready to continue.'
        elif listening and self.hold.get():
            label = 'Listening'
            hint = 'Take all the time you need. I’ll wait.'
        elif listening:
            label = 'Listening'
            hint = 'I’m here.'
        elif raw_state.startswith('Connecting'):
            label = 'Connecting'
            hint = 'Preparing your coaching space.'
        elif raw_state.startswith('Stopping'):
            label = 'Closing the session'
            hint = 'Your transcript will remain available.'
        elif raw_state == 'Session complete':
            label = 'Session complete'
            hint = 'Keep what is useful. Leave what is not.'
        elif live:
            label = raw_state.replace('…', '').strip() or 'Thinking'
            hint = 'Presence is with your last thought.'
        else:
            label = 'Ready when you are'
            hint = 'A quiet space for whatever matters.'

        if self.display_state.get() != label:
            self.display_state.set(label)
        if self.display_hint.get() != hint:
            self.display_hint.set(hint)

        delay = REDUCED_MOTION_DELAY_MS if gentle else ANIMATION_DELAY_MS
        self.after(delay, self.animate)

    def save(self):
        if not self.transcript.rows:
            messagebox.showinfo('Transcript', 'There is no conversation to export yet.')
            return False

        filename = filedialog.asksaveasfilename(
            defaultextension='.txt',
            initialfile='Presence-Coach-session.txt',
            filetypes=[('Text file', '*.txt')],
        )
        if not filename:
            return False

        try:
            Path(filename).write_text(self.transcript.export(), encoding='utf-8')
        except OSError as exc:
            messagebox.showerror('Export failed', str(exc))
            return False

        self.dirty = False
        return True

    def confirm_unsaved(self):
        if self.dirty:
            choice = messagebox.askyesnocancel(
                'Save conversation?',
                'Export the current transcript before continuing?',
            )
            if choice is None:
                return False
            if choice is True and not self.save():
                return False

        engine = self.engine
        has_audio = bool(
            engine
            and hasattr(engine, 'has_audio')
            and engine.has_audio()
        )
        if has_audio and not self.audio_exported:
            return messagebox.askyesno(
                'Discard unexported session audio?',
                'This session still has audio in memory that has not been exported. '
                'Continue and permanently discard that audio?',
                icon='warning',
            )
        return True

    def close(self):
        if self.engine and self.engine.is_alive():
            self.stop()
            self.after(100, self.close)
            return
        if self.confirm_unsaved():
            self.destroy()


if __name__ == '__main__':
    App().mainloop()

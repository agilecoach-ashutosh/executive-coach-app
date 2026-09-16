"""Presence Coach desktop application. Run with Python 3.12+."""
import math
import time
import webbrowser
import queue
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import keyring
import sounddevice as sd
from coaching import Transcript
from engine import LiveEngine

BG, PANEL, CYAN, INK, MUTED = '#080f1c', '#101e30', '#ffb454', '#e8f2ff', '#90a6bc'


API_HELP = """GET YOUR GEMINI API KEY

1. Open aistudio.google.com and sign in with your Google account.
2. Open API keys (sometimes labelled Get API key).
3. Click Create API key. Choose or create a project when prompted. New accounts may already have a default key.
4. Copy the key and paste it into the Gemini API key field here.
5. Close Settings, tick the conversation consent box, then click Begin conversation.

If your project is missing, import it from AI Studio's Projects page. Keep your key private. Live model access and billing depend on your Google account.

Click this info button for links you can open.
Source: ai.google.dev/gemini-api/docs/api-key"""


class HoverHelp:
    def __init__(self, widget, text):
        self.widget, self.text, self.popup = widget, text, None
        widget.bind('<Enter>', self.show)
        widget.bind('<Leave>', self.hide)
        widget.bind('<FocusIn>', self.show)
        widget.bind('<FocusOut>', self.hide)
        widget.bind('<ButtonPress>', self.hide)
        widget.bind('<Destroy>', self.hide)

    def show(self, event=None):
        if self.popup:
            return
        self.popup = tk.Toplevel(self.widget)
        self.popup.overrideredirect(True)
        tk.Label(self.popup, text=self.text, wraplength=380, justify='left',
                 bg='#20344b', fg=INK, font=('Segoe UI', 10), padx=16, pady=14,
                 relief='solid', borderwidth=1).pack()
        self.popup.update_idletasks()
        x = min(self.widget.winfo_rootx(), self.widget.winfo_screenwidth()-self.popup.winfo_reqwidth()-12)
        y = min(self.widget.winfo_rooty()+self.widget.winfo_height()+6,
                self.widget.winfo_screenheight()-self.popup.winfo_reqheight()-40)
        self.popup.geometry(f'+{max(0,x)}+{max(0,y)}')

    def hide(self, event=None):
        if self.popup:
            self.popup.destroy()
            self.popup = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Presence Coach • A space to think')
        self.geometry('1180x780')
        self.minsize(1080, 700)
        self.configure(bg=BG)
        self.events, self.engine = queue.Queue(), None
        self.transcript = Transcript()
        self.dirty = False
        self.phase, self.level = 0, 0
        self.envelope = 0.0
        self.display_state = tk.StringVar(value='Ready when you are')
        self.reduced_motion = tk.BooleanVar(value=False)
        self.state = tk.StringVar(value='Ready when you are')
        self.key = tk.StringVar()
        try:
            self.key.set(keyring.get_password('PresenceCoach', 'gemini') or '')
        except Exception:
            pass
        self.model = tk.StringVar(value='gemini-3.1-flash-live-preview')
        self.voice = tk.StringVar(value='Kore')
        self.pause = tk.StringVar(value='6')
        self.threshold = tk.StringVar(value='0.018')
        self.remember = tk.BooleanVar(value=False)
        self.consent = tk.BooleanVar(value=False)
        self.hold, self.muted = tk.BooleanVar(), tk.BooleanVar()
        self.make_ui()
        self.make_settings()
        self.render()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(40, self.poll)
        self.after(40, self.animate)

    def label(self, parent, text, size=11, color=INK):
        return tk.Label(parent, text=text, font=('Segoe UI', size), bg=parent['bg'], fg=color)

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, font=('Segoe UI', 10, 'bold'),
                         bg=CYAN if primary else '#20344b', fg=BG if primary else INK,
                         activebackground='#9bf8ec', relief='flat', padx=14, pady=10, cursor='hand2')

    def make_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        header = tk.Frame(self, bg=BG)
        header.grid(row=0, column=0, sticky='ew', padx=28, pady=(20, 10))
        self.label(header, 'P R E S E N C E', 22, CYAN).pack(side='left')
        self.label(header, 'COACH  /  A SPACE TO THINK', 10, MUTED).pack(side='left', padx=18)
        self.button(header, 'Settings', self.open_settings).pack(side='right', padx=(8, 0))
        self.button(header, 'Save transcript', self.save).pack(side='right')
        body = tk.Frame(self, bg=BG)
        body.grid(row=2, column=0, sticky='nsew', padx=28, pady=(0, 12))
        left = tk.Frame(body, bg=PANEL, width=370)
        left.pack(side='left', fill='y', padx=(0, 18))
        left.pack_propagate(False)
        self.label(left, 'Y O U R   S P A C E   T O   T H I N K', 9, MUTED).pack(pady=(24, 6))
        self.orb = tk.Canvas(left, width=360, height=370, bg=PANEL, highlightthickness=0)
        self.orb.pack(fill='both', expand=True, padx=4)
        self.build_orb()
        tk.Label(left, textvariable=self.display_state, bg=PANEL, fg=CYAN,
                 font=('Segoe UI', 15, 'bold'), wraplength=340).pack(pady=8)
        self.label(left, 'One question. Your pace. Your direction.', 10, MUTED).pack(pady=(0, 16))
        tk.Checkbutton(left, text='Gentle motion', variable=self.reduced_motion,
                       bg=PANEL, fg=MUTED, selectcolor=BG, activebackground=PANEL,
                       activeforeground=INK).pack(pady=(0, 20))
        right = tk.Frame(body, bg=BG)
        right.pack(side='left', fill='both', expand=True)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(4, weight=1)
        self.label(right, 'YOUR CONVERSATION', 11, CYAN).grid(row=0, column=0, sticky='w')
        self.label(right, 'AI reflection partner • Informed by ICF principles • Not ICF-certified', 9, MUTED).grid(row=1, column=0, sticky='w', pady=(5, 12))
        textframe = tk.Frame(right, bg=PANEL)
        textframe.grid(row=4, column=0, sticky='nsew')
        self.log = tk.Text(textframe, bg=PANEL, fg=INK, font=('Segoe UI', 12), wrap='word',
                           relief='flat', padx=18, pady=18, state='disabled', spacing3=8, height=1, width=1)
        scrollbar = ttk.Scrollbar(textframe, command=self.log.yview)
        scrollbar.pack(side='right', fill='y')
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(fill='both', expand=True)
        self.log.tag_configure('Coach', foreground=CYAN)
        self.log.tag_configure('Coachee', foreground='#e9c57d')
        self.message = tk.StringVar()
        composer = tk.Frame(right, bg=BG)
        composer.grid(row=5, column=0, sticky='ew', pady=(10, 0))
        entry = ttk.Entry(composer, textvariable=self.message, font=('Segoe UI', 12))
        entry.pack(side='left', fill='x', expand=True, ipady=9)
        entry.bind('<Return>', lambda _: self.send())
        self.button(composer, 'Send', self.send).pack(side='right', padx=(8, 0))
        controls = tk.Frame(right, bg=BG)
        controls.grid(row=2, column=0, sticky='ew')
        self.start_button = self.button(controls, 'Begin conversation', self.start, True)
        self.start_button.pack(side='left')
        self.button(controls, 'End', self.stop).pack(side='left', padx=6)
        self.button(controls, 'Interrupt coach', lambda: self.command('interrupt')).pack(side='left')
        self.button(controls, 'I’m ready', lambda: self.command('finish')).pack(side='left', padx=6)
        options = tk.Frame(right, bg=BG)
        options.grid(row=3, column=0, sticky='ew', pady=8)
        for label, var, name in [('Take your time — wait until I’m ready', self.hold, 'hold'), ('Mute mic', self.muted, 'mute')]:
            tk.Checkbutton(options, text=label, variable=var, command=lambda n=name, v=var: self.command(n, v.get()),
                           bg=BG, fg=INK, selectcolor=PANEL, activebackground=BG, activeforeground=INK).pack(side='left')
        footer = tk.Frame(self, bg=BG)
        footer.grid(row=1, column=0, sticky='ew', padx=28, pady=(0, 12))
        tk.Checkbutton(footer, text='I agree to send this conversation to Google Gemini. API usage may be billed. Text is saved only when I export.',
                       variable=self.consent, bg=BG, fg=MUTED, selectcolor=PANEL, wraplength=1000, justify='left',
                       activebackground=BG, activeforeground=INK).pack(anchor='w')
        self.label(footer, 'Start → speak about what you want to explore. Use headphones for clarity. Export before starting a new session.', 9, MUTED).pack(anchor='w')

    def make_settings(self):
        self.settings = tk.Toplevel(self)
        self.settings.title('Presence • Settings')
        self.settings.configure(bg=PANEL)
        self.settings.geometry('560x700')
        self.settings.minsize(440, 420)
        self.settings.protocol('WM_DELETE_WINDOW', self.settings.withdraw)
        self.settings.bind('<Escape>', lambda _: self.settings.withdraw())
        self.settings.rowconfigure(1, weight=1)
        self.settings.columnconfigure(0, weight=1)
        self.label(self.settings, 'Make this space yours', 20, CYAN).grid(row=0, column=0, sticky='w', padx=20, pady=15)
        wrap = tk.Frame(self.settings, bg=PANEL)
        wrap.grid(row=1, column=0, sticky='nsew')
        canvas = tk.Canvas(wrap, bg=PANEL, highlightthickness=0)
        bar = ttk.Scrollbar(wrap, command=canvas.yview)
        bar.pack(side='right', fill='y')
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(fill='both', expand=True)
        left = tk.Frame(canvas, bg=PANEL)
        window = canvas.create_window((0, 0), window=left, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window, width=e.width))
        left.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))
        form = tk.Frame(left, bg=PANEL)
        form.pack(fill='x', padx=18)
        self.settings_widgets = []
        for label, variable, choices in [
            ('Gemini API key', self.key, None), ('Live model (editable)', self.model, ['gemini-3.8-live', 'gemini-3.1-flash-live-preview']),
            ('Voice', self.voice, ['Kore', 'Aoede', 'Puck', 'Charon', 'Fenrir']),
            ('Silence before reply (seconds)', self.pause, ['3', '6', '10', '15']),
            ('Mic threshold (lower = more sensitive)', self.threshold, ['0.008', '0.018', '0.035', '0.06'])]:
            heading = tk.Frame(form, bg=PANEL)
            heading.pack(fill='x')
            self.label(heading, label, 10, MUTED).pack(side='left')
            if variable is self.key:
                info = self.button(heading, 'ⓘ How to get a key', self.api_help)
                info.configure(font=('Segoe UI', 9), padx=8, pady=3)
                info.pack(side='right')
                self.key_tip = HoverHelp(info, API_HELP)
            if choices:
                widget = ttk.Combobox(form, textvariable=variable, values=choices)
            else:
                widget = ttk.Entry(form, textvariable=variable, show='•')
            widget.pack(fill='x', pady=(2, 5))
            self.settings_widgets.append(widget)
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
        for label, variable, values in [('Microphone', self.mic, inputs), ('Speaker / headphones', self.speaker, outputs)]:
            self.label(form, label, 9, MUTED).pack(anchor='w')
            widget = ttk.Combobox(form, textvariable=variable, values=values, state='readonly')
            widget.pack(fill='x', pady=(2, 5))
            self.settings_widgets.append(widget)
        tk.Checkbutton(form, text='Remember key in Windows Credential Manager', variable=self.remember,
                       bg=PANEL, fg=MUTED, selectcolor=BG, activebackground=PANEL, activeforeground=INK,
                       font=('Segoe UI', 8)).pack(anchor='w')
        self.button(form, 'Forget saved key', self.forget_key).pack(anchor='w', pady=6)
        self.label(form, 'Changes apply to the next conversation.', 10, MUTED).pack(anchor='w', pady=8)
        self.button(self.settings, 'Done', self.settings.withdraw, True).grid(row=2, column=0, sticky='e', padx=20, pady=12)
        self.settings.withdraw()

    def open_settings(self):
        self.settings.deiconify()
        self.settings.lift()
        self.settings.focus_set()

    def api_help(self):
        dialog = tk.Toplevel(self.settings)
        dialog.title('Get your Gemini API key')
        dialog.configure(bg=PANEL)
        dialog.transient(self.settings)
        text = tk.Label(dialog, text=API_HELP, wraplength=430, justify='left',
                        bg=PANEL, fg=INK, font=('Segoe UI', 11), padx=22, pady=22)
        text.pack(fill='both', expand=True)
        self.button(dialog, 'Open Google AI Studio', lambda: webbrowser.open('https://aistudio.google.com/')).pack(padx=22, pady=6, fill='x')
        self.button(dialog, 'Open API keys page', lambda: webbrowser.open('https://aistudio.google.com/api-keys')).pack(padx=22, pady=6, fill='x')
        self.button(dialog, 'Close', dialog.destroy).pack(pady=12)
        dialog.bind('<Escape>', lambda _: dialog.destroy())

    def start(self):
        if self.engine and self.engine.is_alive():
            return
        if not self.key.get().strip():
            self.open_settings()
            messagebox.showinfo('Connect your coach', 'Enter your Gemini API key in Settings. Use the info button for step-by-step help.', parent=self.settings)
            return
        if not self.consent.get():
            messagebox.showinfo('Before we begin', 'Tick the consent checkbox directly below the title, then begin your conversation.')
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
                messagebox.showwarning('Key storage', 'Could not remember the key securely. It will remain in memory for this run.')
        self.transcript = Transcript()
        self.dirty = False
        self.render()
        self.muted.set(False)
        self.hold.set(False)
        self.state.set('Connecting…')
        self.engine = LiveEngine(self.key.get().strip(), self.model.get().strip(), self.voice.get(),
                                 self.devices.get(self.mic.get()), self.devices.get(self.speaker.get()),
                                 self.events, pause, threshold)
        self.start_button.configure(state='disabled')
        self.engine.start()

    def command(self, name, value=None):
        if self.engine and self.engine.is_alive():
            self.engine.command(name, value)

    def send(self):
        text = self.message.get().strip()
        if not text:
            return
        if not self.engine or not self.engine.is_alive() or self.state.get() == 'Connecting…':
            messagebox.showinfo('Start a session', 'Start and connect before sending a message.')
            return
        self.command('text', text)
        self.message.set('')

    def stop(self):
        if self.engine and self.engine.is_alive():
            self.engine.stop()
            self.state.set('Stopping…')

    def forget_key(self):
        try:
            keyring.delete_password('PresenceCoach', 'gemini')
        except keyring.errors.PasswordDeleteError:
            pass
        except Exception:
            messagebox.showerror('Key storage', 'Could not delete the saved key. Check Windows Credential Manager.')
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
                self.state.set('Listening — what would you like to explore?')
            elif kind == 'disconnected':
                self.state.set('Session stopped • transcript available')
                self.start_button.configure(state='normal')
                self.level = 0
            elif kind == 'notice':
                self.transcript.boundary = True
                self.transcript.add('Session note', value)
                self.transcript.boundary = True
                self.dirty, changed = True, True
            elif kind == 'error':
                messagebox.showerror('Connection or audio issue', value + '\n\nCheck API key, quota, Live model access, and audio devices. Your transcript is still available.')
        if changed:
            self.render()
        self.after(40, self.poll)

    def render(self):
        bottom = self.log.yview()[1] >= .98
        position = self.log.yview()[0]
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')
        if not self.transcript.rows:
            self.log.insert('end', 'A little room to think.\n\nWhat would make this conversation useful for you?\n\nWhen connected, speak or type to begin.\n\n“Take your time” holds your turn through long pauses. Click “I’m ready” when you want a response.\n\nThe amber orb responds to your voice and the coach’s audio. Voice, microphone, and thinking time can be adjusted in Settings.')
        for stamp, role, text in self.transcript.rows:
            self.log.insert('end', f'{dict(Coachee="YOU", Coach="PRESENCE").get(role, role.upper())}  ·  {stamp}\n', role)
            self.log.insert('end', text + '\n\n')
        self.log.configure(state='disabled')
        if bottom:
            self.log.see('end')
        else:
            self.log.yview_moveto(position)

    def build_orb(self):
        # Reuse Canvas items: no per-frame deletion or allocations of Tk widgets.
        self.particles = []
        for i in range(650):
            y = 1 - 2 * (i + .5) / 650
            angle = i * math.pi * (3 - math.sqrt(5))
            ring = math.sqrt(1 - y*y)
            point = (ring * math.cos(angle), y, ring * math.sin(angle))
            item = self.orb.create_oval(0, 0, 1, 1, outline='', fill=CYAN)
            self.particles.append((item, point, i))
        self.filaments = [self.orb.create_line(0, 0, 1, 1, fill='#965522', width=1) for _ in range(12)]
        self.core = [self.orb.create_oval(0, 0, 1, 1, outline=color, width=width)
                     for color, width in [('#30291f', 14), ('#6d4421', 7), ('#b3742b', 3), ('#ffd694', 1)]]

    def animate(self):
        engine = self.engine
        live = bool(engine and engine.is_alive() and not engine.stopping.is_set())
        now = time.monotonic()
        playing = bool(live and getattr(engine, 'playback_until', 0) > now)
        talking = getattr(engine, 'output_level', 0) if playing else 0
        listening = live and self.state.get().startswith('Listening') and not self.muted.get()
        target = min(1., talking * 8 if playing else self.level * 10 if listening else 0)
        self.envelope += (target - self.envelope) * (.4 if target > self.envelope else .12)
        power = self.envelope
        gentle = self.reduced_motion.get()
        self.phase += .008 if gentle else .015 + power * .035
        t = self.phase
        c = self.orb
        w, h = max(1, c.winfo_width()), max(1, c.winfo_height())
        radius = min(w, h) * .33
        shake = 0 if gentle else power * 4
        cx = w/2 + math.sin(t*17) * shake
        cy = h/2 + math.cos(t*21) * shake
        ca, sa = math.cos(t), math.sin(t)
        tilt = .3 * math.sin(t*.7)
        ct, st = math.cos(tilt), math.sin(tilt)
        for item, (x, y, z), i in self.particles:
            xr, zr = x*ca + z*sa, z*ca - x*sa
            yr, depth = y*ct - zr*st, y*st + zr*ct
            ripple = 1 + power * (.025 if gentle else .13) * math.sin(i*.43 + t*14)
            perspective = 2.8 / (2.8-depth*.45)
            px, py = cx+xr*radius*ripple*perspective, cy+yr*radius*ripple*perspective
            bright = (depth+1)/2
            size = .6 + bright*1.3 + power*.5
            color = '#%02x%02x%02x' % (int(95+160*bright), int(52+139*bright), int(24+78*bright))
            c.coords(item, px-size, py-size, px+size, py+size)
            c.itemconfigure(item, fill=color)
        for j, item in enumerate(self.filaments):
            points = []
            for k in range(61):
                a = k * math.tau / 60
                rr = radius * (1 + .035 * math.sin(a*9+t*4+j) + power*.09*math.sin(a*17-t*9+j))
                # A set of rotating great-circle filaments around the particle sphere.
                x, y, z = math.cos(a), math.sin(a)*math.cos(j*.48+t*.16), math.sin(a)*math.sin(j*.48+t*.16)
                xr, zr = x*ca+z*sa, z*ca-x*sa
                yr = y*ct-zr*st
                points.extend((cx+xr*rr, cy+yr*rr))
            c.coords(item, *points)
        for j, item in enumerate(self.core):
            r = radius * (.13 + (3-j)*.035 + power*.08)
            c.coords(item, cx-r, cy-r, cx+r, cy+r)
        label = 'Speaking' if playing else self.state.get()
        if live and self.muted.get() and not playing:
            label = 'Microphone muted'
        elif listening and self.hold.get():
            label = 'Listening • take your time'
        if self.display_state.get() != label:
            self.display_state.set(label)
        self.after(40, self.animate)

    def save(self):
        if not self.transcript.rows:
            messagebox.showinfo('Transcript', 'There is no conversation to export yet.')
            return False
        filename = filedialog.asksaveasfilename(defaultextension='.txt', initialfile='Presence-Coach-session.txt',
                                              filetypes=[('Text file', '*.txt')])
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
        if not self.dirty:
            return True
        choice = messagebox.askyesnocancel('Save conversation?', 'Export the current transcript before continuing?')
        return self.save() if choice is True else choice is False

    def close(self):
        if self.engine and self.engine.is_alive():
            self.stop()
            self.after(100, self.close)
            return
        if self.confirm_unsaved():
            self.destroy()


if __name__ == '__main__':
    App().mainloop()

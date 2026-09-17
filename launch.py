"""Performance-optimized launcher for Presence Coach UI."""
import math
import time
import webbrowser
import tkinter as tk

import app as base


def build_orb(self):
    """Build a visually rich orb with less Canvas overhead."""
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
    """Animate efficiently so UI controls remain immediately responsive."""
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

    # Stars are static; only reposition when the Canvas size changes.
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

    # 41 points is visually smooth but materially cheaper than the old 61.
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

    # 20 fps remains fluid for this ambient orb and leaves Tk time for clicks/dialogs.
    self.after(50, self.animate)


def api_help(self):
    # Use Settings as the parent only when Settings is actually visible.
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
        ('2', 'Open API keys and create a key.'),
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
        'Open Google AI Studio ↗',
        lambda: webbrowser.open('https://aistudio.google.com/'),
        True,
    ).pack(fill='x', padx=24, pady=4)
    self.button(
        dialog,
        'Open API keys ↗',
        lambda: webbrowser.open('https://aistudio.google.com/api-keys'),
    ).pack(fill='x', padx=24, pady=4)
    self.button(dialog, 'Close', dialog.destroy, compact=True).pack(pady=(8, 18))
    dialog.bind('<Escape>', lambda _: dialog.destroy())

    # Give the help window focus immediately.
    dialog.update_idletasks()
    dialog.lift()
    dialog.focus_force()


base.App.build_orb = build_orb
base.App.animate = animate
base.App.api_help = api_help

if __name__ == '__main__':
    base.App().mainloop()

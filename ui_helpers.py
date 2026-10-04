"""Small shared helpers for readable desktop screens."""
import tkinter as tk


def fit_window(window, width, height, minimum=(700, 480)):
    """Keep dialogs on the screen, including laptops with display scaling."""
    available_w = max(320, window.winfo_screenwidth() - 60)
    available_h = max(240, window.winfo_screenheight() - 100)
    width, height = min(width, available_w), min(height, available_h)
    window.minsize(min(minimum[0], width), min(minimum[1], height))
    window.geometry(f"{width}x{height}+{max(0, (available_w-width)//2)}+{max(0, (available_h-height)//2)}")


def tooltip(widget, text):
    """Show control help on pointer hover or keyboard focus."""
    popup = None
    timer = None

    def hide(_event=None):
        nonlocal popup, timer
        if timer:
            widget.after_cancel(timer)
            timer = None
        if popup:
            popup.destroy()
            popup = None

    def show():
        nonlocal popup, timer
        timer = None
        if not widget.winfo_exists():
            return
        popup = tk.Toplevel(widget)
        popup.overrideredirect(True)
        label = tk.Label(popup, text=text, bg="#eef5ff", fg="#0d1724",
                         font=("Segoe UI", 10), wraplength=280, justify="left", padx=12, pady=8)
        label.pack()
        popup.update_idletasks()
        x = min(widget.winfo_rootx(), widget.winfo_screenwidth()-popup.winfo_reqwidth()-12)
        y = min(widget.winfo_rooty()+widget.winfo_height()+6,
                widget.winfo_screenheight()-popup.winfo_reqheight()-12)
        popup.geometry(f"+{max(0,x)}+{max(0,y)}")

    def schedule(_event=None):
        nonlocal timer
        hide()
        timer = widget.after(500, show)

    for event in ("<Enter>", "<FocusIn>"):
        widget.bind(event, schedule, add="+")
    for event in ("<Leave>", "<FocusOut>", "<ButtonPress>", "<Destroy>"):
        widget.bind(event, hide, add="+")

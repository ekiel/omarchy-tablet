#!/usr/bin/env python3
"""Disposable GTK4 field for manual or automated OSK/dictation checks.

Reports focus and character count only to /tmp/omarchy-tablet-input-probe.json.
Closes automatically after two minutes. Never records the field's text.
"""
import json
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

app = Gtk.Application(application_id="io.github.omarchy_tablet.InputProbe")


def activate(application):
    window = Gtk.ApplicationWindow(application=application, title="Omarchy Tablet input check")
    window.set_default_size(600, 250)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    for side in ("top", "bottom", "start", "end"):
        getattr(box, "set_margin_" + side)(24)
    box.append(Gtk.Label(label="Disposable input field — keyboard and dictation check"))
    entry = Gtk.Entry(placeholder_text="Tap here, then use the keyboard or microphone in the top bar")
    box.append(entry)
    window.set_child(box)
    window.present()
    entry.grab_focus()

    def report():
        focus = window.get_focus()
        Path("/tmp/omarchy-tablet-input-probe.json").write_text(json.dumps({
            "active": window.is_active(), "fieldFocused": focus is not None and (focus == entry or focus.is_ancestor(entry)),
            "characters": len(entry.get_text())}))
        return True
    GLib.timeout_add(100, report)
    GLib.timeout_add_seconds(120, lambda: (application.quit(), False)[1])


app.connect("activate", activate)
app.run()

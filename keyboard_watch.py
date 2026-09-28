#!/usr/bin/env python3
"""Report OSK visibility from D-Bus signals, without polling or starting it."""
import json
from gi.repository import Gio, GLib

proxy = Gio.DBusProxy.new_for_bus_sync(
    Gio.BusType.SESSION, Gio.DBusProxyFlags.DO_NOT_AUTO_START, None,
    'sm.puri.OSK0', '/sm/puri/OSK0', 'sm.puri.OSK0', None)


def report(*_):
    value = proxy.get_cached_property('Visible')
    print(json.dumps({'visible': bool(proxy.get_name_owner() and value and value.unpack())}), flush=True)


proxy.connect('g-properties-changed', report)
proxy.connect('notify::g-name-owner', report)
report()
GLib.MainLoop().run()

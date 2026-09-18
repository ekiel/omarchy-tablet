# Omarchy Tablet

A native Omarchy shell plugin for touch devices and detachable keyboards. Keep your wallpaper, theme and original status widgets; add a tablet Home, application search, window switching, an on-screen keyboard and dictation.

![Tablet Home in landscape with Tokyo Night colors](docs/screenshots/landscape-tokyo-night.png)

## What it does

- Hosts the widgets already configured in `shell.json`, including resources, AI quotas, audio, power, network, Bluetooth, clock, tray and indicators. Their original menus and actions remain available.
- Adds Home, Apps, Windows, keyboard and microphone controls. Tablet controls have a minimum 48-logical-pixel target. Desktop mode uses the shell's compact bar size.
- Moves secondary widgets into **More** in portrait or narrow layouts. Primary widgets can scroll horizontally when larger fonts need more room.
- Shows favorite applications over the Omarchy wallpaper. Use **All apps → Customize** to add or remove favorites; search works across all applications.
- Uses Omarchy's live `Color` and `Style` tokens for typography, colors, borders, transparency, spacing and corners. Adds no independent animation timing; native widgets retain their own animation behavior.
- Detects physical keyboard attachment independently of virtual keyboards. **Automatic**, **Tablet** and **Desktop** are available in More and Settings.
- Remembers **Single app** or **Omarchy tiling**. Single app maximizes eligible windows on the internal display below the bar, preserving the application's own fullscreen state. A recovery journal restores changed states on exit, reload or the next startup after a crash.
- Starts Squeekboard in tablet mode for compatible Wayland text fields, with a manual button for other applications.
- Runs `murmure --transcription` from the microphone button without taking keyboard focus. Configure a different executable and arguments in Settings. No speculative recording indicator is shown, and F9 is untouched.

## Requirements

Tested with the Quickshell-based Omarchy shell, Quickshell 0.3.1 and Hyprland 0.56.2 (Lua API), on a Surface at 2× display scale. This is **not a Waybar plugin**. It uses the installed shell's widget registry and `qs.Commons` API; older Omarchy releases are not supported.

Required: Python 3, `hyprctl`, `omarchy-shell`, systemd user services, `busctl`, `gsettings`, `gtk-launch` and `uwsm-app`. Install `squeekboard` for the virtual keyboard. Murmure is optional; any configured dictation command must already be installed and ready to run.

## Install and update

Clone this repository, review the source, then run from its root:

```sh
python3 install.py
```

The installer preserves your widget layout, writes the plugin into `$XDG_CONFIG_HOME/omarchy/plugins/surface.tablet`, saves the previous bar selection, and selects the tablet bar. It does not edit Hyprland configuration, rotation services, keybindings or the system theme. Updates use content-versioned QML paths to avoid stale components retained by shell rescanning.

After pulling an update, run `python3 install.py` again. Allow a few seconds for the shell to reload its plugins. If your shell does not recover, use `omarchy restart shell`.

Restore the previous bar:

```sh
python3 install.py --restore
```

This restores the previous bar ID and position while preserving widget edits and unrelated settings made since installation. Plugin files and favorites remain for reuse. You can also run the installed copy:

```sh
python3 ~/.config/omarchy/plugins/surface.tablet/install.py --restore
```

The backup is consumed after restoration so a later installation captures a fresh baseline. Installation needs no root privileges.

## Keyboard language and input

The interface is English; keyboard language is independent. This Surface's physical layout is French Canadian (`ca`). Squeekboard uses GNOME input sources. To choose French Canadian on your own machine:

```sh
python3 scripts/keyboard_language.py ca
# Restore the previous input sources if needed:
python3 scripts/keyboard_language.py --restore
```

See Squeekboard's [layout documentation](https://world.pages.gitlab.gnome.org/Phosh/squeekboard/layouts.html) for layout selection and custom layouts. Squeekboard may use its US terminal-specific layout when a Canadian terminal variant is unavailable; regular text fields use its built-in Canadian layout. Not every application supports Wayland text-input. Apps launched from Home receive `GTK_IM_MODULE=wayland` and `QT_IM_MODULE=wayland`; already running applications may need restarting with these settings. The keyboard button remains available for unsupported fields.

While Squeekboard owns the input method, the backend temporarily stops the known `omarchy-fcitx5.service` and enables the accessibility keyboard setting. It restores their original states when it stops. It does not terminate arbitrary input methods. Do not run another on-screen keyboard concurrently.

Dictation commands are parsed into an argument list, without implicit shell evaluation. Use a wrapper executable if a command needs pipes or shell syntax. The button does not change focus, read the selected field, or store dictated text. Transcription and any network use belong to the chosen dictation application.

## Layout boundaries

Single app changes only fullscreen/maximized state, through address-targeted [Hyprland dispatches](https://wiki.hypr.land/Configuring/Basics/Dispatchers/). Floating dialogs, pinned windows, special workspaces and grouped windows are left alone. External monitors retain their layout. An existing application fullscreen request remains fullscreen. Without an internal `eDP`, `DSI` or `LVDS` display, Single app leaves windows alone.

Omarchy tiling restores the states changed by this plugin. The plugin does not reconstruct a tiling tree you changed yourself while tablet mode was active. Hardware detection polls Linux input topology every half second; manual mode remains available for unusual keyboards.

## Commands

```sh
omarchy-shell tablet home
omarchy-shell tablet apps
omarchy-shell tablet close
omarchy-shell tablet mode auto       # auto, tablet, desktop, toggle
omarchy-shell tablet layout single   # single, tiling
omarchy-shell tablet keyboard
omarchy-shell tablet dictation
omarchy-shell tablet status
```

Preferences live in `$XDG_STATE_HOME/omarchy-tablet/preferences.json`. Runtime recovery leases live in `$XDG_RUNTIME_DIR/omarchy-tablet`. Window recovery is scoped to a compositor session and stable window identity; titles and window contents are not saved.

## Validation

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile tablet.py layout.py install.py
```

The opt-in `scripts/live_smoke.py` exercises the running desktop, temporarily changes palette, font size and rotation, captures Home, then restores settings. On this Surface it briefly pauses and restores `surface-autorotate.service`. `scripts/check_input.py` uses a disposable GTK field and requires PyGObject, GTK4 and `wtype`.

Read the [validation report](docs/validation.md) for evidence and remaining hands-on checks, and the [Omarchy presentation sheet](docs/omarchy-presentation.md) for a project introduction.

## License

MIT. Omarchy, Quickshell, application icons and the wallpaper shown in screenshots belong to their respective projects and authors. Native widgets are loaded from the installed Omarchy shell, not copied into this repository.

# Validation report

Validated locally on September 18, 2026. This report separates executed checks from tests that still need a person or extra hardware.

## Executed

| Area | Evidence |
| --- | --- |
| Backend and installer | 22 Python unit tests: attachment classification, mode overrides, favorites, layout and command persistence, invalid input, keyboard failure recovery, session-scoped window recovery, external-window exclusion, and reversible updates. |
| QML | All plugin QML files parsed with Qt 6 `qmlformat`; exercised in the running Omarchy shell. |
| Native widgets | All 14 configured entries instantiate through the native widget registry. Audio, Bluetooth, network, power, clock, resource monitor and AI quota panels opened and closed through shell routing. Original audio menu inspected visually. Hidden widgets retain their native visibility rules. |
| Layouts | Single app maximized the active internal window with internal state 1 and unchanged client state. Omarchy tiling restored state 0. Unit tests cover dialogs, external windows, groups, closed windows, reused addresses, failed dispatch and reload recovery. |
| Keyboard | Manual show/hide passed. A disposable GTK4 field caused Squeekboard to open automatically and accepted Wayland input. Desktop mode stopped the keyboard service. The accessibility setting is restored with the input-method lease. Canadian `ca_wide` was confirmed in Squeekboard logs for regular fields; terminal-purpose fields use its US fallback. |
| Theme and scale | Tokyo Night and Catppuccin Latte shell palettes applied live; 12px and 20px shell font sizes exercised. Original wallpaper retained. Theme and font settings restored afterward. |
| Orientation | Real internal monitor transform 0 and 1, asserted against `hyprctl monitors`. Existing autorotation service paused only during capture and restarted afterward. |
| Reload | Registry rescan recreated widgets and backend successfully. Installer uses content-versioned component URLs. Python bytecode writing is disabled in the installed service to avoid watcher-triggered reloads. |
| Installation | Temporary-directory tests verify updates preserve unrelated settings, restoration retains later widget edits, and reinstall captures a fresh baseline. Installed and updated on the Surface. A live restore/reinstall check also verifies the original bar, widget layout, idle settings, plugins, and accessibility keyboard setting. |

Raw live-check summary: [live-results.json](live-results.json). The images in [screenshots](screenshots) were captured from the running plugin and visually inspected. They are not generated mockups. “Latte” screenshots apply the shell palette while intentionally retaining the Surface wallpaper.

## Still needs hands-on confirmation

- Physically detach and reconnect the Type Cover. The connected state was detected live; detached topology and auto-mode transitions have automated coverage.
- Tap actual touch targets, especially the microphone, then speak into a disposable application field. The default command, availability, argument handling and focus-free bar configuration are verified; spoken recognition and insertion quality are not claimed as tested.
- Connect an external display and exercise dialogs across both displays. Exclusion and restoration logic have unit coverage; a physical second monitor was not available.
- Full interactive coverage of every native widget action (network changes, Bluetooth pairing, quota refresh, media controls) is not claimed. Popup lifecycle and the original component loading are verified.

Native shell code emits duplicate IPC-target warnings while multiple instances load, and weather-panel null-host messages can appear during teardown. These are recorded rather than represented as a completely warning-free shell run. The plugin does not patch packaged Omarchy components.

## Reproduce

```sh
python3 -m unittest discover -s tests -v
python3 scripts/live_smoke.py
python3 scripts/check_input.py
```

Run live checks only in an unlocked desktop session. They temporarily manipulate the visible desktop and write Home captures. `input_probe.py` logs only focus state and character count, never field contents. For a manual dictation check, launch it with `GTK_IM_MODULE=wayland python3 scripts/input_probe.py`, tap the microphone, speak, then tap it again. The disposable window closes after two minutes.

GitHub authentication and public publication remain pending. No upstream submission has been sent.

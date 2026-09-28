# Desktop/Tablet and keyboard controls — follow-up

> Historical development report. For the current behavior and release checks, see [README](../README.md) and [release readiness](release-readiness.md). Later sections may supersede earlier observations.

## Changes

- Restored the permanent Desktop/Tablet switch at the far left. Its monitor/tablet icon and selected state indicate the active mode. Tablet controls appear only in Tablet; Desktop keeps the native widgets. Both reserve a single 55-logical-pixel top bar with the current settings.
- Restored Desktop / Tablet / Automatic labels in Settings. Tablet continues to maximize the active application and supplies the app switcher.
- Keyboard CSS now imports Squeekboard's installed common styles and explicitly sizes `small-row` keys. The terminal's Esc, Tab, Ctrl, Alt, Shift and arrow labels fit inside their short keys again. The original keyboard layouts and language are preserved.
- Added an attached, themed keyboard toolbar with microphone and hide buttons. It reserves its own space directly above the keyboard without covering keys. D-Bus visibility signals show and hide it with the OSK. Its surface never requests keyboard focus.
- Dictation starts the OSK and keeps it available despite temporary text-input focus loss, until the user explicitly hides it or changes modes. Murmure receives `--hidden`; custom dictation commands remain unmodified. The microphone button toggles the configured dictation command and does not claim to know recording state.

## Checks

- 40 unit tests pass, including retained keyboard visibility, explicit hide releasing that behaviour, persistence and custom-command preservation.
- Python compilation and `git diff --check` pass.
- Real Wayland pointer clicks on the mode button switch in both directions. A real click on the keyboard Hide button dismisses the keyboard and retains focus in a disposable GTK field. Real OSK hide/show with a simulated speech executable verifies visibility recovery without recording audio.
- Desktop and Tablet show one row; the D-Bus watcher correctly follows visible/hidden state.
- Visually inspected the corrected terminal row: [screenshot](screenshots/keyboard-terminal-fixed.png).
- Actually switched from Everforest to Flexoki Light. Generated OSK CSS changed to background `#FFFCF0`, accent `#205EA6`; the attached controls and keys both changed appearance: [light-theme screenshot](screenshots/keyboard-flexoki-light.png). Style changes are applied after hiding/reopening the OSK.
- Restored Everforest after the test. Initial test runs needed harness corrections (the available terminal is Foot, and a field may already have opened the keyboard automatically). A shell restart was needed after repeated theme reloads caused IPC timeouts. No application reset or package files were modified.

## Limits

No actual speech was recorded during validation. Keyboard retention is exercised with a simulated speech executable and real OSK visibility changes; a complete Murmure recording/transcription remains a hands-on check. A manual hide does not cancel an ongoing Murmure recording. Theme application itself can make shell IPC slow during reloading.

## Manual activation follow-up

The OSK now starts only from the keyboard button, in either mode. Explicit hide stops the owned service and restores the prior input method/accessibility setting; `SetVisible(false)` alone allowed later text-input focus events to reopen it. Dictation retains an already enabled keyboard but does not start a hidden one.

42 unit tests pass, including no startup on tablet focus changes and no reopening from dictation after dismissal.

Live check passed: after explicit hide, focusing a disposable GTK text field and making three Home/switcher round trips did not start the service or show the keyboard. The keyboard button reopened it successfully, and toggling it off stopped the service even in Tablet mode. The prior mode was restored after the check.

## Contextual automatic activation (latest preference)

Added Settings → Keyboard activation with Automatic (default in Tablet) and Button only. Automatic leaves Squeekboard listening to Wayland text-input activation/deactivation; manual mode retains stop-on-hide. Opening the switcher dismisses the current keyboard and releases the dictation visibility guard. That guard is now bounded to two seconds, so it cannot indefinitely prevent automatic hiding. A return to a still-active text field may legitimately reopen the keyboard; the input method does not distinguish that from a fresh field activation.

45 unit tests pass, including automatic service lifetime, manual preference persistence, expiry of the dictation guard, and one-time dismissal of stale OSK visibility on a new window.

Automatic mode also dismisses the previous keyboard once on a change of active window; repeated focus/title events for the same window do not interfere with text-input activation. This avoids carrying the old keyboard into a newly focused window with no text field.

Live Wayland pointer test passed on a disposable GTK window: initial non-text control leaves the keyboard hidden; clicking the entry opens it; clicking the non-text button hides it; opening/closing the switcher keeps it hidden; clicking the entry again reopens it. Pure programmatic focus is not equivalent to a pointer click in this GTK/Squeekboard setup, so the final check uses actual virtual-pointer clicks.

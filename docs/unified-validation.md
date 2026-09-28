# Unified bar and keyboard styles — 2026-09-27

> Historical development report. For the current behavior and release checks, see [README](../README.md) and [release readiness](release-readiness.md). Later sections may supersede earlier observations.

Applied to the running Surface session with `python3 install.py`. Existing uncommitted work was preserved. The previous installed manifest and shell configuration were copied to `/tmp/omarchy-tablet-before` before installation (temporary backup).

## Verified

- 39 Python unit tests pass, including theme palette fallback/validation, light-theme colour generation, style selection persistence and deferring keyboard restart until hidden.
- Python compilation and `git diff --check` pass.
- Running shell: all 14 configured native widgets load. Both desktop and tablet window behaviours reserve one 55-logical-pixel bar. The underlying native widgets retain their 43-pixel sizing.
- Live portrait check at scale 2: 575-pixel system viewport and 864-pixel content width. One horizontal scroll area, six pinned touch actions and no second row. Original monitor scale and orientation were restored in `finally`.
- Opened and visually inspected all three keyboard appearances. Squeekboard logs confirm the generated resource overlay was loaded; no CSS parsing errors were observed. Canadian wide layout remains selected.
- Live disposable GTK field: automatic keyboard opening and text input pass (`scripts/check_input.py`); no Hyprland configuration errors reported.
- Original window preference and default Omarchy keyboard style restored after appearance checks.

Geometry evidence: [unified-validation.json](unified-validation.json).

## Captures

- [Omarchy keyboard](screenshots/keyboard-omarchy.png)
- [Rounded keyboard](screenshots/keyboard-rounded.png)
- [High contrast keyboard](screenshots/keyboard-contrast.png)
- [Settings](screenshots/unified-settings.png)
- [Portrait bar and settings](screenshots/unified-portrait.png)

## Boundaries

Physical touch accuracy, hardware keyboard detachment and microphone transcription were not exercised. The live portrait check verifies layout/overflow, not a physical swipe. Light palette handling and deferred style reload were checked in unit tests; the live appearance captures use the existing Everforest theme. The shell emitted transient invalid-context warnings while replacing QML components during installation; no recurring warnings were observed afterward. Squeekboard's existing GNOME session-manager warning and XKB modifier-map warnings remain in the session logs.

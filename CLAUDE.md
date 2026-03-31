# JARVIS Clap Launcher

Cross-platform clap-activated launcher for Claude Code. Iron Man / Tony Stark themed.

## Project Rules

- This is a fun, open-source product — keep the tone playful and on-brand
- Cross-platform is a hard requirement: every change must work on macOS, Windows, and Linux
- Music playback uses a cascading fallback: Apple Music → YouTube → local file → system chime
- The clap detection logic in `ClapDetector` is tested and calibrated — do not change threshold defaults without testing
- `play_music.sh` exists for backward compatibility with the macOS LaunchAgent — do not remove it
- Python 3.9+ compatibility required (use `from __future__ import annotations`)
- No external dependencies beyond `sounddevice` and `numpy`
- Keep it as a single-file script (`clap_launcher.py`) — resist splitting into a package unless complexity demands it

## When Debugging Audio Issues

- Check `--list-devices` output first
- PortAudio errors on macOS usually mean microphone permissions
- On Windows, check Settings > Privacy > Microphone
- On Linux, check PulseAudio/PipeWire with `pactl list sources short`
- Use `--threshold 0.1` to test if the mic is picking up anything at all

## When Adding New Platform Support

- Add the platform branch to every function in the Platform section
- Test that `--help` still works (catches import errors)
- Update the platform matrix table in README.md
- Follow the existing pattern: `if IS_MAC / elif IS_WIN / elif IS_LINUX`

## When Adding New Features

- New CLI flags need defaults that preserve current behavior
- Every feature must degrade gracefully — if a platform lacks support, skip silently
- Update README.md examples section
- Keep the Tony Stark personality in user-facing strings

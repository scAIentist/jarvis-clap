#!/usr/bin/env python3
"""
JARVIS Clap Launcher — Cross-Platform Edition
==============================================
Double-clap to wake up Claude Code, just like Tony Stark.

Platforms: macOS, Windows, Linux
Music:     Apple Music → YouTube fallback → local file → system chime

Lifecycle (runs forever):
  1. If Claude is running → sleep and wait for it to quit
  2. Once Claude quits → start listening for double-clap
  3. Double-clap detected → launch Claude + play AC/DC
  4. Go back to step 1

Runs automatically on macOS startup via LaunchAgent.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
import webbrowser

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    print(
        "Missing dependencies. Install with:\n"
        "  pip install sounddevice numpy\n"
    )
    sys.exit(1)

# ─── Platform Detection ─────────────────────────────────────────────────────

SYSTEM = platform.system()  # 'Darwin', 'Windows', 'Linux'
IS_MAC = SYSTEM == "Darwin"
IS_WIN = SYSTEM == "Windows"
IS_LINUX = SYSTEM == "Linux"

# Enable ANSI escape codes on Windows 10+ (static call, no user input)
if IS_WIN:
    subprocess.run(
        ["cmd", "/c", "chcp", "65001"],
        capture_output=True,
    )

# ─── Configuration ───────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "SAMPLE_RATE": 44100,
    "BLOCK_SIZE": 1024,
    "CLAP_THRESHOLD": 0.35,
    "CLAP_MAX_GAP": 0.7,
    "CLAP_MIN_GAP": 0.08,
    "POLL_INTERVAL": 5,
    "APP_NAME": "Claude",
    "SONG_NAME": "Back In Black",
    "SONG_START": 6,
    "YOUTUBE_VIDEO_ID": "pAgnJDJN4VA",
    "NO_MUSIC": False,
}

# ─── Terminal Styling ────────────────────────────────────────────────────────

CYAN    = "\033[96m"
YELLOW  = "\033[93m"
GREEN   = "\033[92m"
RED     = "\033[91m"
MAGENTA = "\033[95m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

BANNER = f"""
{CYAN}{BOLD}
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
{RESET}
{DIM}  Double-clap to wake up Claude Code.{RESET}
{DIM}  "Wake up, daddy's home."{RESET}
"""

# ─── Platform: Process Detection ─────────────────────────────────────────────

def is_app_running(app_name: str) -> bool:
    """Check if an application is currently running (cross-platform)."""
    try:
        if IS_WIN:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {app_name}.exe", "/NH"],
                capture_output=True, text=True, timeout=5,
            )
            return app_name.lower() in result.stdout.lower()
        else:
            # macOS and Linux both support pgrep
            result = subprocess.run(
                ["pgrep", "-xi", app_name],
                capture_output=True, timeout=3,
            )
            return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# ─── Platform: Text-to-Speech ────────────────────────────────────────────────

def speak(text: str) -> None:
    """JARVIS-style voice announcement (cross-platform)."""
    try:
        if IS_MAC:
            subprocess.Popen(
                ["say", "-v", "Daniel", "-r", "180", text],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif IS_WIN:
            escaped = text.replace("'", "''").replace('"', '`"')
            ps_script = (
                "Add-Type -AssemblyName System.Speech; "
                "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$synth.Speak('{escaped}')"
            )
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_script],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif IS_LINUX:
            for tts in ["espeak-ng", "espeak"]:
                if shutil.which(tts):
                    subprocess.Popen(
                        [tts, text],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    break
    except FileNotFoundError:
        pass


# ─── Platform: Sound Playback ────────────────────────────────────────────────

def play_sound(path: str) -> None:
    """Play a WAV/audio file (cross-platform)."""
    if not os.path.exists(path):
        return
    try:
        if IS_MAC:
            subprocess.Popen(
                ["afplay", path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif IS_WIN:
            if path.lower().endswith(".wav"):
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                subprocess.Popen(
                    ["cmd", "/c", "start", "", path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
        elif IS_LINUX:
            for player in ["paplay", "aplay", "ffplay"]:
                if shutil.which(player):
                    cmd = [player, path]
                    if player == "ffplay":
                        cmd = [player, "-nodisp", "-autoexit", path]
                    subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    break
    except Exception:
        pass


def play_system_chime() -> None:
    """Play a platform-native notification sound as last resort."""
    try:
        if IS_MAC:
            subprocess.Popen(
                ["afplay", "/System/Library/Sounds/Glass.aiff"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif IS_WIN:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        elif IS_LINUX:
            if shutil.which("paplay"):
                for path in [
                    "/usr/share/sounds/freedesktop/stereo/complete.oga",
                    "/usr/share/sounds/ubuntu/stereo/system-ready.ogg",
                ]:
                    if os.path.exists(path):
                        subprocess.Popen(
                            ["paplay", path],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        )
                        break
    except Exception:
        pass


# ─── Platform: Window Management ─────────────────────────────────────────────

def bring_to_front(app_name: str) -> None:
    """Bring an application window to the foreground."""
    try:
        if IS_MAC:
            for name in [app_name, f"{app_name} Code"]:
                result = subprocess.run(
                    ["osascript", "-e", f'tell application "{name}" to activate'],
                    capture_output=True, timeout=3,
                )
                if result.returncode == 0:
                    return
        elif IS_WIN:
            ps_script = (
                '$wsh = New-Object -ComObject WScript.Shell; '
                f'$wsh.AppActivate("{app_name}")'
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, timeout=3,
            )
        elif IS_LINUX:
            if shutil.which("wmctrl"):
                subprocess.run(
                    ["wmctrl", "-a", app_name],
                    capture_output=True, timeout=3,
                )
            elif shutil.which("xdotool"):
                subprocess.run(
                    ["xdotool", "search", "--name", app_name, "windowactivate"],
                    capture_output=True, timeout=3,
                )
    except Exception:
        pass


# ─── Music Playback (Cascading Fallback) ─────────────────────────────────────

def play_music(config: dict, music_file: str | None = None) -> bool:
    """
    Play entrance music with cascading fallback:
      1. Local file (if --music provided)
      2. Apple Music (macOS only, song must be in library)
      3. YouTube (all platforms — opens browser at timestamp)
      4. Bundled entrance.wav chime
    """
    if config.get("NO_MUSIC"):
        return False

    # 1. Local file override
    if music_file and os.path.exists(music_file):
        play_sound(music_file)
        print(f"  {DIM}♫ Playing: {os.path.basename(music_file)}{RESET}")
        return True

    # 2. Apple Music (macOS only)
    if IS_MAC:
        if _play_apple_music(config):
            print(f"  {DIM}♫ Playing via Apple Music{RESET}")
            return True

    # 3. YouTube fallback (all platforms)
    if _play_youtube(config):
        return True

    # 4. Bundled entrance chime
    entrance = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entrance.wav")
    if os.path.exists(entrance):
        play_sound(entrance)
        print(f"  {DIM}♫ Playing entrance chime{RESET}")
        return True

    return False


def _play_apple_music(config: dict) -> bool:
    """Try playing via Apple Music (macOS only). Returns False on any failure."""
    try:
        subprocess.run(
            ["osascript", "-e", 'tell application "Music" to activate'],
            capture_output=True, timeout=5,
        )
        time.sleep(2)
        script = (
            'tell application "Music"\n'
            f'    set theTrack to first track of playlist "Library" '
            f'whose name is "{config["SONG_NAME"]}"\n'
            '    play theTrack\n'
            '    delay 1\n'
            f'    set player position to {config["SONG_START"]}\n'
            'end tell'
        )
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def _play_youtube(config: dict) -> bool:
    """Open YouTube in the default browser at the configured timestamp."""
    video_id = config.get("YOUTUBE_VIDEO_ID", "pAgnJDJN4VA")
    start = config.get("SONG_START", 6)
    url = f"https://www.youtube.com/watch?v={video_id}&t={start}"
    try:
        webbrowser.open(url)
        print(f"  {DIM}♫ Playing via YouTube{RESET}")
        return True
    except Exception:
        return False


# ─── App Launcher ────────────────────────────────────────────────────────────

def _find_claude_windows() -> str | None:
    """Search common Windows install paths for Claude Desktop."""
    local_app = os.environ.get("LOCALAPPDATA", "")
    if not local_app:
        return None

    search_roots = [
        os.path.join(local_app, "Programs", "claude-desktop"),
        os.path.join(local_app, "AnthropicClaude"),
        os.path.join(local_app, "Claude"),
    ]

    for root in search_roots:
        direct = os.path.join(root, "Claude.exe")
        if os.path.exists(direct):
            return direct
        if os.path.isdir(root):
            try:
                for entry in sorted(os.listdir(root), reverse=True):
                    if entry.startswith("app-"):
                        exe = os.path.join(root, entry, "Claude.exe")
                        if os.path.exists(exe):
                            return exe
            except OSError:
                continue
    return None


def launch_app(app_name: str) -> bool:
    """Launch the target application (cross-platform)."""
    if IS_MAC:
        for name in [app_name, f"{app_name} Code"]:
            try:
                result = subprocess.run(
                    ["open", "-a", name],
                    capture_output=True, timeout=5,
                )
                if result.returncode == 0:
                    print(f"{GREEN}  {name} launched.{RESET}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        # Fallback: launch CLI in Terminal
        try:
            subprocess.Popen(
                ["osascript", "-e",
                 'tell application "Terminal" to do script "claude"'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            print(f"{GREEN}  Claude Code launched via Terminal.{RESET}")
            return True
        except Exception:
            pass

    elif IS_WIN:
        exe = _find_claude_windows()
        if exe:
            try:
                subprocess.Popen([exe])
                print(f"{GREEN}  Claude launched.{RESET}")
                return True
            except Exception:
                pass
        # Try shell start
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", app_name],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            print(f"{GREEN}  {app_name} launched.{RESET}")
            return True
        except Exception:
            pass
        # Fallback: CLI in cmd
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k", "claude"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            print(f"{GREEN}  Claude Code launched via cmd.{RESET}")
            return True
        except Exception:
            pass

    elif IS_LINUX:
        for cmd in ["claude-desktop", app_name.lower(), "claude"]:
            if shutil.which(cmd):
                subprocess.Popen(
                    [cmd],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                print(f"{GREEN}  {app_name} launched.{RESET}")
                return True
        for term in ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]:
            if shutil.which(term):
                term_cmd = (
                    [term, "--", "claude"] if term == "gnome-terminal"
                    else [term, "-e", "claude"]
                )
                subprocess.Popen(
                    term_cmd,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                print(f"{GREEN}  Claude Code launched via {term}.{RESET}")
                return True

    print(f"{RED}  Could not launch {app_name}.{RESET}")
    return False


# ─── Launch Sequence ─────────────────────────────────────────────────────────

def launch_claude(config: dict, music_file: str | None) -> bool:
    """The full Iron Man activation sequence."""
    print(f"\n{MAGENTA}{BOLD}  *CLAP CLAP*{RESET}")
    print(f"{GREEN}{BOLD}  >> Wake up, daddy's home.{RESET}\n")

    music_played = play_music(config, music_file)
    speak("Welcome back sir. Initializing all systems.")

    app_name = config["APP_NAME"]
    launched = launch_app(app_name)

    if launched and not music_played:
        play_system_chime()

    if launched:
        time.sleep(1)
        bring_to_front(app_name)

    return launched


# ─── Clap Detector ───────────────────────────────────────────────────────────

class ClapDetector:
    def __init__(self, config: dict, music_file: str | None, device: int | None = None):
        self.config = config
        self.music_file = music_file
        self.device = device
        self.last_clap_time = 0.0
        self.clap_count = 0
        self.listening = True
        self.launched = False
        self.peak_display_time = 0.0

    def reset(self):
        """Reset state for a new listening session."""
        self.last_clap_time = 0.0
        self.clap_count = 0
        self.listening = True
        self.launched = False
        self.peak_display_time = 0.0

    def audio_callback(self, indata, frames, time_info, status):
        if not self.listening:
            return

        now = time.time()
        peak = np.max(np.abs(indata))

        if now - self.peak_display_time > 0.5:
            bars = int(peak * 40)
            bar_color = GREEN if peak < self.config["CLAP_THRESHOLD"] else YELLOW
            level = f"{bar_color}{'|' * bars}{DIM}{'.' * (40 - bars)}{RESET}"
            print(
                f"\r  {DIM}Level:{RESET} [{level}] {DIM}{peak:.3f}{RESET}  ",
                end="", flush=True,
            )
            self.peak_display_time = now

        if peak >= self.config["CLAP_THRESHOLD"]:
            gap = now - self.last_clap_time

            if gap < self.config["CLAP_MIN_GAP"]:
                return

            if gap <= self.config["CLAP_MAX_GAP"] and self.clap_count == 1:
                self.clap_count = 0
                self.launched = launch_claude(self.config, self.music_file)
                self.listening = False
            else:
                self.clap_count = 1
                print(
                    f"\r{YELLOW}  Clap 1 detected... "
                    f"waiting for second clap{RESET}    ",
                    flush=True,
                )

            self.last_clap_time = now

        elif (self.clap_count == 1
              and (now - self.last_clap_time) > self.config["CLAP_MAX_GAP"]):
            self.clap_count = 0

    def listen(self) -> bool:
        """Listen for a double-clap. Returns True if app was launched."""
        self.reset()

        if self.device is not None:
            dev_info = sd.query_devices(self.device)
        else:
            dev_info = sd.query_devices(kind="input")

        print(f"  {DIM}Input: {dev_info['name']}{RESET}")
        print(f"  {DIM}Threshold: {self.config['CLAP_THRESHOLD']}{RESET}")
        print(f"\n{CYAN}  Listening for double-clap...{RESET}\n")

        try:
            with sd.InputStream(
                samplerate=self.config["SAMPLE_RATE"],
                blocksize=self.config["BLOCK_SIZE"],
                channels=1,
                callback=self.audio_callback,
                device=self.device,
            ):
                while self.listening:
                    time.sleep(0.1)
        except sd.PortAudioError as e:
            print(f"\n{RED}  Microphone error: {e}{RESET}")
            if IS_MAC:
                print(f"  {DIM}System Preferences > Privacy & Security > Microphone{RESET}")
            elif IS_WIN:
                print(f"  {DIM}Settings > Privacy > Microphone{RESET}")
            elif IS_LINUX:
                print(f"  {DIM}Check: pactl list sources short{RESET}")
            return False

        return self.launched


# ─── Main Loop ───────────────────────────────────────────────────────────────

def wait_for_app_to_quit(app_name: str, poll_interval: int):
    """Block until the target app is no longer running."""
    print(f"  {GREEN}{app_name} is running. Watching for quit...{RESET}")
    while is_app_running(app_name):
        time.sleep(poll_interval)
    print(f"\n  {YELLOW}{app_name} has quit.{RESET}")
    time.sleep(2)


def run_forever(config: dict, music_file: str | None, device: int | None):
    """
    Main lifecycle loop:
      App running? → wait for quit
      App quit?    → listen for claps
      Claps!       → launch + play music → loop back
    """
    print(BANNER)

    system_label = {"Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"}.get(
        SYSTEM, SYSTEM
    )
    print(f"  {DIM}Platform: {system_label} ({platform.machine()}){RESET}")
    print(f"  {DIM}Target app: {config['APP_NAME']}{RESET}")

    if not config.get("NO_MUSIC"):
        print(f"  {DIM}Song: {config['SONG_NAME']} (skip to {config['SONG_START']}s){RESET}")
        if IS_MAC:
            print(f"  {DIM}Music source: Apple Music → YouTube → entrance chime{RESET}")
        else:
            print(f"  {DIM}Music source: YouTube → entrance chime{RESET}")
    else:
        print(f"  {DIM}Music: disabled{RESET}")

    print()

    detector = ClapDetector(config, music_file, device)
    app_name = config["APP_NAME"]

    while True:
        if is_app_running(app_name):
            wait_for_app_to_quit(app_name, config["POLL_INTERVAL"])

        print(f"\n{CYAN}{BOLD}  JARVIS is ready. Awaiting your command.{RESET}")
        launched = detector.listen()

        if launched:
            print(f"\n{GREEN}  Mission accomplished.{RESET}")
            print(f"  {DIM}Watching for {app_name} to quit...{RESET}\n")
            time.sleep(5)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def list_devices():
    """Show available audio input devices."""
    print(f"\n{CYAN}{BOLD}  Available audio input devices:{RESET}\n")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            default = " (default)" if i == sd.default.device[0] else ""
            print(f"  {GREEN}[{i}]{RESET} {dev['name']}{DIM}{default}{RESET}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS — Double-clap to launch Claude Code, Tony Stark style.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "  Examples:\n"
            "    python clap_launcher.py                          # defaults\n"
            "    python clap_launcher.py --threshold 0.5          # less sensitive\n"
            "    python clap_launcher.py --app Cursor              # launch Cursor\n"
            "    python clap_launcher.py --youtube-id dQw4w9WgXcQ  # different song\n"
            "    python clap_launcher.py --no-music                # silent launch\n"
            "    python clap_launcher.py --list-devices            # show mic options\n"
        ),
    )
    parser.add_argument(
        "--threshold", type=float,
        default=DEFAULT_CONFIG["CLAP_THRESHOLD"],
        help=f"Clap sensitivity 0.0-1.0 (default: {DEFAULT_CONFIG['CLAP_THRESHOLD']})",
    )
    parser.add_argument(
        "--gap", type=float,
        default=DEFAULT_CONFIG["CLAP_MAX_GAP"],
        help=f"Max seconds between claps (default: {DEFAULT_CONFIG['CLAP_MAX_GAP']})",
    )
    parser.add_argument(
        "--music", type=str, default=None,
        help="Path to a local entrance music file (mp3/m4a/wav)",
    )
    parser.add_argument(
        "--device", type=int, default=None,
        help="Audio input device index (see --list-devices)",
    )
    parser.add_argument(
        "--list-devices", action="store_true",
        help="List available audio input devices and exit",
    )
    parser.add_argument(
        "--app", type=str,
        default=DEFAULT_CONFIG["APP_NAME"],
        help=f"Application to launch (default: {DEFAULT_CONFIG['APP_NAME']})",
    )
    parser.add_argument(
        "--song", type=str,
        default=DEFAULT_CONFIG["SONG_NAME"],
        help=f"Song name for Apple Music lookup (default: {DEFAULT_CONFIG['SONG_NAME']})",
    )
    parser.add_argument(
        "--song-start", type=int,
        default=DEFAULT_CONFIG["SONG_START"],
        help=f"Seconds to skip into the song (default: {DEFAULT_CONFIG['SONG_START']})",
    )
    parser.add_argument(
        "--youtube-id", type=str,
        default=DEFAULT_CONFIG["YOUTUBE_VIDEO_ID"],
        help="YouTube video ID for fallback music (default: Back In Black)",
    )
    parser.add_argument(
        "--no-music", action="store_true",
        help="Launch without any music",
    )

    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        sys.exit(0)

    config = DEFAULT_CONFIG.copy()
    config["CLAP_THRESHOLD"] = args.threshold
    config["CLAP_MAX_GAP"] = args.gap
    config["APP_NAME"] = args.app
    config["SONG_NAME"] = args.song
    config["SONG_START"] = args.song_start
    config["YOUTUBE_VIDEO_ID"] = args.youtube_id
    config["NO_MUSIC"] = args.no_music

    music_file = args.music
    if music_file and not os.path.exists(music_file):
        print(f"{RED}  Music file not found: {music_file}{RESET}")
        sys.exit(1)

    # Graceful shutdown
    def shutdown(*_):
        print(f"\n\n{DIM}  JARVIS signing off. Goodbye, sir.{RESET}\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    run_forever(config, music_file, args.device)


if __name__ == "__main__":
    main()

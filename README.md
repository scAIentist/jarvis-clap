# JARVIS

**Double-clap to launch Claude Code. Tony Stark style.**

```
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
```

JARVIS listens for a double-clap through your microphone, then launches Claude Code with AC/DC's "Back In Black" — because every coding session deserves an entrance.

Works on **macOS**, **Windows**, and **Linux**.

## What Happens When You Clap

1. JARVIS detects a double-clap via your microphone
2. AC/DC starts playing (Apple Music on Mac, YouTube everywhere else)
3. Claude Code launches and comes to the foreground
4. JARVIS announces: *"Welcome back sir. Initializing all systems."*
5. JARVIS watches for Claude to quit, then listens for the next clap

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/jarvis-clap.git
cd jarvis-clap

# Install dependencies
pip install sounddevice numpy

# Run
python clap_launcher.py
```

Then clap twice.

## Music Fallback Chain

JARVIS tries to play your entrance music in this order:

| Priority | Source | Platform | Notes |
|----------|--------|----------|-------|
| 1 | Local file | All | Pass `--music path/to/song.mp3` |
| 2 | Apple Music | macOS only | Song must be in your Library |
| 3 | YouTube | All | Opens browser at the right timestamp |
| 4 | Entrance chime | All | Bundled `entrance.wav` sci-fi sound |

## Configuration

```bash
# Adjust clap sensitivity (0.0 = hair trigger, 1.0 = sledgehammer)
python clap_launcher.py --threshold 0.5

# Use a different song in Apple Music
python clap_launcher.py --song "Thunderstruck" --song-start 0

# Use a different YouTube video
python clap_launcher.py --youtube-id dQw4w9WgXcQ

# Launch a different app (Cursor, VS Code, etc.)
python clap_launcher.py --app Cursor

# No music, just launch
python clap_launcher.py --no-music

# Pick a specific microphone
python clap_launcher.py --list-devices
python clap_launcher.py --device 2
```

## Platform Support

| Feature | macOS | Windows | Linux |
|---------|-------|---------|-------|
| Clap detection | Yes | Yes | Yes |
| Apple Music | Yes | - | - |
| YouTube fallback | Yes | Yes | Yes |
| Voice (TTS) | `say` (Daniel) | SAPI | espeak |
| App launch | `open -a` | Start Menu / exe path | Desktop / terminal |
| Window focus | AppleScript | WScript.Shell | wmctrl / xdotool |
| System chime | Glass.aiff | MessageBeep | freedesktop sounds |

### Windows Requirements

- Windows 10 or later (for ANSI terminal colors)
- Python 3.9+
- A microphone (grant access in Settings > Privacy > Microphone)
- Claude Desktop installed

### Linux Requirements

- Python 3.9+
- PortAudio (`sudo apt install libportaudio2` on Debian/Ubuntu)
- Optional: `espeak-ng` for voice, `wmctrl` for window focus

## Auto-Start on macOS

JARVIS can start automatically when you log in using a LaunchAgent:

```bash
# Create the plist
cat > ~/Library/LaunchAgents/com.jarvis.clap.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jarvis.clap</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/YOUR_USERNAME/jarvis/clap_launcher.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load it
launchctl load ~/Library/LaunchAgents/com.jarvis.clap.plist
```

## How It Works

The clap detector runs in a real-time audio callback via PortAudio. It measures peak amplitude in each audio block (1024 samples at 44.1kHz). When two peaks above the threshold occur within 0.08-0.7 seconds of each other, that's a double-clap.

The level meter in the terminal shows your ambient noise level, making it easy to calibrate the `--threshold` value for your environment.

## License

MIT

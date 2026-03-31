#!/bin/bash
osascript -e 'tell application "Music" to activate'
sleep 2
osascript -e '
tell application "Music"
    set theTrack to first track of playlist "Library" whose name is "Back In Black"
    play theTrack
    delay 1
    set player position to 6
end tell
'
osascript -e 'tell application "Claude" to activate'

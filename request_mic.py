#!/usr/bin/env python3
"""Request microphone permission from macOS. Run this once to trigger the prompt."""
import AVFoundation
import time

print("Requesting microphone access...")
print("You should see a macOS permission popup — click ALLOW.")
print()

result = [None]

def callback(granted):
    result[0] = granted

AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
    AVFoundation.AVMediaTypeAudio, callback
)

# Wait for user to respond to the dialog
for _ in range(60):
    if result[0] is not None:
        break
    time.sleep(0.5)

if result[0]:
    print("Microphone access GRANTED! JARVIS is ready.")
else:
    print("Microphone access DENIED.")
    print("Go to: System Settings > Privacy & Security > Microphone")
    print("and enable access for Python.")

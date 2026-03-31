#!/usr/bin/env python3
"""
Generate a JARVIS-style startup chime (sci-fi power-up sound).
Saves to ~/jarvis/entrance.wav
"""

import numpy as np
import wave
import struct
import os

SAMPLE_RATE = 44100
DURATION = 3.0  # seconds
OUTPUT = os.path.join(os.path.dirname(__file__), "entrance.wav")

def generate_chime():
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)

    # Rising sci-fi tone (like an arc reactor powering up)
    freq_start = 180
    freq_end = 880
    freq_sweep = np.linspace(freq_start, freq_end, len(t))
    sweep = 0.3 * np.sin(2 * np.pi * freq_sweep * t)

    # Harmonic shimmer
    shimmer = 0.15 * np.sin(2 * np.pi * freq_sweep * 2 * t)
    shimmer2 = 0.08 * np.sin(2 * np.pi * freq_sweep * 3 * t)

    # Sub bass thump at the start
    bass_env = np.exp(-t * 4)
    bass = 0.4 * bass_env * np.sin(2 * np.pi * 60 * t)

    # High sparkle ping at the end
    sparkle_t = t - 1.5
    sparkle_env = np.where(sparkle_t > 0, np.exp(-sparkle_t * 3), 0)
    sparkle = 0.2 * sparkle_env * np.sin(2 * np.pi * 1760 * t)

    # Combine
    signal = sweep + shimmer + shimmer2 + bass + sparkle

    # Envelope: fade in, sustain, fade out
    fade_in = np.minimum(t / 0.1, 1.0)
    fade_out = np.minimum((DURATION - t) / 0.5, 1.0)
    envelope = fade_in * fade_out
    signal = signal * envelope

    # Normalize to 16-bit
    signal = signal / np.max(np.abs(signal)) * 0.85
    samples = (signal * 32767).astype(np.int16)

    # Write WAV
    with wave.open(OUTPUT, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(samples.tobytes())

    print(f"  Chime saved to: {OUTPUT}")

if __name__ == "__main__":
    generate_chime()

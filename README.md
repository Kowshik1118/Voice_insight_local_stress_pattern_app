# Voice Insight

A single-file, attractive local desktop application for inspecting **vocal patterns** in WAV recordings. It is deliberately simple: it uses only Python standard-library modules and requires no API key, cloud service, server, database, Atlas account, or package installation.

## Run

1. Install Python 3.10 or newer with Tk support.
2. Open a terminal in this folder.
3. Run:

```bash
python main.py
```

4. Click **Select WAV** and choose an uncompressed PCM WAV file.

## What it measures

- Average active vocal energy in dBFS
- Variation in vocal energy between 200 ms segments
- Estimated quiet-time percentage
- A simple zero-crossing-based speech activity proxy
- A transparent 0–100 pattern score derived from those measurements

## Privacy and limits

All analysis runs locally in memory. The application does not upload, retain, or transmit your recording. It is not a medical device and cannot diagnose stress, anxiety, emotional state, deception, or any health condition. Background noise, microphone distance, illness, accent, and recording conditions can substantially affect measurements.

## Supported input

Use uncompressed PCM `.wav` files. The app supports 8-, 16-, 24-, and 32-bit sample widths and mono or stereo audio.

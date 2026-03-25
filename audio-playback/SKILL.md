---
name: audio-playback
description: Play audio files (MP3, WAV, OGG, FLAC, M4A) on Linux using available command-line tools such as aplay, ffplay, mpg123, or cvlc. Use this skill whenever the user wants to listen to, play back, or preview an audio file.
homepage: https://www.ffmpeg.org/ffplay.html
metadata: {"nanobot":{"emoji":"🔊","os":["linux"],"requires":{"bins":["ffplay"]},"install":[{"id":"apt","kind":"apt","package":"ffmpeg","bins":["ffplay"],"label":"Install ffmpeg (apt)"},{"id":"brew","kind":"brew","formula":"ffmpeg","bins":["ffplay"],"label":"Install ffmpeg (brew)"}]}}
---

# Audio Playback

Play audio files from the command line. Automatically selects the best available player.

## Supported Formats

MP3, WAV, OGG, FLAC, M4A, AAC, WMA, OPUS, and any format supported by the underlying tool.

## Tool Priority

Try tools in this order and use the first one found:

1. **ffplay** (part of ffmpeg) — universal, handles all formats
2. **mpg123** — lightweight, great for MP3
3. **aplay** — ALSA player, best for WAV/PCM
4. **cvlc** — VLC headless mode, very broad format support

## Usage

### Check available player

```bash
for cmd in ffplay mpg123 aplay cvlc; do command -v "$cmd" && break; done
```

### Play a file (silent/non-interactive)

```bash
# ffplay (suppress GUI and verbose output)
ffplay -nodisp -autoexit -loglevel quiet /path/to/file.mp3

# mpg123
mpg123 -q /path/to/file.mp3

# aplay (WAV/PCM files only)
aplay /path/to/file.wav

# cvlc (VLC headless)
cvlc --play-and-exit /path/to/file.mp3
```

### Play at a specific volume (0.0–1.0 scale)

```bash
# ffplay with volume
ffplay -nodisp -autoexit -volume 50 /path/to/file.mp3

# mpg123 with scale
mpg123 -q --scale 16384 /path/to/file.mp3
```

### Play only a portion of a file

```bash
# Start at 30 s, play for 10 s
ffplay -nodisp -autoexit -ss 30 -t 10 /path/to/file.mp3
```

## Notes

- Ensure the system audio device is not muted (`amixer sset Master unmute` on ALSA systems).
- On headless servers without a sound card, playback will fail silently; consider converting to a different format or streaming instead.
- For PicoClaw hardware boards (e.g., MaixCAM, LicheeRV Nano) that expose an audio device via ALSA, `aplay` is the most reliable choice for WAV files.

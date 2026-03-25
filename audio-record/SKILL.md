---
name: audio-record
description: Record audio from the default microphone or a specified input device to a file on Linux. Use this skill whenever the user wants to capture audio, record a voice memo, sample ambient sound, or record microphone input.
homepage: https://www.ffmpeg.org/ffmpeg-devices.html#alsa
metadata: {"nanobot":{"emoji":"🎙️","os":["linux"],"requires":{"bins":["ffmpeg"]},"install":[{"id":"apt","kind":"apt","package":"ffmpeg","bins":["ffmpeg","arecord"],"label":"Install ffmpeg (apt)"},{"id":"brew","kind":"brew","formula":"ffmpeg","bins":["ffmpeg"],"label":"Install ffmpeg (brew)"}]}}
---

# Audio Record

Capture audio from a microphone or any ALSA input device and save it to a file.

## Supported Output Formats

WAV, MP3, OGG, FLAC, M4A — any format supported by ffmpeg.

## Tool Priority

1. **ffmpeg** — preferred; handles all formats and devices
2. **arecord** — ALSA recorder, lightweight, outputs WAV/PCM only

## Quick Start

### Record for a fixed duration (10 seconds, WAV output)

```bash
ffmpeg -f alsa -i default -t 10 output.wav
```

### Record until the user stops (Ctrl-C)

```bash
ffmpeg -f alsa -i default output.wav
```

### Record directly to MP3 (requires libmp3lame in ffmpeg build)

```bash
ffmpeg -f alsa -i default -acodec libmp3lame -ab 192k output.mp3
```

### Record to FLAC (lossless)

```bash
ffmpeg -f alsa -i default output.flac
```

### Using arecord (WAV only)

```bash
# Record for 10 seconds at CD quality (44100 Hz, stereo, 16-bit)
arecord -d 10 -f cd output.wav

# Record until Ctrl-C
arecord -f cd output.wav
```

## Listing Available Input Devices

```bash
# ALSA devices
arecord -l

# PulseAudio sources
pactl list short sources
```

### Use a specific device with ffmpeg

```bash
# Replace hw:1,0 with the device shown by arecord -l
ffmpeg -f alsa -i hw:1,0 -t 10 output.wav
```

## Common Quality Settings

| Quality | Sample Rate | Channels | Flag |
|---------|------------|----------|------|
| Voice   | 16000 Hz   | Mono     | `-ar 16000 -ac 1` |
| CD      | 44100 Hz   | Stereo   | `-ar 44100 -ac 2` |
| Studio  | 48000 Hz   | Stereo   | `-ar 48000 -ac 2` |

```bash
# Voice quality (small file, good for speech recognition)
ffmpeg -f alsa -i default -ar 16000 -ac 1 voice.wav
```

## Notes

- Verify the microphone is not muted: `amixer sset Capture unmute`
- On PicoClaw hardware boards, check which ALSA card exposes the microphone with `arecord -l` before recording.
- Recorded files are saved to the current working directory unless a full path is given.

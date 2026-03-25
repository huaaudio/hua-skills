---
name: audio-convert
description: Convert audio files between formats (MP3, WAV, OGG, FLAC, M4A, AAC, OPUS) and adjust properties such as bit rate, sample rate, and channel count using ffmpeg. Use this skill whenever the user wants to change an audio file's format, compress it, or re-encode it.
homepage: https://ffmpeg.org/ffmpeg.html
metadata: {"nanobot":{"emoji":"🎵","os":["linux","darwin"],"requires":{"bins":["ffmpeg"]},"install":[{"id":"apt","kind":"apt","package":"ffmpeg","bins":["ffmpeg"],"label":"Install ffmpeg (apt)"},{"id":"brew","kind":"brew","formula":"ffmpeg","bins":["ffmpeg"],"label":"Install ffmpeg (brew)"}]}}
---

# Audio Convert

Convert audio files between formats and adjust encoding parameters with ffmpeg.

## Supported Formats

Input and output: MP3, WAV, OGG, FLAC, M4A (AAC), AAC, OPUS, WMA, AIFF, and all other formats supported by ffmpeg.

## Basic Conversion

### WAV → MP3

```bash
ffmpeg -i input.wav -acodec libmp3lame -ab 192k output.mp3
```

### MP3 → WAV

```bash
ffmpeg -i input.mp3 output.wav
```

### Any format → FLAC (lossless)

```bash
ffmpeg -i input.mp3 output.flac
```

### Any format → OGG Vorbis

```bash
ffmpeg -i input.mp3 -acodec libvorbis -q:a 5 output.ogg
```

### Any format → OPUS (high quality, low bitrate)

```bash
ffmpeg -i input.wav -acodec libopus -b:a 96k output.opus
```

### Any format → M4A (AAC)

```bash
ffmpeg -i input.mp3 -acodec aac -ab 192k output.m4a
```

## Adjust Audio Properties

### Change sample rate (e.g., to 16 kHz for speech recognition)

```bash
ffmpeg -i input.wav -ar 16000 output.wav
```

### Convert stereo to mono

```bash
ffmpeg -i input.wav -ac 1 output.wav
```

### Change bit rate

```bash
ffmpeg -i input.wav -ab 128k output.mp3
```

### Combine sample rate + channels + format in one command

```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav
```

## Batch Conversion

### Convert all MP3 files in a directory to WAV

```bash
for f in *.mp3; do ffmpeg -i "$f" "${f%.mp3}.wav"; done
```

## Check File Info Before Converting

```bash
ffprobe -v quiet -show_streams -select_streams a:0 input.mp3
```

## Common Codec Reference

| Format | Codec flag          | Notes                        |
|--------|---------------------|------------------------------|
| MP3    | `libmp3lame`        | Requires lame in ffmpeg build |
| AAC/M4A| `aac`              | Built-in encoder             |
| OGG    | `libvorbis`         | Open, patent-free            |
| OPUS   | `libopus`           | Best quality/size ratio      |
| FLAC   | `flac`              | Lossless, larger files       |
| WAV    | `pcm_s16le`         | Uncompressed PCM             |

## Notes

- ffmpeg overwrites output files by default; add `-n` to skip existing files or `-y` to always overwrite.
- To strip metadata from the output, add `-map_metadata -1`.
- On resource-constrained PicoClaw hardware, prefer lightweight formats (WAV, MP3) over computationally expensive ones (FLAC encoding is fast; OPUS encoding may be slow on very low-end boards).

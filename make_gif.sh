#!/usr/bin/env bash
#
# Turn a screen recording (.mov) into a small, crisp demo.gif for the README.
# No Homebrew needed — grabs a static ffmpeg via uv + imageio-ffmpeg.
#
# Usage:   ./make_gif.sh <recording.mov> [width] [fps]
#          ./make_gif.sh ~/Desktop/recording.mov 480 12
#
set -euo pipefail
IN="${1:?Usage: ./make_gif.sh <recording.mov> [width] [fps]}"
W="${2:-480}"      # output width in px (height auto)
FPS="${3:-12}"     # frames per second
cd "$(dirname "$0")"

echo "==> Locating ffmpeg (via uv, first run downloads it once)…"
FF="$(uv run --with imageio-ffmpeg python -c 'import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())')"

echo "==> Building color palette…"
"$FF" -y -i "$IN" -vf "fps=$FPS,scale=$W:-1:flags=lanczos,palettegen" /tmp/neko_palette.png

echo "==> Encoding demo.gif…"
"$FF" -y -i "$IN" -i /tmp/neko_palette.png \
    -filter_complex "fps=$FPS,scale=$W:-1:flags=lanczos[x];[x][1:v]paletteuse" \
    demo.gif

echo ""
echo "✓ Done → $(pwd)/demo.gif  ($(du -h demo.gif | cut -f1))"
echo "   Preview:  open demo.gif"

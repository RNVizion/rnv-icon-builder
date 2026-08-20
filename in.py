sudo apt-get update && sudo apt-get install -y --no-install-recommends \
  libegl1 libgl1 libglib2.0-0 libxkbcommon0 libdbus-1-3 libfontconfig1 \
  libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
  libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \
  libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0

python up.py --snapshots-only

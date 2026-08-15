sudo apt-get update && sudo apt-get install -y \
  libgl1 libegl1 libglib2.0-0 libfontconfig1 libdbus-1-3 \
  libxkbcommon0 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 \
  libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-shape0 libxcb-sync1 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1

export QT_QPA_PLATFORM=offscreen
python tests/test_snapshots.py

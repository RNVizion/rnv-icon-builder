sudo apt-get update && sudo apt-get install -y --no-install-recommends \
  libegl1 libgl1 libglib2.0-0 libxkbcommon0 \
  libdbus-1-3 libfontconfig1 libxcb-cursor0 \
  libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
  libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxcb-sync1 libxcb-xfixes0 libxcb-xinerama0 \
  libxcb-xkb1 libxkbcommon-x11-0 \
  xvfb x11-utils

pip install -r requirements.txt
pip install -r requirements-test.txt      # if you have NOT run up.py yet
# pip install -r tests/requirements-dev.txt   # if you HAVE run up.py

python up.py                              # if not already applied
xvfb-run -a python run_tests.py

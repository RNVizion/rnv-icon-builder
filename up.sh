pip install -r requirements.txt -r requirements-test.txt
export QT_QPA_PLATFORM=offscreen
python tests/test_snapshots.py

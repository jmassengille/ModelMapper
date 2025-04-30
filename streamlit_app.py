# streamlit_app.py

# Optional: early patches to avoid watcher noise
import sys
sys.modules.pop('torch._classes', None)

from app.app import main

# Kick off the Streamlit UI
main()

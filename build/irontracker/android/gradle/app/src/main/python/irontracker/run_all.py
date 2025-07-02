import subprocess
import threading
import webview
import time

def start_streamlit():
    subprocess.Popen(["streamlit", "run", "irontracker.py"])

# Start streamlit server
threading.Thread(target=start_streamlit, daemon=True).start()

# Wait for Streamlit to spin up
time.sleep(3)

# Launch in a WebView window
webview.create_window("IronTracker", "http://localhost:8501", width=480, height=800)
webview.start()

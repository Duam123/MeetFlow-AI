
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_FILE = PROJECT_ROOT / "streamlit_app.py"

def main():
    print("=" * 55)
    print("             MEETFLOW AI")
    print("       LOCAL AI AGENT SYSTEM")
    print("=" * 55)

    if not APP_FILE.exists():
        print("ERROR: streamlit_app.py not found!")
        return

    print("\n[1/2] Checking project files...")

    print("[2/2] Starting MeetFlow AI dashboard...")
    print("\nYour browser will open automatically.")
    print("Press CTRL+C to stop the application.\n")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_FILE),
    ]

    try:
        subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
    except KeyboardInterrupt:
        print("\nMeetFlow AI stopped.")

if __name__ == "__main__":
    main()

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_FILE = PROJECT_ROOT / "streamlit_app.py"

def main():
    print("=" * 55)
    print("             MEETFLOW AI")
    print("       LOCAL AI AGENT SYSTEM")
    print("=" * 55)

    if not APP_FILE.exists():
        print("ERROR: streamlit_app.py not found!")
        return

    print("\n[1/2] Checking project files...")

    print("[2/2] Starting MeetFlow AI dashboard...")
    print("\nYour browser will open automatically.")
    print("Press CTRL+C to stop the application.\n")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_FILE),
    ]

    try:
        subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
    except KeyboardInterrupt:
        print("\nMeetFlow AI stopped.")

if __name__ == "__main__":
    main()

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_FILE = PROJECT_ROOT / "streamlit_app.py"

def main():
    print("=" * 55)
    print("             MEETFLOW AI")
    print("       LOCAL AI AGENT SYSTEM")
    print("=" * 55)

    if not APP_FILE.exists():
        print("ERROR: streamlit_app.py not found!")
        return

    print("\n[1/2] Checking project files...")

    print("[2/2] Starting MeetFlow AI dashboard...")
    print("\nYour browser will open automatically.")
    print("Press CTRL+C to stop the application.\n")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_FILE),
    ]

    try:
        subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
    except KeyboardInterrupt:
        print("\nMeetFlow AI stopped.")

if __name__ == "__main__":
    main()

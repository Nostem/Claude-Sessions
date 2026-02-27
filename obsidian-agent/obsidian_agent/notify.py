import subprocess

def send_notification(title: str, subtitle: str, message: str):
    script = f'display notification "{message}" with title "{title}" subtitle "{subtitle}"'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
    except Exception:
        pass  # Best-effort; works on macOS only

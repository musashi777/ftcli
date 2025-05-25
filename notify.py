
"""
Wrapper minimal de termux-notification.
"""
import subprocess, shutil
TERMUX_NOTIFY = shutil.which("termux-notification")
def notifier(title: str, text: str, id: int = 999, **opts) -> None:
    if TERMUX_NOTIFY:
        args = [
            "termux-notification",
            "--id", str(id),
            "--title", title,
            "--content", text,
        ]
        for k, v in opts.items():
            args.extend([f"--{k.replace('_', '-')}", str(v)])
        subprocess.run(args, check=False)
    else:
        print(f"[NOTIFY] {title}: {text}")

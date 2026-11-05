"""Tiny native launcher for the local-first browser studio (Windows .exe target)."""
from __future__ import annotations

from threading import Thread
import tkinter as tk
import webbrowser

from projection_mapping.studio_server import start_server


def main() -> None:
    server, url = start_server()
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True)
    thread.start()

    root = tk.Tk()
    root.title("Projection Studio")
    root.geometry("380x205")
    root.configure(bg="#0b1016")
    root.resizable(False, False)
    tk.Label(
        root, text="PROJECTION  /  STUDIO", fg="#66e6e2", bg="#0b1016",
        font=("Segoe UI", 14, "bold"),
    ).pack(pady=(22, 9))
    tk.Label(
        root, text="Local-only WebGL studio. Your media is not uploaded.",
        fg="#b0bfce", bg="#0b1016", font=("Segoe UI", 9),
    ).pack(pady=(0, 14))
    tk.Button(
        root, text="OPEN STUDIO", command=lambda: webbrowser.open(url),
        bg="#66e6e2", fg="#071016", relief="flat", width=24,
    ).pack(pady=(0, 8))

    def close() -> None:
        server.shutdown()
        server.server_close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    root.after(300, lambda: webbrowser.open(url))
    try:
        root.mainloop()
    finally:
        if thread.is_alive():
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()

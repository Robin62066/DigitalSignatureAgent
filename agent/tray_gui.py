# agent/tray_gui.py
import threading
import pystray
from PIL import Image, ImageDraw
import os
import sys
import time
import signal
import warnings

# Suppress pystray warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from .main import app, PORT


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    # Construct the absolute path
    path = os.path.join(base_path, relative_path)

    # If file doesn't exist, try relative to current directory
    if not os.path.exists(path):
        # Try relative to the executable location
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        path = os.path.join(exe_dir, relative_path)

        # If still doesn't exist, try one level up (for development)
        if not os.path.exists(path):
            parent_dir = os.path.dirname(exe_dir)
            path = os.path.join(parent_dir, relative_path)

    return path


def create_fallback_image():
    """Create a simple fallback image when logo is not found"""
    # Create a simple 64x64 image with text
    img = Image.new("RGB", (64, 64), color="blue")
    d = ImageDraw.Draw(img)
    d.text((10, 25), "DS", fill="white")
    return img


def create_image():
    """Create tray icon image with proper path handling"""
    try:
        # Try multiple possible locations
        possible_paths = [
            get_resource_path("common/images/logo.png"),
            "common/images/logo.png",
            os.path.join(
                os.path.dirname(__file__), "..", "common", "images", "logo.png"
            ),
            os.path.join(os.path.dirname(sys.argv[0]), "common", "images", "logo.png"),
        ]

        print(f"[DEBUG] Looking for logo.png...")
        for img_path in possible_paths:
            if img_path and os.path.exists(img_path):
                print(f"[DEBUG] Loading image from: {img_path}")
                return Image.open(img_path)
            else:
                print(f"[DEBUG] Not found: {img_path}")

        # If no image found, create a simple fallback
        print("[DEBUG] Logo image not found in any location, creating fallback image")
        return create_fallback_image()

    except Exception as e:
        print(f"[DEBUG] Error loading tray icon: {e}")
        return create_fallback_image()


class StoppableFlaskThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._stop_event = threading.Event()

    def stop(self):
        """Stop the Flask thread"""
        self._stop_event.set()

    def run(self):
        """Run Flask app in a separate thread"""
        try:
            print(f"Starting Digital Signature Agent on http://127.0.0.1:{PORT}")
            # Use development server for simplicity
            from werkzeug.serving import make_server

            server = make_server("127.0.0.1", PORT, app)
            print("Flask server started successfully")

            # Serve until stopped
            while not self._stop_event.is_set():
                server.handle_request()

        except Exception as e:
            print(f"Flask error: {e}")


class TrayApp:
    def __init__(self):
        self.icon = None
        self.flask_thread = None
        self.shutting_down = False

    def setup_signal_handlers(self):
        """Setup proper signal handlers"""

        def signal_handler(sig, frame):
            if not self.shutting_down:
                self.shutting_down = True
                print(f"\nReceived signal {sig}, shutting down gracefully...")
                self.stop_app()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def stop_app(self):
        """Stop the application gracefully"""
        if self.shutting_down:
            return

        self.shutting_down = True
        print("Stopping Digital Signature Agent...")

        # Stop Flask thread
        if self.flask_thread and self.flask_thread.is_alive():
            print("Stopping Flask server...")
            self.flask_thread.stop()
            # Send a request to wake up the server
            try:
                import requests

                requests.get(f"http://127.0.0.1:{PORT}/", timeout=0.5)
            except:
                pass
            self.flask_thread.join(timeout=5)

        # Stop tray icon
        if self.icon:
            print("Stopping tray icon...")
            self.icon.stop()

        print("Shutdown complete.")
        os._exit(0)

    def on_quit(self, icon):
        """Handle quit from tray menu"""
        print("Quit requested from tray menu")
        self.stop_app()

    def run_flask(self):
        """Run Flask in a thread"""
        self.flask_thread = StoppableFlaskThread()
        self.flask_thread.start()
        return self.flask_thread

    def run_tray(self):
        """Run the tray icon"""
        # Create tray icon
        self.icon = pystray.Icon(
            "digital_signature_agent",
            create_image(),
            title=f"Digital Signature Agent\nhttp://127.0.0.1:{PORT}",
            menu=pystray.Menu(
                pystray.MenuItem("Show Info", self.show_info),
                pystray.MenuItem("Quit", self.on_quit),
            ),
        )

        print("Tray icon started. Use 'Quit' from tray menu to exit.")
        print("You can also close the console window to exit.")

        try:
            self.icon.run()
        except Exception as e:
            print(f"Tray error: {e}")
            self.stop_app()

    def show_info(self, icon=None, item=None):
        """Show application info"""
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showinfo(
            "Digital Signature Agent",
            f"Digital Signature Agent is running!\n\n"
            f"Access at: http://127.0.0.1:{PORT}\n\n"
            f"To stop: Use 'Quit' from tray menu.",
        )
        root.destroy()

    def start(self):
        """Start the application"""
        self.setup_signal_handlers()

        # Start Flask
        self.run_flask()

        # Wait a moment for Flask to start
        time.sleep(2)

        # Start tray
        self.run_tray()


def start_agent():
    """Start the agent"""
    app = TrayApp()
    app.start()


if __name__ == "__main__":
    start_agent()

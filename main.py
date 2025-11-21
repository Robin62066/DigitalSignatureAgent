# main.py (in root directory)
import sys
import os
import traceback
import sys
import traceback
import linecache

# Global exception handler to catch the None format error
original_excepthook = sys.excepthook


def detailed_excepthook(exc_type, exc_value, exc_traceback):
    if "NoneType" in str(exc_type) and "__format__" in str(exc_value):
        print("\n" + "!" * 80)
        print("NONE TYPE FORMAT ERROR DETECTED!")
        print("!" * 80)

        # Print detailed traceback with line numbers
        tb = exc_traceback
        frame_count = 0

        while tb and frame_count < 10:  # Limit to first 10 frames
            frame = tb.tb_frame
            lineno = tb.tb_lineno
            filename = frame.f_code.co_filename
            function = frame.f_code.co_name

            print(f"\nFrame {frame_count}: {filename}, line {lineno}, in {function}")

            # Try to get the code line
            try:
                line = linecache.getline(filename, lineno).strip()
                print(f"   Code: {line}")
            except:
                pass

            # Check for None values in local variables
            none_vars = [
                name for name, value in frame.f_locals.items() if value is None
            ]
            if none_vars:
                print(f"   None variables: {none_vars}")

            tb = tb.tb_next
            frame_count += 1

        print("\n" + "!" * 80)

    # Call original excepthook
    original_excepthook(exc_type, exc_value, exc_traceback)


sys.excepthook = detailed_excepthook
# Add the agent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent"))


def main():
    """Main entry point for the application"""
    try:
        from agent.tray_gui import start_agent

        print("Starting Digital Signature Agent...")
        start_agent()

    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed.")
        if sys.stdout and sys.stdout.isatty():
            input("Press Enter to exit...")
    except Exception as e:
        print(f"Failed to start application: {e}")
        traceback.print_exc()
        if sys.stdout and sys.stdout.isatty():
            input("Press Enter to exit...")


if __name__ == "__main__":
    main()

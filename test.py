import tkinter as tk
from tkinter import simpledialog, messagebox
import serial
import json
import threading
import time
import os
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities

# Serial port configuration
SERIAL_PORT = "COM3"  # Replace with your actual COM port
BAUD_RATE = 9600

# File to save app list and volumes
APP_LIST_FILE = "app_list.txt"

# App data
apps = {}  # Dictionary to store app mappings: {"app0": "spotify.exe", ...}
app_volumes = {}  # Dictionary to track app volumes


def load_app_list():
    """Load the app list and volumes from a file."""
    global apps, app_volumes
    if os.path.exists(APP_LIST_FILE):
        with open(APP_LIST_FILE, "r") as f:
            data = json.load(f)
            apps = data.get("apps", {})
            app_volumes = data.get("volumes", {})
        print(f"Loaded app list and volumes: {apps}, {app_volumes}")
    else:
        print("No saved app list found. Starting fresh.")


def save_app_list():
    """Save the current app list and volumes to a file."""
    try:
        data = {"apps": apps, "volumes": app_volumes}
        with open(APP_LIST_FILE, "w") as f:
            json.dump(data, f)
        print(f"Saved app list and volumes: {apps}, {app_volumes}")
    except Exception as e:
        print(f"Error saving app list: {e}")


def send_app_list(serial_port):
    """Send the updated app list to the Pi."""
    try:
        app_list_json = json.dumps({f"app{i}": name for i, name in enumerate(apps.values())})
        serial_port.write((app_list_json + "\n").encode())
        print(f"Sent app list to Pi: {app_list_json}")
    except Exception as e:
        print(f"Error sending app list: {e}")


def set_app_volume(app_name, volume):
    """Set volume for a specific app."""
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name().lower() == app_name.lower():
                volume_control = session.SimpleAudioVolume
                volume_control.SetMasterVolume(volume / 100.0, None)
                app_volumes[app_name] = volume  # Update the volume record
                save_app_list()  # Save volumes to file
                print(f"Set volume for {app_name} to {volume}%")
                return
        print(f"App {app_name} not found.")
    except Exception as e:
        print(f"Error setting volume for {app_name}: {e}")


def serial_thread():
    """Thread to handle serial communication."""
    global app_volumes
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            print("Serial connection established.")
            send_app_list(ser)  # Send initial app list

            while True:
                if ser.in_waiting > 0:
                    raw_data = ser.readline().decode().strip()
                    try:
                        # Parse JSON data from Pi
                        data = json.loads(raw_data)
                        print(f"Received data from Pi: {data}")
                        for app_name, volume in data.items():
                            if app_name in apps.values():
                                set_app_volume(app_name, volume)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
                time.sleep(0.1)  # Avoid busy looping
    except serial.SerialException as e:
        print(f"Serial port error: {e}")
    except Exception as e:
        print(f"Error in serial thread: {e}")


def update_app_list():
    """Send updated app list to the Pi and save it."""
    save_app_list()
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            send_app_list(ser)
            messagebox.showinfo("Success", "App list updated and sent to Pi!")
    except serial.SerialException as e:
        messagebox.showerror("Error", f"Serial port error: {e}")


def add_app():
    """Add a new app to the control list."""
    app_name = simpledialog.askstring("Add App", "Enter the executable name of the app (e.g., spotify.exe):")
    if app_name:
        app_key = f"app{len(apps)}"
        apps[app_key] = app_name
        app_volumes[app_name] = 0  # Initialize volume to 0
        update_ui()
        save_app_list()


def remove_app(app_key):
    """Remove an app from the control list."""
    if app_key in apps:
        del app_volumes[apps[app_key]]
        del apps[app_key]
        update_ui()
        save_app_list()


def update_ui():
    """Refresh the UI to reflect the current app list."""
    for widget in app_frame.winfo_children():
        widget.destroy()

    for app_key, app_name in apps.items():
        frame = tk.Frame(app_frame)
        frame.pack(fill=tk.X, pady=5)

        tk.Label(frame, text=f"{app_name} (Last Volume: {app_volumes.get(app_name, 0)}%)", anchor="w").pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        tk.Button(frame, text="Remove", command=lambda k=app_key: remove_app(k)).pack(side=tk.RIGHT)


def start_serial_thread():
    """Start the serial communication thread."""
    thread = threading.Thread(target=serial_thread, daemon=True)
    thread.start()


# Initialize GUI
root = tk.Tk()
root.title("App Volume Controller")

# App control section
control_frame = tk.Frame(root)
control_frame.pack(fill=tk.X, padx=10, pady=10)

tk.Button(control_frame, text="Add App", command=add_app).pack(side=tk.LEFT, padx=5)
tk.Button(control_frame, text="Update App List", command=update_app_list).pack(side=tk.RIGHT, padx=5)

# App list section
app_frame = tk.Frame(root)
app_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Load app list from file
load_app_list()

# Update UI with current apps and volumes
update_ui()

# Start serial communication thread
start_serial_thread()

root.mainloop()

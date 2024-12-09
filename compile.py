import serial
import tkinter as tk
from tkinter import scrolledtext
import os
import threading

# Global variables
ser = None
app_volumes = {}
SAVE_FILE = "app_volumes.txt"
potentiometer_value = 0  # Store the potentiometer value received from the Mega

# Initialize Tkinter window
root = tk.Tk()
root.title("App Volume Control")

# Function to handle serial communication with the Mega
def connect_serial():
    global ser
    try:
        ser = serial.Serial('COM4', 9600, timeout=1)  # Adjust COM port if necessary
        log_serial_output("Connected to COM4 successfully.")
    except serial.SerialException as e:
        log_serial_output(f"Error opening serial port: {e}")

# Function to handle sending data to the Mega
def send_data_to_mega(data):
    try:
        if ser and ser.is_open:
            ser.write(data.encode())  # Send data as bytes to the Mega
            log_serial_output(f"Sent data: {data}")
        else:
            log_serial_output("Serial connection not open.")
    except Exception as e:
        log_serial_output(f"Error sending data: {e}")

# Function to log serial output into the text area
def log_serial_output(message):
    serial_output_text.insert(tk.END, message + '\n')  # Append message to the text box
    serial_output_text.yview(tk.END)  # Auto-scroll to the latest message

# Function to handle the button click and send app data
def send_app_data():
    app_data = ""
    for app, volume in app_volumes.items():
        app_data += f"{app}|{volume}\n"  # Format: app_name|volume
    send_data_to_mega(app_data)

# Function to update the app volume from the UI
def update_app_volume(app_name, volume):
    app_volumes[app_name] = volume
    log_serial_output(f"Updated {app_name} volume to {volume}%")
    save_app_data()  # Save updated app data

# Function to handle the UI action for changing app volume
def change_volume(app_name, volume):
    update_app_volume(app_name, volume)
    send_app_data()

# Function to handle adding new apps
def add_app():
    app_name = app_name_entry.get()
    if app_name and app_name not in app_volumes:
        app_volumes[app_name] = 50  # Default volume set to 50%
        update_app_list_ui()
        log_serial_output(f"Added new app: {app_name}")
        save_app_data()  # Save updated app data

# Function to update the app list UI
def update_app_list_ui():
    app_list_box.delete(0, tk.END)
    for app_name in app_volumes:
        app_list_box.insert(tk.END, app_name)

# Function to handle volume slider update
def on_slider_change(value):
    volume = int(value)
    selected_app = app_list_box.get(tk.ACTIVE)
    if selected_app:
        change_volume(selected_app, volume)

# Function to save app list and volumes to a file
def save_app_data():
    with open(SAVE_FILE, 'w') as f:
        for app_name, volume in app_volumes.items():
            f.write(f"{app_name}|{volume}\n")

# Function to load app list and volumes from the file
def load_app_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            for line in f:
                app_name, volume = line.strip().split('|')
                app_volumes[app_name] = int(volume)
        update_app_list_ui()

# Function to receive data from the Mega
def receive_data_from_mega():
    global potentiometer_value
    while True:
        if ser and ser.is_open:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()
                log_serial_output(f"Received from Mega: {data}")
                try:
                    # Assuming Mega sends potentiometer value like 'POT:123'
                    if data.startswith("POT:"):
                        potentiometer_value = int(data.split(":")[1])
                        update_slider_based_on_potentiometer(potentiometer_value)
                except ValueError:
                    log_serial_output("Error parsing potentiometer data.")

# Function to update the slider based on potentiometer value
def update_slider_based_on_potentiometer(value):
    volume_slider.set(value)
    selected_app = app_list_box.get(tk.ACTIVE)
    if selected_app:
        change_volume(selected_app, value)

# Create a text area for serial output
serial_output_text = scrolledtext.ScrolledText(root, width=70, height=10)
serial_output_text.pack(padx=10, pady=10)

# Create UI elements for app management
app_name_entry = tk.Entry(root)
app_name_entry.pack(padx=10, pady=10)
add_app_button = tk.Button(root, text="Add App", command=add_app)
add_app_button.pack(padx=10, pady=10)

# Create a listbox for showing apps
app_list_box = tk.Listbox(root, selectmode=tk.SINGLE, width=50, height=10)
app_list_box.pack(padx=10, pady=10)

# Volume slider
volume_slider = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, label="Volume")
volume_slider.pack(padx=10, pady=10)
volume_slider.bind("<Motion>", lambda event: on_slider_change(volume_slider.get()))

# Create a button to send app data (for testing)
send_button = tk.Button(root, text="Send App Data", command=send_app_data)
send_button.pack(padx=10, pady=10)

# Connect to the serial port when starting the app
connect_serial()

# Load the saved app data (if any) when the app starts
load_app_data()

# Start the serial reading thread
serial_thread = threading.Thread(target=receive_data_from_mega, daemon=True)
serial_thread.start()

# Start the Tkinter event loop to run the UI
root.mainloop()

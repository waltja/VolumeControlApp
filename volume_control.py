import psutil
import serial
from pycaw.pycaw import AudioUtilities

# Target applications and initial volumes
target_apps = {
    "spotify.exe": 20,  # Replace with the exact executable names of your apps
    "discord.exe": 100,
    "opera.exe": 10,
    "Windows10Universal.exe": 30
}

# Initialize serial communication
com_port = "COM3"  # Change to match your COM port
baud_rate = 9600


# Function to get process name by PID
def get_process_name(pid):
    try:
        process = psutil.Process(pid)
        return process.name()
    except psutil.NoSuchProcess:
        return None


# Function to set volume for a specific application
def set_application_volume(app_name, volume_level):
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        process_name = get_process_name(session.ProcessId)
        if process_name and process_name.lower() == app_name.lower():
            try:
                session.SimpleAudioVolume.SetMasterVolume(volume_level / 100.0, None)
                print(f"Set volume for {app_name} to {volume_level}%")
            except Exception as e:
                print(f"Error adjusting volume for {app_name}: {e}")


# Main program to read and process serial data
try:
    with serial.Serial(com_port, baud_rate, timeout=1) as ser:
        print(f"Listening on {com_port} at {baud_rate} baud...")
        while True:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
            print(f"Received: {line}")
            try:
                app_name, volume = line.split(":")
                volume = int(volume)
                if app_name in target_apps:
                    set_application_volume(app_name, volume)
                else:
                    print(f"Unknown application: {app_name}")
            except ValueError:
                print(f"Invalid data format: {line}")
except serial.SerialException as e:
    print(f"Serial error: {e}")

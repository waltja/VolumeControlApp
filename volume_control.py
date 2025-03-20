import time
from pycaw.pycaw import ISimpleAudioVolume
from pycaw.pycaw import AudioUtilities


class VolumeController:
    def __init__(self):
        self.sessions = None
        self.initialize_sessions()

    def initialize_sessions(self):
        """Initialize audio sessions."""
        self.sessions = AudioUtilities.GetAllSessions()

    def refresh_sessions(self):
        """Refresh the session manager to detect new apps."""
        self.initialize_sessions()

    def set_volume(self, app_name, volume):
        """Set the volume for a specific app."""
        for session in self.sessions:
            if session.Process and session.Process.name() == app_name:
                try:
                    # Query the ISimpleAudioVolume interface
                    volume_interface = session._ctl.QueryInterface(ISimpleAudioVolume)
                    volume_interface.SetMasterVolume(volume / 100.0, None)
                    print(f"Set volume for {app_name} to {volume}%")
                    return True
                except Exception as e:
                    print(f"Error setting volume for {app_name}: {e}")
        print(f"App {app_name} not found.")
        return False

    def get_volume(self, app_name):
        """Get the volume for a specific app."""
        for session in self.sessions:
            if session.Process and session.Process.name() == app_name:
                try:
                    # Query the ISimpleAudioVolume interface
                    volume_interface = session._ctl.QueryInterface(ISimpleAudioVolume)
                    return volume_interface.GetMasterVolumeLevel()
                except Exception as e:
                    print(f"Error setting volume for {app_name}: {e}")
        print(f"App {app_name} not found.")
        return False

    def update_volumes(self, app_names, app_volumes):
        """Update volumes for a list of apps."""
        for app_name, volume in zip(app_names, app_volumes):
            if not self.set_volume(app_name, volume):
                print(f"Failed to update volume for {app_name}. Refreshing sessions.")
                self.refresh_sessions()

    # Main loop to process volume updates
    def volume_control_loop(self, serial_handler, app_names, app_volumes, callback=None):
        """Continuously listens for data from serial_comm and updates app volumes."""
        callback("Volume controller initialized.")
        for i, app in enumerate(app_names):
            app_volumes[i] = self.get_volume(app)
        while True:
            # Check for incoming serial data
            current_app = serial_handler.current_app
            self.set_volume(app_names[current_app], int(serial_handler.values[0]))
            time.sleep(0.1)  # Small delay to prevent busy-waiting

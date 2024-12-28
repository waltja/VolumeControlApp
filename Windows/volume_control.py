import time

from pycaw.api.endpointvolume import IAudioEndpointVolume
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
                    volume_interface = session._ctl.QueryInterface(IAudioEndpointVolume)
                    volume_interface.SetMasterVolumeLevelScalar(volume / 100.0, None)
                    print(f"Set volume for {app_name} to {volume}%")
                    return True
                except Exception as e:
                    print(f"Error setting volume for {app_name}: {e}")
        print(f"App {app_name} not found.")
        return False

    def update_volumes(self, app_volumes, app_names):
        """Update volumes for a list of apps."""
        for app_name, volume in zip(app_names, app_volumes):
            if not self.set_volume(app_name, volume):
                print(f"Failed to update volume for {app_name}. Refreshing sessions.")
                self.refresh_sessions()

    # Main loop to process volume updates
    def volume_control_loop(self, serial_handler, app_names, callback=None):
        """Continuously listens for data from serial_comm and updates app volumes."""
        print("Volume controller initialized.")
        app_volumes = []
        while True:
            # Check for incoming serial data
            if app_volumes != serial_handler.volumes:
                try:
                    app_volumes = serial_handler.volumes
                    if isinstance(app_volumes, list) and len(app_volumes) == len(app_names):
                        if callback:
                            callback(f"Received volume data: {app_volumes}")
                        self.update_volumes(app_volumes, app_names)
                    else:
                        if callback:
                            callback(f"Invalid data format received: {serial_handler.volumes}")
                except Exception as e:
                    if callback:
                        callback(f"Error processing serial data: {e}")

            time.sleep(0.1)  # Small delay to prevent busy-waiting


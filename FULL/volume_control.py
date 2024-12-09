import psutil
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


def _initialize_audio_session_manager():
    devices = AudioUtilities.GetAllSessions()
    return {s.Process.name().lower(): s for s in devices if s.Process}


class VolumeController:
    def __init__(self):
        self.session_manager = _initialize_audio_session_manager()

    def update_volumes(self, app_volumes):
        """Updates volumes of all tracked apps based on the provided dictionary."""
        for app_name, volume in app_volumes.items():
            self.set_volume(app_name, volume)

    def set_volume(self, app_name, volume):
        """Sets the volume for a specific application."""
        session = self.session_manager.get(app_name.lower())
        if not session:
            print(f"Error: Application {app_name} not found.")
            return

        try:
            interface = session.SimpleAudioVolume
            interface.SetMasterVolume(volume / 100, None)
            print(f"Set volume for {app_name} to {volume}%")
        except Exception as e:
            print(f"Error setting volume for {app_name}: {e}")

"""
Module that starts the application
"""

from src.gui.app import App
import threading
from src.app.auxiliary_functions import find_files
import time
import os


def background_task(app):
    """
    Background task to periodically check for the availability of the Spotify access token.

    Parameters:
    - app: An instance of the application class containing Spotify authentication and playlist update methods.
    """
    access_token_file, _ = find_files()

    while True:
        time.sleep(2)
        print("Checking for spotify access token")
        if os.path.getsize(access_token_file) > 0:
            print("Spotify access token found. Getting playlists...")
            app.spotifyLogin.is_token_available()
            app.spotifyApi.access_token = app.spotifyLogin.access_token
            app.update_playlists()  # Call the method in your App class to update playlists
            break  # Exit the loop once the token is found and playlists are updated


if __name__ == "__main__":
    # Creates app instance and runs it
    app_instance = App()
    app_instance.run()

    # Start a background thread to periodically check for Spotify access token
    access_token_thread = threading.Thread(target=background_task, daemon=True, args=(app_instance,))
    access_token_thread.start()

    # Start the main loop of the App
    app_instance.mainloop()
    




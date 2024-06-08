"""
Flask Application for SenyaFy Music Converter

This module defines the MyFlask class, a Flask application responsible for handling the Spotify authentication callback
and shutting down the Flask server. It includes routes for the Spotify callback and server shutdown.

Classes:
    - MyFlask: Flask application class for handling Spotify authentication callback and server shutdown.

Adjustments and modifications may be needed based on specific implementations and requirements.
"""

import os
import logging

from flask import Flask, request

from src.app.auxiliary_functions import find_files
from src.assets import config


class MyFlask:
    """
    Initializes the MyFlask class.

    Parameters:
    - spotify_login: An instance of the SpotifyLogin class for handling Spotify authentication.
    """

    def __init__(self, spotify_login):
        log = logging.getLogger('werkzeug')
        log.disabled = True
        self.app = Flask(__name__)
        self.spotify_login = spotify_login
        self.app.route('/callback')(self.callback)
        self.app.route('/shutdown', methods=['POST'])(self.shutdown)

    def callback(self):
        """
        Handles the Spotify callback.

        Retrieves the authorization code from the callback URL,
        exchanges it for an access token, and stores the access
        and refresh tokens in files.

        Returns:
        - A message indicating the success of obtaining the access token.
        """
        authorization_code = request.args.get('code')
        # Could be used to secure connections
        # state = request.args.get('state')
        code_verifier = os.environ.get('code_verifier')

        # Exchange the authorization code for an access token
        token_response = self.spotify_login.exchange_code_for_token(authorization_code, code_verifier)

        # Store the access token
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        access_token_path, refresh_token_path = find_files()
        with open(access_token_path, 'a', encoding='utf-8') as f:
            f.write(access_token)
        # print(f"\nSpotify access token writen to {access_token_path}")
        with open(refresh_token_path, 'a', encoding='utf-8') as rf:
            rf.write(refresh_token)
        # print("Refresh token writen")

        return 'Access token obtained successfully. You can now make API requests.'

    def shutdown(self):
        """
        Shuts down the Flask server.

        Sets a flag to indicate the server should be shut down and
        triggers the server shutdown.

        Returns:
        - A message indicating that the server is shutting down.
        """
        print('Shutting down the server...')
        os.environ['SHUTDOWN_SERVER'] = 'true'  # Set a flag to indicate the server should be shut down
        request.environ.get('werkzeug.server.shutdown')()
        return 'Server shutting down...'

    def run(self):
        """
        Runs the Flask application.

        Starts the Flask development server with the specified port.
        """
        self.app.run(port=config.port)

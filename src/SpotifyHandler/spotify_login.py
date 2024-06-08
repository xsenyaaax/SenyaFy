"""
Spotify Login Module

This module handles Spotify authentication, including exchanging authorization code for tokens,
generating the authorization URL, and checking token availability.

"""
import base64
import os
from urllib.parse import urlencode

import requests

from src.assets import config
from src.app import auxiliary_functions


class SpotifyLogin:
    """
    Class that handles Spotify Login and getting token
    """
    def __init__(self):
        """
        Initializes the SpotifyLogin class.

        Attributes:
        - access_token (str or None): The Spotify access token obtained during authentication.
        - refresh_token (str or None): The Spotify refresh token obtained during authentication.
        """
        self.access_token = None
        self.refresh_token = None

    @staticmethod
    def exchange_code_for_token(authorization_code, code_verifier):
        """
        Exchanges an authorization code for Spotify access and refresh tokens.

        Parameters:
        - authorization_code (str): The authorization code obtained during the authentication process.
        - code_verifier (str): The code verifier used in the authentication process.

        Returns:
        - dict: The JSON response containing access and refresh tokens.
        """
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(f'{config.spotify_client_id}:{config.spotify_client_secret}'.encode()).decode(),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': config.spotify_redirect_uri,
            'code_verifier': code_verifier
        }

        response = requests.post(config.spotify_token_url, headers=headers, data=data, timeout=30)
        return response.json()

    @staticmethod
    def get_authorization_url():
        """
        Generates the Spotify authorization URL for user authentication.

        Returns:
        - str: The generated Spotify authorization URL.
        """
        code_verifier = auxiliary_functions.generate_random_string(128)
        code_challenge = auxiliary_functions.generate_code_challenge(code_verifier)

        os.environ['code_verifier'] = code_verifier

        authorization_url = config.spotify_auth_url
        query_params = {
            'response_type': 'code',
            'client_id': config.spotify_client_id,
            'scope': config.scope,
            'redirect_uri': config.spotify_redirect_uri,
            'code_challenge_method': 'S256',
            'code_challenge': code_challenge
        }
        authorization_url += '?' + urlencode(query_params)
        return authorization_url

    def is_token_available(self):
        """
         Checks if the Spotify access token is available by examining the token file.

         Returns:
         - bool: True if the access token is available, False otherwise.
         """
        access_token_path, _ = auxiliary_functions.find_files()
        if os.path.getsize(access_token_path) == 0:
            return False

        with open(access_token_path, 'r', encoding='utf-8') as file:
            access = file.readline()
        # Could be done in the future be enabling refreshing token
        # with open(refresh_token_path, 'r') as file:
        #    refresh = file.readline()
        self.access_token = access
        # self.refresh_token = refresh
        return True

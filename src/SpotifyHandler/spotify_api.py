"""
Spotify api module

Defines the SpotifyApi class, which is responsible for interacting with the Spotify API to
retrieve the user's playlists and songs.

"""

import requests
import src.assets.config as config_variables
from src.app.auxiliary_functions import send_request, error_in_json


class SpotifyApi:
    """
    Class that handles spotify api responses and get playlists/songs of current user
    """
    def __init__(self):
        self.access_token = None
        self.spotify_current_playlist = None
        self.spotify_playlists = {}
        self.spotify_playlist_songs = {}
        self.spotify_chosen_songs = []


    def get_auth_header(self):
        """
        Generates an authorization header with the access token.

        Returns:
        - dict: The authorization header with the access token.
        """
        return {"Authorization": "Bearer " + self.access_token}

    def make_test_request(self):
        """
        Makes a test request to the Spotify API to verify the access token.

        Returns:
        - dict or None: The JSON response from the test request if successful, otherwise None.
        """
        url = config_variables.spotify_user_info_url
        if self.access_token is None:
            return None

        headers = self.get_auth_header()
        response = send_request(url=url, headers=headers)
        if not error_in_json(response):
            return response.json()

        return None

    def get_playlist(self, playlist_id):
        """
        Retrieves information about a Spotify playlist.

        Parameters:
        - playlist_id (str): The ID of the Spotify playlist.

        Returns:
        - dict or None: The JSON response containing playlist information if successful, otherwise None.
        """
        url = f'{config_variables.spotify_playlist_info_url}{playlist_id}'
        headers = self.get_auth_header()
        if headers is None:
            return None
        response = send_request(url=url, headers=headers)
        if not error_in_json(response):
            return response.json()

        return None

    def get_user_playlists(self):
        """
        Retrieves the user's Spotify playlists.

        Returns:
        - dict or None: The JSON response containing user playlists if successful, otherwise None.
        """
        url = config_variables.spotify_user_playlists_info_url
        headers = self.get_auth_header()
        if headers is None:
            return None
        query = {
            "limit": 50
        }
        response = send_request(url=url, headers=headers, params=query)
        if not error_in_json(response):
            return response.json()

        return None

    def get_all_playlists(self):
        """
        Retrieves all of the user's Spotify playlists.

        This function iteratively fetches playlist information using paginated responses.

        This function updates the class attribute 'self.spotify_playlists' with the complete playlist information.
        """
        playlists_info = {}
        response = self.get_user_playlists()
        while response:
            playlists_prev, playlists_next, playlists = self.get_playlists_info(response)
            playlists_info.update(playlists)

            if playlists_next:
                response = send_request(playlists_next, self.get_auth_header())
                if response is None:
                    break
                response = response.json()
            else:
                response = None

        self.spotify_playlists = playlists_info

    @staticmethod
    def get_playlists_info(response):
        """
        Extracts information about playlists from a Spotify API response.

        Parameters:
        - response (dict): The JSON response from a Spotify API call.

        Returns:
        - list: A list containing previous URL, next URL, and a dictionary with playlist information.
        """
        playlists_next = response['next']
        playlists_prev = response['previous']
        playlists = response['items']
        playlists_info = {}

        for playlist in playlists:
            name = playlist.get("name")
            images = playlist.get("images")
            tracks_api = playlist.get("tracks")
            # playlists_info.append({"name": name, "images": images, "tracks_api": tracks_api})
            playlists_info[name] = ({"images": images, "tracks_api": tracks_api})
        return [playlists_prev, playlists_next, playlists_info]

    def get_playlist_items(self, playlist_url):
        """
        Retrieves the items (tracks) from a Spotify playlist.

        Parameters:
        - playlist_url (str): The URL of the Spotify playlist.

        Returns:
        - list: A list containing the tracks from the playlist.
        """
        headers = self.get_auth_header()
        url = playlist_url

        tracks = []
        while url:
            response = requests.get(url, headers=headers, timeout=30)
            response_json = response.json()
            if 'error' in response_json:
                return response_json
            response_next = response_json['next']
            if 'items' in response_json:
                items = response_json['items']
                current = self.get_tracks(items)
                tracks.extend(current)
            if response_next is not None:
                url = response_json.get('next')
            else:
                break

        return tracks

    @staticmethod
    def get_tracks(response):
        """
        Extracts track information from a Spotify API response.

        Parameters:
        - response (list): The list of items containing track information.

        Returns:
        - list: A list containing formatted track names.
        """
        if response and "error" in response:
            return 401
        if response:
            tracks = []
            i = 1
            for item in response:
                track = item.get("track")
                if track is None:
                    continue
                artists = track.get('artists')
                i += 1
                artists_tuple = tuple(artist.get("name") for artist in artists)
                name = track.get('name')
                song = ','.join(artists_tuple) + f' - {name}'
                tracks.append(song)

            return tracks

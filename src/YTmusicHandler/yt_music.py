"""
YT Music api module

Defines the YTMusicHandler class, which is responsible for interacting with the YouTube Music API to
retrieve,update the user's playlists. Allow exporting music to those playlists.

"""

from ytmusicapi import YTMusic


class YTMusicHandler:
    """
    Class that handler yt music api connection and retrieves data
    """
    def __init__(self, auth):
        """
        Initializes the YTMusicHandler class.

        Sets up the YTMusic object by loading the authentication
        information from the 'oauth.json' file in the same directory
        as this script.
        """
        self.yt_music = YTMusic(auth)
        self.user_playlists_id = {}

    def test_request(self):
        """
        Performs a test request to create a playlist on YouTube Music.

        For testing purposes, it creates a playlist named "test playlist"
        with a "test description" and retrieves the playlist ID.
        """
        if self.yt_music is None:
            return False
        playlist_id = self.yt_music.create_playlist("test playlist", "test description")
        return isinstance(playlist_id, str)

    def create_playlist(self, title, description):
        """
        Creates a playlist on YouTube Music.

        Parameters:
        - title: Title of the playlist.
        - description: Description of the playlist.

        Returns:
        - The response from the YouTube Music API after creating the playlist.
        """
        response = self.yt_music.create_playlist(title, description)
        return response

    def create_playlist_push_songs(self, title, description, songs):
        """
        Creates a playlist on YouTube Music and adds specified songs.

        Parameters:
        - title: Title of the playlist.
        - description: Description of the playlist.
        - songs: List of song titles to add to the playlist.

        Returns:
        - A list of songs for which the addition to the playlist failed.
        """
        print(f"Total songs to export: {len(songs)}")
        if title not in self.user_playlists_id:
            playlist_id = self.yt_music.create_playlist(title, description)
            self.user_playlists_id[title] = playlist_id
        else:
            playlist_id = self.user_playlists_id[title]

        errors_list = []
        for i, song in enumerate(songs):
            try:
                print(f'{i}: exporting {song}')
                response = self.yt_music.search(song, filter='songs')
                firstItem = response[0]['videoId']
                status = self.yt_music.add_playlist_items(playlistId=playlist_id, videoIds=[firstItem])
                if 'STATUS_SUCCEEDED' not in status['status']:
                    errors_list.append(song)
            except Exception as e:
                errors_list.append(song)
                print(f'Error: {e}')
        return errors_list

    def get_current_playlists(self):
        """
        Retrieves and updates the user's current playlists from YouTube Music.

        This function is typically called to refresh the list of the user's playlists in the application.
        It updates the user_playlists_id dictionary with the latest information from YouTube Music.
        """
        response = self.yt_music.get_library_playlists()
        for item in response:
            if item['title'] == 'Liked Music' or item['title'] == 'Episodes for Later':
                continue

            playlist_name = item['title']
            playlist_id = item['playlistId']
            self.user_playlists_id[playlist_name] = playlist_id

    def get_playlist_id(self, title):
        """
        Get the playlist ID associated with the given title.

        Parameters:
        - title: The title of the playlist.

        Returns:
        - The playlist ID if the playlist is found, otherwise None.
        """
        if title in self.user_playlists_id:
            return self.user_playlists_id[title]

        items = self.yt_music.get_library_playlists()

        for item in items:
            self.user_playlists_id[title] = item['playlistId']
            if item['title'] == title:
                return item['playlistId']
        return None

    def push_to_existing_playlist(self, playlist_title, songs):
        """
        Add songs to an existing playlist on YouTube Music.

        Parameters:
        - playlist_title: The title of the existing playlist.
        - songs: List of song titles to add to the playlist.

        Returns:
        - A list of songs for which the addition to the playlist failed.
        """
        playlist_id = self.get_playlist_id(playlist_title)
        errors_list = []

        for i, song in enumerate(songs):
            try:
                print(f'{i}: exporting {song}')
                response = self.yt_music.search(song, filter='songs')
                firstItem = response[0]['videoId']
                status = self.yt_music.add_playlist_items(playlistId=playlist_id, videoIds=[firstItem])
                if 'STATUS_SUCCEEDED' not in status['status']:
                    errors_list.append(song)
            except Exception as e:
                errors_list.append(song)
                print(f'Error: {e}')
        return errors_list

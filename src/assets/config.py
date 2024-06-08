"""
Module with config variables to store and easy to change

PS: Client_id and client_secret are sensitive information and therefore should not be stored openly like this
"""

spotify_client_id = '?'
spotify_redirect_uri = 'http://localhost:8888/callback'
spotify_client_secret = '?'
port = 8888

scope = 'playlist-read-private user-read-private user-read-email'
spotify_auth_url = 'https://accounts.spotify.com/authorize'
spotify_user_info_url = 'https://api.spotify.com/v1/me'
spotify_playlist_info_url = 'https://api.spotify.com/v1/playlists/'
spotify_user_playlists_info_url = 'https://api.spotify.com/v1/me/playlists'
spotify_token_url = 'https://accounts.spotify.com/api/token'
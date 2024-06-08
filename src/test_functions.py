import pytest

from pylint.reporters import CollectingReporter
import src.assets.config as config_variables
from src.SpotifyHandler.spotify_login import SpotifyLogin
from src.SpotifyHandler.spotify_api import SpotifyApi
from src.app.auxiliary_functions import send_request, error_in_json
from unittest.mock import MagicMock
from pylint.lint import Run
import inspect
from src.YTmusicHandler.yt_music import YTMusicHandler
from pathlib import Path


@pytest.fixture
def spotify_api_instance():
    return SpotifyApi()


@pytest.fixture
def spotify_login_instance():
    return SpotifyLogin()


def test_get_authorization_url(monkeypatch):
    # Mock the generate_random_string and generate_code_challenge functions if necessary
    monkeypatch.setattr("src.SpotifyHandler.spotify_login.auxiliary_functions.generate_random_string", lambda x: "mocked_random_string")
    monkeypatch.setattr("src.SpotifyHandler.spotify_login.auxiliary_functions.generate_code_challenge", lambda x: "mocked_code_challenge")

    # Mock the config values if necessary
    monkeypatch.setattr("src.assets.config.spotify_auth_url", "mocked_auth_url")
    monkeypatch.setattr("src.assets.config.scope", "mocked_scope")
    monkeypatch.setattr("src.assets.config.spotify_client_id", "client_id")
    monkeypatch.setattr("src.assets.config.spotify_redirect_uri", "redirect_uri")

    # Call the method and get the result
    authorization_url = SpotifyLogin.get_authorization_url()

    # Assert the expected result
    expected_url = "mocked_auth_url?response_type=code&client_id=client_id&scope=mocked_scope&redirect_uri=redirect_uri&code_challenge_method=S256&code_challenge=mocked_code_challenge"
    assert authorization_url == expected_url


def test_get_auth_header(spotify_api_instance):
    # Set a custom access token for testing
    spotify_api_instance.access_token = "some_access_token"

    # Call the method to get the auth header
    auth_header = spotify_api_instance.get_auth_header()

    # Assertion to check if the Authorization key is present in the header
    assert "Authorization" in auth_header

    # Assertion to check if the access token is correctly formatted
    assert auth_header["Authorization"].startswith("Bearer ")
    assert len(auth_header["Authorization"]) > len("Bearer ")

    # Assertion to check if the access token matches the expected value
    assert auth_header["Authorization"] == f"Bearer {spotify_api_instance.access_token}"


@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"mock_key": "mock_value"}
    return mock


def test_make_test_request_successful(mock_response, spotify_api_instance, monkeypatch):
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.send_request",
        lambda url, headers: mock_response
    )
    spotify_api_instance.access_token = 'some_access_token'
    result = spotify_api_instance.make_test_request()

    assert result == {"mock_key": "mock_value"}


def test_make_test_request_no_access_token(spotify_api_instance):
    result = spotify_api_instance.make_test_request()

    assert result is None


def test_make_test_request_request_error(mock_response, spotify_api_instance, monkeypatch):
    mock_response.status_code = 500  # Simulating an error response
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.send_request",
        lambda url, headers: mock_response
    )
    spotify_api_instance.access_token = 'some_access_token'
    result = spotify_api_instance.make_test_request()

    assert result is None


def test_make_test_request_json_error(mock_response, spotify_api_instance, monkeypatch):
    mock_response.json.side_effect = ValueError("Invalid JSON")
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.send_request",
        lambda url, headers: mock_response
    )

    result = spotify_api_instance.make_test_request()

    assert result is None


def test_get_playlist_successful(mock_response, spotify_api_instance, monkeypatch):
    playlist_id = "your_playlist_id"
    url = f"{config_variables.spotify_playlist_info_url}{playlist_id}"
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.send_request",
        lambda url, headers: mock_response
    )
    spotify_api_instance.access_token = 'some_access_token'
    result = spotify_api_instance.get_playlist(playlist_id)

    assert result == {"mock_key": "mock_value"}


def test_get_playlist_no_auth_header(spotify_api_instance):
    playlist_id = "your_playlist_id"
    spotify_api_instance.get_auth_header = MagicMock(return_value=None)

    result = spotify_api_instance.get_playlist(playlist_id)

    assert result is None


def test_get_playlist_request_error(mock_response, spotify_api_instance, monkeypatch):
    playlist_id = "your_playlist_id"
    url = f"{config_variables.spotify_playlist_info_url}{playlist_id}"
    mock_response.status_code = 500  # Simulating an error response
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.send_request",
        lambda url, headers: mock_response
    )
    spotify_api_instance.access_token = 'some_access_token'
    result = spotify_api_instance.get_playlist(playlist_id)

    assert result is None


def test_get_playlist_json_error(mock_response, spotify_api_instance, monkeypatch):
    playlist_id = "your_playlist_id"
    url = f"{config_variables.spotify_playlist_info_url}{playlist_id}"
    mock_response.json.side_effect = ValueError("Invalid JSON")
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.send_request",
        lambda url, headers: mock_response
    )
    spotify_api_instance.access_token = 'some_access_token'
    result = spotify_api_instance.get_playlist(playlist_id)

    assert result is None


def test_get_user_playlists_successful(mock_response, spotify_api_instance, monkeypatch):
    url = config_variables.spotify_user_playlists_info_url
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.send_request",
        lambda url, headers, params: mock_response
    )
    spotify_api_instance.access_token = 'some_access_token'
    result = spotify_api_instance.get_user_playlists()

    assert result == {"mock_key": "mock_value"}


def test_get_user_playlists_no_auth_header(spotify_api_instance):
    spotify_api_instance.get_auth_header = MagicMock(return_value=None)

    result = spotify_api_instance.get_user_playlists()

    assert result is None


def test_get_user_playlists_request_error(mock_response, spotify_api_instance, monkeypatch):
    url = config_variables.spotify_user_playlists_info_url
    mock_response.status_code = 500  # Simulating an error response
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.send_request",
        lambda url, headers, params: mock_response
    )
    spotify_api_instance.access_token = 'some_access_token'
    result = spotify_api_instance.get_user_playlists()

    assert result is None


def test_get_user_playlists_json_error(mock_response, spotify_api_instance, monkeypatch):
    url = config_variables.spotify_user_playlists_info_url
    mock_response.json.side_effect = ValueError("Invalid JSON")
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.send_request",
        lambda url, headers, params: mock_response
    )
    spotify_api_instance.access_token = 'some_access_token'
    result = spotify_api_instance.get_user_playlists()

    assert result is None


def test_get_all_playlists_no_user_playlists(mock_response, spotify_api_instance, monkeypatch):
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.SpotifyApi.get_user_playlists",
        lambda self: None
    )

    spotify_api_instance.get_all_playlists()

    assert spotify_api_instance.spotify_playlists == {}


def test_get_playlists_info():
    # Example response from Spotify API
    response = {
        'next': 'next_url',
        'previous': 'previous_url',
        'items': [
            {
                'name': 'Playlist 1',
                'images': [{'url': 'image_url_1'}],
                'tracks': {'total': 666}
            },
            {
                'name': 'Playlist 2',
                'images': [{'url': 'image_url_2'}],
                'tracks': {'total': 1337}
            }
        ]
    }

    result = SpotifyApi.get_playlists_info(response)

    # Check if the result has the correct structure and values
    assert result == ['previous_url', 'next_url', {
        'Playlist 1': {'images': [{'url': 'image_url_1'}], 'tracks_api': {'total': 666}},
        'Playlist 2': {'images': [{'url': 'image_url_2'}], 'tracks_api': {'total': 1337}}
    }]


def test_get_playlists_info_missing_fields():
    # Example response with missing fields
    response = {'next': 'next_url', 'previous': 'previous_url', 'items': []}

    result = SpotifyApi.get_playlists_info(response)

    # Check if the result has the correct structure and empty playlist information
    assert result == ['previous_url', 'next_url', {}]


def test_get_playlists_info_missing_values():
    # Example response with missing values for some playlists
    response = {
        'next': 'next_url',
        'previous': 'previous_url',
        'items': [
            {'name': 'Playlist 1', 'images': [{'url': 'image_url_1'}]},
            {'name': 'Playlist 2', 'tracks': {'total': 15}}
        ]
    }

    result = SpotifyApi.get_playlists_info(response)

    # Check if the result has the correct structure and handles missing values
    assert result == ['previous_url', 'next_url', {
        'Playlist 1': {'images': [{'url': 'image_url_1'}], 'tracks_api': None},
        'Playlist 2': {'images': None, 'tracks_api': {'total': 15}}
    }]


def test_get_playlist_items_request_error(mock_response, spotify_api_instance, monkeypatch):
    playlist_url = "playlist_url"
    headers = {"Authorization": "Bearer access_token"}
    mock_response.json.side_effect = [{'error': 'Error message'}]
    timeout = 30

    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.requests.get",
        lambda url, headers, timeout=timeout: mock_response
    )
    monkeypatch.setattr(
        "src.SpotifyHandler.spotify_api.SpotifyApi.get_auth_header",
        lambda self: headers
    )
    spotify_api_instance.access_token = 'some_access_token'
    result = spotify_api_instance.get_playlist_items(playlist_url)

    assert result == {'error': 'Error message'}


def test_get_tracks_successful():
    response = [
        {'track': {'artists': [{'name': 'Artist 1'}], 'name': 'Track 1'}},
        {'track': {'artists': [{'name': 'Artist 2'}], 'name': 'Track 2'}}
    ]

    result = SpotifyApi.get_tracks(response)

    # Check if the result has the correct structure and values
    assert result == ['Artist 1 - Track 1', 'Artist 2 - Track 2']


def test_get_tracks_empty_response():
    # Example response with an empty list
    response = []

    result = SpotifyApi.get_tracks(response)

    # Check if the result handles an empty response correctly
    assert result is None


def test_get_tracks_error_response():
    # Example response with an error
    response = {'error': 'Error message'}

    result = SpotifyApi.get_tracks(response)

    # Check if the result returns the appropriate error code
    assert result == 401


@pytest.fixture
def yt_music_handler():
    yt_music_mock = MagicMock()
    handler = YTMusicHandler(auth=None)
    handler.yt_music = yt_music_mock
    return handler, yt_music_mock


def test_yt_test_request(yt_music_handler):
    handler, yt_music_mock = yt_music_handler
    yt_music_mock.create_playlist.return_value = "test_playlist_id"

    result = handler.test_request()

    assert result is True
    yt_music_mock.create_playlist.assert_called_once_with("test playlist", "test description")


def test_yt_create_playlist(yt_music_handler):
    handler, yt_music_mock = yt_music_handler
    yt_music_mock.create_playlist.return_value = "new_playlist_id"

    response = handler.create_playlist("New Playlist", "Playlist Description")

    assert response == "new_playlist_id"
    yt_music_mock.create_playlist.assert_called_once_with("New Playlist", "Playlist Description")


def test_yt_create_playlist_push_songs(yt_music_handler):
    handler, yt_music_mock = yt_music_handler
    yt_music_mock.create_playlist.return_value = "existing_playlist_id"
    yt_music_mock.search.return_value = [{'videoId': 'song_video_id'}]
    yt_music_mock.add_playlist_items.return_value = {'status': 'STATUS_SUCCEEDED'}

    songs = ["Song 1", "Song 2", "Song 3"]
    errors_list = handler.create_playlist_push_songs("Existing Playlist", "Playlist Description", songs)

    assert errors_list == []
    yt_music_mock.create_playlist.assert_called_once_with("Existing Playlist", "Playlist Description")
    yt_music_mock.add_playlist_items.assert_called_with(playlistId='existing_playlist_id', videoIds=['song_video_id'])


def test_yt_get_current_playlists(yt_music_handler):
    handler, yt_music_mock = yt_music_handler
    yt_music_mock.get_library_playlists.return_value = [
        {'title': 'Playlist 1', 'playlistId': 'id1'},
        {'title': 'Playlist 2', 'playlistId': 'id2'}
    ]

    handler.get_current_playlists()

    assert handler.user_playlists_id == {'Playlist 1': 'id1', 'Playlist 2': 'id2'}
    yt_music_mock.get_library_playlists.assert_called_once()


def test_yt_push_to_existing_playlist(yt_music_handler):
    handler, yt_music_mock = yt_music_handler
    yt_music_mock.get_library_playlists.return_value = [
        {'title': 'Existing Playlist', 'playlistId': 'existing_id'}
    ]
    yt_music_mock.search.return_value = [{'videoId': 'song_video_id'}]
    yt_music_mock.add_playlist_items.return_value = {'status': 'STATUS_SUCCEEDED'}

    songs = ["Song 1", "Song 2", "Song 3"]
    errors_list = handler.push_to_existing_playlist("Existing Playlist", songs)

    assert errors_list == []
    yt_music_mock.get_library_playlists.assert_called_once()
    yt_music_mock.add_playlist_items.assert_called_with(playlistId='existing_id', videoIds=['song_video_id'])


def test_yt_get_playlist_id(yt_music_handler):
    handler, yt_music_mock = yt_music_handler
    yt_music_mock.get_library_playlists.return_value = [
        {'title': 'Playlist 1', 'playlistId': 'id1'},
        {'title': 'Playlist 2', 'playlistId': 'id2'}
    ]

    playlist_id = handler.get_playlist_id("Playlist 1")

    assert playlist_id == 'id1'
    yt_music_mock.get_library_playlists.assert_called_once()


@pytest.fixture(scope="session")
def linter_auxiliary():
    """ Test codestyle for src file of auxiliary_functions.py file. """
    src_file = inspect.getfile(send_request)
    rep = CollectingReporter()
    # disabled warnings:
    # 0301 line too long
    # 0103 variables name (does not like shorter than 2 chars)
    # 0719 too general exception (needed for invalid trees without defining own exception class)
    r = Run(['--disable=C0301,C0103,W0719', '-sn', src_file], reporter=rep, exit=False)
    return r.linter


@pytest.mark.parametrize("limit", range(0, 11))
def test_codestyle_score_auxiliary_functions(linter_auxiliary, limit, runs=[]):
    """ Evaluate codestyle for different thresholds. """
    if len(runs) == 0:
        print('\nLinter output:')
        for m in linter_auxiliary.reporter.messages:
            print(f'{m.msg_id} ({m.symbol}) line {m.line}: {m.msg}')
    runs.append(limit)
    # score = linter.stats['global_note']
    score = linter_auxiliary.stats.global_note

    print(f'pylint score = {score} limit = {limit}')
    assert score >= limit


@pytest.fixture(scope="session")
def linter_spotify_login():
    """ Test codestyle for src file of spotify_login.py file. """

    src_file = Path(__file__).resolve().parent.parent / 'SpotifyHandler' / 'spotify_login.py'
    rep = CollectingReporter()
    # disabled warnings:
    # 0301 line too long
    # 0103 variables name (does not like shorter than 2 chars)
    # 0719 too general exception (needed for invalid trees without defining own exception class)
    r = Run(['--disable=C0301,C0103,W0719', '-sn', src_file], reporter=rep, exit=False)
    return r.linter


"""
DOESNT WORK, DONT KNOW WHY

@pytest.mark.parametrize("limit", range(0, 11))
def test_codestyle_score_spotify_login(linter_spotify_login, limit, runs=[]):
    if len(runs) == 0:
        print('\nLinter output:')
        for m in linter_spotify_login.reporter.messages:
            print(f'{m.msg_id} ({m.symbol}) line {m.line}: {m.msg}')
    runs.append(limit)
    # score = linter.stats['global_note']
    score = linter_spotify_login.stats.global_note

    print(f'pylint score = {score} limit = {limit}')
    assert score >= limit
"""

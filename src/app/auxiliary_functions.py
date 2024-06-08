"""
Module with auxiliary function for easy access to some functions required in different parts of the app

"""

import base64
import hashlib
import os
import random
import socket
import string
import webbrowser
from pathlib import Path

import requests


def find_files():
    """
    Finds and returns file paths for access token and refresh token.

    Returns:
    - A set containing file paths for the access token and refresh token.
    """
    current_file = Path(__file__).resolve()
    src_dir = None
    for parent in current_file.parents:
        if parent.name == 'src':
            src_dir = parent
            break
    if src_dir:
        access_token_path = src_dir / 'assets/access_token'
        refresh_token_path = src_dir / 'assets/refresh_token'
        if Path.exists(access_token_path) and Path.exists(refresh_token_path):
            return {access_token_path, refresh_token_path}
        if Path.exists(access_token_path):
            with open(src_dir / 'assets/refresh_token', 'x', encoding='utf-8') as f:
                f.truncate(0)
            # f = open(src_dir / 'assets/refresh_token', 'x', encoding='utf-8')
            # f.close()

        elif Path.exists(refresh_token_path):
            with open(src_dir / 'assets/access_token', 'x',encoding='utf-8') as f:
                f.truncate(0)
            # f = open(src_dir / 'assets/access_token', 'x',encoding='utf-8')
            # f.close()

        else:
            with open(src_dir / 'assets/refresh_token', 'x', encoding='utf-8') as f:
                f.truncate(0)
            # f = open(src_dir / 'assets/refresh_token', 'x', encoding='utf-8')
            # f.close()
            with open(src_dir / 'assets/access_token', 'x', encoding='utf-8') as f:
                f.truncate(0)
            # f = open(src_dir / 'assets/access_token', 'x', encoding='utf-8')
            # f.close()

    return access_token_path, refresh_token_path

def clear_files():
    """
    Clears content and removes specific files related to authentication.

    This function is typically called to reset authentication-related files during application initialization.

    PS: Sensitive information like api keys should be stored in environ and some secure space, like database.
    It wasn't in my abilities to transfer keys securely and I chose the easiest and not secure way.

    """
    current_file = Path(__file__).resolve()
    src_dir = None
    for parent in current_file.parents:
        if parent.name == 'src':
            src_dir = parent
            break
    if src_dir:
        access_token_path = src_dir / 'assets/access_token'
        refresh_token_path = src_dir / 'assets/refresh_token'
        oauth_path = src_dir / 'oauth.json'
        with open(access_token_path, "w", encoding='utf-8') as f:
            f.truncate(0)

        with open(refresh_token_path, "w", encoding='utf-8') as f:
            f.truncate(0)
        try:
            os.remove(oauth_path)
        except FileNotFoundError:
            print(f"File {oauth_path} not found. Ignore if this is first start up")
        except PermissionError:
            print(f"Permission error: unable to delete {oauth_path}")
        except OSError as e:
            print(f'Error: {e}')


def generate_code_challenge(code_verifier):
    """
    Generates a code challenge for the PKCE (Proof Key for Code Exchange) authorization flow.

    Parameters:
    - code_verifier (str): The code verifier used to generate the code challenge.

    Returns:
    - str: The generated code challenge.
    """
    sha256_hash = hashlib.sha256(code_verifier.encode()).digest()
    base64_encoded = base64.urlsafe_b64encode(sha256_hash).rstrip(b'=')
    return base64_encoded.decode()


def generate_random_string(length):
    """
    Generates a random string of a specified length.

    Parameters:
    - length (int): The desired length of the random string.

    Returns:
    - str: The generated random string.
    """
    characters = string.ascii_letters + string.digits + '-._~'
    return ''.join(random.choice(characters) for _ in range(length))


def open_browser(url):
    """
    Opens the default web browser to the specified URL.

    Parameters:
    - url (str): The URL to be opened in the web browser.
    """
    webbrowser.open(url)


def find_open_port(start_port, end_port):
    """
    Finds an open port within a specified range.

    Parameters:
    - start_port (int): The starting port of the range.
    - end_port (int): The ending port of the range.

    Returns:
    - int or None: The first open port found within the range, or None if no open ports are found.
    """
    for port in range(start_port, end_port + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        if result != 0:  # Open port
            return port
    return None  # No open ports


def send_request(url, headers, params=None):
    """
    Sends an HTTP GET request to the specified URL with optional headers and parameters.

    Parameters:
    - url (str): The URL to send the request to.
    - headers (dict): The headers to include in the request.
    - params (dict, optional): The parameters to include in the request. Defaults to None.

    Returns:
    - requests.Response or None: The response object if the request is successful, otherwise None.
    """
    timeout = 30
    try:
        if params is None:
            response = requests.get(url, headers=headers, timeout=timeout)
        else:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None


def error_in_json(response):
    """
    Checks if there is an error in the JSON response.

    Parameters:
    - response (requests.Response or None): The response object from an HTTP request.

    Returns:
    - bool: True if there is an error in the JSON response, False otherwise.
    """
    if response is None:
        return True
    if response.status_code != 200:
        return True

    try:
        json_response = response.json()
        if 'error' in json_response:
            return True
    except ValueError:
        return True

    return False

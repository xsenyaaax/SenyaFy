"""
SenyaFy Music Converter Module

This module defines the main application class for SenyaFy Music Converter. The application facilitates the conversion
and export of songs between Spotify and YouTube Music. It includes functions for initializing, authenticating,
and updating playlists and songs, as well as handling user interactions for exporting songs.

Classes:
    - MessageWindow: Tkinter top level window with specified message in constructor
    - YoutubePlaylistChooser: Tkinter top level window with YT Music user playlists
    - ScrollableRadiobuttonFrame: Frame with responsive radiobutton list and functions to get checked, add, remove items
    - ScrollableCheckBoxFrame: Frame with responsive checked box list and functions to get checked, add, remove items
    - App: main application that controls everything, updates UI.

Note: Adjustments and modifications may be needed based on specific implementations and requirements.
PS: I am very bad at planning and creating GUI. GUI logic and layout was taken as inspiration and modified to suit my
purposes. https://github.com/TomSchimansky/CustomTkinter/tree/master/examples
"""

import os
import threading
import time
from pathlib import Path

import customtkinter
import ytmusicapi
from PIL import Image
import json

import src.app.auxiliary_functions as af
from src.SpotifyHandler import spotify_login, my_flask, spotify_api
from src.YTmusicHandler import yt_music
import src.assets.config as config

customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"
customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"


class MessageWindow(customtkinter.CTkToplevel):
    """
    Class that displays window with specified text
    """

    def __init__(self, master, text, **kwargs):
        super().__init__(master, **kwargs)
        self.geometry("400x300")

        self.label = customtkinter.CTkLabel(self, text=text)
        self.label.pack(padx=20, pady=20)


class ReportWindow(customtkinter.CTkToplevel):
    """
    Class that displays window with specified text
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.geometry("400x300")

        self.textbox = customtkinter.CTkTextbox(self, width=400, height=300)
        self.textbox.grid(row=1, column=1, sticky="nsew")


class YoutubePlaylistChooser(customtkinter.CTkToplevel):
    """
    Class that displays playlists and list and lets to choose from it.
    """

    def __init__(self, master, item_list, button_command, **kwargs):
        super().__init__(master, **kwargs)
        self.export_command = button_command
        self.geometry("400x300")
        self.title("YT Music playlists")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.radiobutton_variable = customtkinter.StringVar()
        self.scrollable_checkbox_frame = ScrollableRadiobuttonFrame(self, item_list=item_list,
                                                                    label_text="Yours Youtube Playlists",
                                                                    command=self.radiobutton_frame_event
                                                                    )
        self.button1 = customtkinter.CTkButton(self, text="Export to chosen playlist",
                                               command=self.export_command)
        # self.button1.configure(command=self.export_command)
        self.scrollable_checkbox_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")
        self.button1.grid(row=2, column=0, padx=10, pady=10, sticky="ew", columnspan=2)

    def get_checked_item(self):
        return self.scrollable_checkbox_frame.get_checked_item()

    def export_to_chosen_playlist(self):
        print(f'Exporting to: {self.scrollable_checkbox_frame.get_checked_item()}')

    def radiobutton_frame_event(self):
        print(f"New YTMusic playlist chosen: {self.scrollable_checkbox_frame.get_checked_item()}")


class ScrollableRadiobuttonFrame(customtkinter.CTkScrollableFrame):
    """
    Frame with responsive radiobutton list and functions to get checked, add, remove items
    """

    def __init__(self, master, item_list, command=None, **kwargs):
        super().__init__(master, **kwargs)

        self.command = command
        self.radiobutton_variable = customtkinter.StringVar()
        self.radiobutton_list = []
        for i, item in enumerate(item_list):
            self.add_item(item)

    def add_item(self, item):
        radiobutton = customtkinter.CTkRadioButton(self, text=item, value=item, variable=self.radiobutton_variable)
        if self.command is not None:
            radiobutton.configure(command=self.command)
        radiobutton.grid(row=len(self.radiobutton_list), column=0, pady=(0, 10), sticky='w')
        self.radiobutton_list.append(radiobutton)

    def remove_item(self, item):
        for radiobutton in self.radiobutton_list:
            if item == radiobutton.cget("text"):
                radiobutton.destroy()
                self.radiobutton_list.remove(radiobutton)
                return

    def get_checked_item(self):
        return self.radiobutton_variable.get()


class ScrollableCheckBoxFrame(customtkinter.CTkScrollableFrame):
    """
    Frame with responsive checked box list and functions to get checked, add, remove items
    """

    def __init__(self, master, item_list, command=None, **kwargs):
        super().__init__(master, **kwargs)

        self.command = command
        self.checkbox_list = []
        for i, item in enumerate(item_list):
            self.add_item(item)

    def add_item(self, item):
        checkbox = customtkinter.CTkCheckBox(self, text=item)
        if self.command is not None:
            checkbox.configure(command=self.command)
        checkbox.grid(row=len(self.checkbox_list), column=0, pady=(0, 10), sticky='w')
        self.checkbox_list.append(checkbox)

    def remove_item(self, item):
        for checkbox in self.checkbox_list:
            if item == checkbox.cget("text"):
                checkbox.destroy()
                self.checkbox_list.remove(checkbox)
                return

    def remove_all(self):
        for checkbox in self.checkbox_list:
            checkbox.destroy()
            self.checkbox_list.remove(checkbox)

    def get_checked_items(self):
        return [checkbox.cget("text") for checkbox in self.checkbox_list if checkbox.get() == 1]


# https://github.com/TomSchimansky/CustomTkinter/blob/master/examples/image_example.py
class App(customtkinter.CTk):
    """
    Main app class
    """

    def __init__(self):
        super().__init__()

        self.title("SenyaiFy: Spotify to YT music exporter")
        self.geometry("800x550")

        # set grid layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        current_file = Path(__file__).resolve()
        path = None
        for parent in current_file.parents:
            if parent.name == 'src':
                path = parent
                break
        path = path / 'gui'

        # ------------------ USED IMAGES ------------------
        self.home_logo_image = customtkinter.CTkImage(light_image=Image.open(path / 'black_text_logo.png'),
                                                      dark_image=Image.open(path / 'white_text_logo.png'),
                                                      size=(400, 200))
        self.spotify_icon_image = customtkinter.CTkImage(Image.open(path / 'spotify-logo.png'), size=(20, 20))
        self.yt_icon_image = customtkinter.CTkImage(Image.open(path / 'youtube.png'), size=(20, 20))
        self.questionmark_image = customtkinter.CTkImage(Image.open(path / 'questionmark_green.png'), size=(20, 20))
        self.connection_image = customtkinter.CTkImage(Image.open(path / 'connection.png'), size=(20, 20))
        self.secret_icon_image = customtkinter.CTkImage(Image.open(path / 'egg.png'), size=(20, 20))
        self.home_image = customtkinter.CTkImage(light_image=Image.open(path / 'home_green2.png'),
                                                 dark_image=Image.open(path / 'home_green2.png'), size=(20, 20))
        self.share_image = customtkinter.CTkImage(light_image=Image.open(path / 'share_green2edited.png'),
                                                  dark_image=Image.open(path / 'share_green2edited.png'), size=(20, 20))
        # --------------------------------------------------

        # ---------------- create navigation frame ----------------------
        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text="Senyafy",
                                                             # image=self.logo_image,
                                                             compound="left",
                                                             font=customtkinter.CTkFont(family='Algerian', size=19,
                                                                                        weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10,
                                                   text="Home",
                                                   fg_color="transparent", text_color=("gray10", "gray90"),
                                                   hover_color=("gray70", "gray30"),
                                                   image=self.home_image, anchor="w", command=self.home_button_event,
                                                   font=("Futura", 16)
                                                   )
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.export_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40,
                                                     border_spacing=10, text="Export Music",
                                                     fg_color="transparent", text_color=("gray10", "gray90"),
                                                     hover_color=("gray70", "gray30"),
                                                     image=self.share_image, anchor="w",
                                                     command=self.frame_2_button_event,
                                                     font=("Futura", 16)
                                                     )
        self.export_button.grid(row=2, column=0, sticky="ew")

        self.about_app_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40,
                                                        border_spacing=10, text="About app",
                                                        fg_color="transparent", text_color=("gray10", "gray90"),
                                                        hover_color=("gray70", "gray30"),
                                                        image=self.questionmark_image, anchor="w",
                                                        command=self.frame_3_button_event)
        self.about_app_button.grid(row=3, column=0, sticky="ew")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(self.navigation_frame,
                                                                values=["Light", "Dark", "System"],
                                                                command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=4, column=0, padx=20, pady=20, sticky="s")
        # ---------------------------------------------------------

        # ---------------- create home frame ----------------------
        self.home_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.home_frame_large_image_label = customtkinter.CTkLabel(self.home_frame, text="",
                                                                   image=self.home_logo_image)
        self.home_frame_large_image_label.grid(row=0, column=0, padx=20, pady=10)

        self.home_spotify_login_button = customtkinter.CTkButton(self.home_frame, text="Spotify Login",
                                                                 image=self.spotify_icon_image, compound="left",
                                                                 anchor="w",
                                                                 font=("Open Sans", 15),
                                                                 text_color=("#212121", "#FAFAFA"),
                                                                 command=self.spotify_login_button_pressed
                                                                 )
        self.home_spotify_login_button.grid(row=1, column=0, padx=20, pady=10)
        self.home_yt_login_button = customtkinter.CTkButton(self.home_frame, text="Youtube Login",
                                                            image=self.yt_icon_image, compound="left", anchor="w",
                                                            font=("Open Sans", 14),
                                                            text_color=("#212121", "#FAFAFA"),
                                                            command=self.yt_login_button_pressed
                                                            )
        self.home_yt_login_button.grid(row=2, column=0, padx=20, pady=10)
        self.home_about_button = customtkinter.CTkButton(self.home_frame, text="Connection",
                                                         image=self.connection_image, compound="left", anchor="w",
                                                         font=("Open Sans", 15),
                                                         text_color=("#212121", "#FAFAFA"),
                                                         command=self.make_test_request
                                                         )
        self.home_about_button.grid(row=3, column=0, padx=20, pady=10)
        self.home_easter_egg_button = customtkinter.CTkButton(self.home_frame, text="Easter egg",
                                                              image=self.secret_icon_image, compound="left", anchor="w",
                                                              font=("Open Sans", 15),
                                                              text_color=("#212121", "#FAFAFA"),
                                                              command=self.easter_egg
                                                              )
        self.home_easter_egg_button.grid(row=4, column=0, padx=20, pady=10)
        # ------------------------------------------------------

        # ---------------- create export frame ----------------------
        self.export_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.export_frame.grid_rowconfigure(0, weight=1)
        self.export_frame.grid_columnconfigure(0, weight=1)

        self.spotify_playlists_frame = ScrollableRadiobuttonFrame(self.export_frame, width=300,
                                                                  command=self.radiobutton_frame_event,
                                                                  item_list=[],
                                                                  label_text="Yours Spotify Playlists",
                                                                  )

        self.spotify_songs_frame = ScrollableCheckBoxFrame(self.export_frame, width=300, height=200,
                                                           command=self.checkbox_frame_event,
                                                           item_list=[],
                                                           label_text="Playlist Songs", )

        self.spotify_playlists_frame.grid(row=0, column=0, padx=15, pady=15, sticky="new")
        self.spotify_songs_frame.grid(row=1, column=0, padx=15, pady=15, sticky="new")
        self.option_menu_export_frame = customtkinter.CTkOptionMenu(self.export_frame,
                                                                    values=["Export Current Playlist",
                                                                            "Export Chosen Songs to new Playlist",
                                                                            "Export Chosen Songs to existing Playlist"
                                                                            ],
                                                                    variable=customtkinter.StringVar(
                                                                        value="Export Options"),
                                                                    command=self.exportmenu_callback
                                                                    )
        self.option_menu_export_frame.grid(row=3, column=0, pady=10)
        # -----------------------------------------------------------

        # create third frame
        self.third_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")

        # select default frame
        self.select_frame_by_name("home")

        # VARIABLES
        self.report_window = None  # tkinter top level with report status of exported songs
        self.yt_playlists_chooser_window = None  # tkinter top level window with yt playlists
        self.message_window = None  # variable to open top level window with some message
        self.spotifyLogin = None  # used to authenticate user in spotify
        self.spotifyApi = None  # used to communicate with spotify api
        self.flask_thread = None  # used to help to retrieve spotify api token
        self.ytMusic = None  # used to communicate with yt music api
        self.chosen_songs = []  # chosen songs in current spotify playlist
        self.current_playlist = None  # current chosen spotify playlist in frame
        self.yt_connected = False  # bool to know if yt music api is successfully connected

    def initialize(self):
        """
        Initializes the necessary components for the application.

        This function performs the following tasks:
        1. Clears the contents of the access and refresh token files.
        2. Sets up Spotify API credentials and authentication parameters.
        3. Initializes a SpotifyLogin instance for user authentication.
        4. Initializes a SpotifyApi instance for making API requests.

        Note: This function is typically called at the start of the application to ensure a clean and
        well-configured state for handling Spotify authentication and API interactions.
        """

        access_token_path, refresh_token_path = af.find_files()

        with open(access_token_path, "w") as f:
            f.truncate(0)

        with open(refresh_token_path, "w") as f:
            f.truncate(0)

        # client_id = config.spotify_client_id
        # redirect_uri = config.spotify_redirect_uri
        # client_secret = config.spotify_client_secret
        # port = config.port

        self.spotifyLogin = spotify_login.SpotifyLogin()
        self.spotifyApi = spotify_api.SpotifyApi()

    def make_test_request(self):
        """
        Performs a test request to check the connectivity of Spotify and YouTube Music services.

        This function does the following:
        1. Sends a test request to the Spotify API using the SpotifyApi instance.
        2. Checks the connectivity of the YouTube Music service by invoking the test_request method of the self.ytMusic.
        3. Displays a message window indicating the status of the connections:
           - If both Spotify and YouTube Music connections fail, a message prompts manual connection for both.
           - If only YouTube Music connection fails, a message prompts manual connection for YouTube Music.
           - If only Spotify connection fails, a message prompts manual connection for Spotify.
           - If both connections succeed, a message indicates successful connectivity.

        Note: This function is typically used for testing the initial connectivity of Spotify and YouTube Music services
        within the application.
        """

        spotify_fail = False
        yt_fail = False
        if self.spotifyApi.make_test_request() is None:
            spotify_fail = True
        if self.ytMusic is None:
            yt_fail = True
        elif not self.ytMusic.test_request():
            yt_fail = True

        if spotify_fail and yt_fail:
            self.message_window = MessageWindow(master=self, text='Spotify and YTMusic Connection Failed. Please '
                                                                  'connect manually')
        elif yt_fail:
            self.message_window = MessageWindow(master=self, text='YT Music Connection Failed. Please connect manually')
        elif spotify_fail:
            self.message_window = MessageWindow(master=self, text='Spotify Connection Failed. Please connect manually')
        else:
            self.message_window = MessageWindow(master=self, text='Connected successfully')

    def init_yt_oauth_terminal(self):
        """
        Initializes the YouTube Music OAuth process through the terminal.

        This function performs the following tasks:
        1. Determines the path to the 'oauth.json' file within the 'assets' folder.
        2. Attempts to remove any existing 'oauth.json' file.
        3. Initiates the YouTube Music OAuth process by calling ytmusicapi.setup_oauth with open_browser=True.
        4. Saves the OAuth response data to the 'oauth.json' file.
        5. Creates an instance of YTMusicHandler using the 'oauth.json' file.
        6. Sets self.yt_connected to True if the YTMusicHandler instance is successfully created.
        7. Prints a confirmation message indicating that the OAuth JSON has been saved.
        """
        current_folder = Path(__file__).resolve().parent.parent
        oauth_json_path = current_folder / 'assets' / 'oauth.json'
        try:
            os.remove(oauth_json_path)
        except Exception:
            raise
        ret = ytmusicapi.setup_oauth(open_browser=True)
        with open(oauth_json_path, 'w') as json_file:
            json.dump(ret, json_file, indent=4)
        self.ytMusic = yt_music.YTMusicHandler(oauth_json_path)
        if self.ytMusic is not None:
            self.yt_connected = True
        print("oauth json saved in src/assets")

    def init_spotify_terminal(self):
        """
        Initiates the Spotify authentication process through the terminal.

        This function performs the following tasks:
        1. Retrieves the authorization URL for Spotify authentication using self.spotifyLogin.
        2. Opens the default web browser with the Spotify authorization URL.

        Note: This function is typically used to start the authentication process for Spotify in a terminal.
        """
        url = self.spotifyLogin.get_authorization_url()
        af.open_browser(url)

    def run_flask(self):
        """
        Initializes and runs a Flask application for handling Spotify Login and retrieving api token.

        This function performs the following tasks:
        1. Creates an instance of the MyFlask class, passing the SpotifyLogin instance for authentication.
        2. Runs the Flask application, allowing it to handle requests related to Spotify functionalities.

        """
        my_flask_obj = my_flask.MyFlask(self.spotifyLogin)
        my_flask_obj.run()

    def select_frame_by_name(self, name):
        """
        Selects and displays frame based on clicked button in navigation bar.

        """
        # set button color for selected button
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.export_button.configure(fg_color=("gray75", "gray25") if name == "frame_2" else "transparent")
        self.about_app_button.configure(fg_color=("gray75", "gray25") if name == "frame_3" else "transparent")

        # show selected frame
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if name == "frame_2":
            self.export_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.export_frame.grid_forget()
        if name == "frame_3":
            self.third_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.third_frame.grid_forget()

    def home_button_event(self):
        """
        Select home frame
        """
        self.select_frame_by_name("home")

    def frame_2_button_event(self):
        """
        Select export frame
        """
        self.select_frame_by_name("frame_2")

    def frame_3_button_event(self):
        """
        Select about app frame
        """
        af.open_browser('https://gitlab.fit.cvut.cz/BI-PYT/b231/pogodars/-/blob/semestral/README.md?ref_type=heads')
        self.select_frame_by_name("frame_3")

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode):
        """
        Changes appearance of app based on clicked item in list
        """
        customtkinter.set_appearance_mode(new_appearance_mode)

    def radiobutton_frame_event(self):
        """
        Event handler for radio button selections in the Spotify playlists frame.

        This function is triggered when a user selects a different Spotify playlist, and it ensures that the
        application has the necessary playlist information for further interactions.
        """
        print(f"Spotify playlist chosen: {self.spotify_playlists_frame.get_checked_item()}")
        print(f'Getting items for {self.spotify_playlists_frame.get_checked_item()}...')
        name = self.spotify_playlists_frame.get_checked_item()
        if name in self.spotifyApi.spotify_playlist_songs:
            self.current_playlist = name
        else:
            p_id = self.spotifyApi.spotify_playlists[name]['tracks_api']
            self.spotifyApi.spotify_playlist_songs[name] = self.spotifyApi.get_playlist_items(p_id['href'])
            self.current_playlist = name

        self.update_songs_frame()

    def open_yt_playlist_chooser(self):
        """
        Opens a window for choosing YouTube playlists and exporting songs to the chosen playlist.

        This function is typically called when the user wants to export songs to a specific YouTube playlist.
        The window allows the user to choose a playlist from the available options.
        This window button listens to button event and starts exporting chosen songs if button is pressed
        """
        if self.yt_playlists_chooser_window is None or not self.yt_playlists_chooser_window.winfo_exists():
            self.update_playlists(spot=False)  # update in case user added playlists manually
            playlist_names = []
            if self.ytMusic is not None:
                playlist_names = list(self.ytMusic.user_playlists_id.keys())
            self.yt_playlists_chooser_window = YoutubePlaylistChooser(master=self, item_list=playlist_names,
                                                                      button_command=self.export_to_chosen_playlist
                                                                      )
            self.yt_playlists_chooser_window.focus()
        else:
            self.yt_playlists_chooser_window.focus()

    def export_to_chosen_playlist(self):
        """
        Exports selected Spotify songs to a chosen YouTube playlist.

        This function is typically called when the user wants to export selected Spotify songs to a specific
        YouTube playlist chosen from the YoutubePlaylistChooser window.
        """
        if self.yt_playlists_chooser_window.winfo_exists:
            playlist_name = self.yt_playlists_chooser_window.get_checked_item()
            error = self.ytMusic.push_to_existing_playlist(playlist_name,
                                                           self.spotify_songs_frame.get_checked_items())
            self.report_export(error)

    def exportmenu_callback(self, choice):
        """
        Callback function for the export option menu.

        This function performs the task based on the user's choice. After exporting it opens window with report about
        exporting.

        This function is typically triggered when the user selects an option from the export option menu,
        providing different export functionalities based on the chosen action.
        """
        print("Export optionmenu clicked:", choice)
        if choice == 'Export Chosen Songs to new Playlist':
            dialog = customtkinter.CTkInputDialog(text="Type in playlist name:", title="Export to new playlist")
            text = dialog.get_input()
            description = f'Exported songs from Spotify'
            print("Playlist name: ", text)
            if text is not None:
                errors = self.ytMusic.create_playlist_push_songs(text, description,
                                                                 self.spotify_songs_frame.get_checked_items())
                self.report_export(errors)
        if choice == 'Export Chosen Songs to existing Playlist':
            self.open_yt_playlist_chooser()
            self.yt_playlists_chooser_window.focus()
        if choice == 'Export Current Playlist':
            description = f'Exported {self.current_playlist} playlist from Spotify'
            errors = self.ytMusic.create_playlist_push_songs(self.current_playlist,
                                                             description,
                                                             self.spotifyApi.spotify_playlist_songs[
                                                                 self.current_playlist]
                                                             )
            self.report_export(errors)
            print("Export to new playlist")

    def report_export(self, errors):
        """
        Reports the result of the song export operation.

        This function is typically called after an attempt to export songs to a YouTube playlist.
        It communicates the outcome of the export operation to the user, allowing user to identify which songs were
        failed to export
        """
        if len(errors) == 0:
            self.message_window = MessageWindow(master=self, text='All songs exported!')
        else:
            result_list = ["Failed songs to export:"] + errors
            result_string = '\n'.join(result_list)
            # self.message_window = MessageWindow(master=self, text=result_string)
            self.report_window = ReportWindow(master=self)
            self.report_window.textbox.insert("0.0", result_string)

    def checkbox_frame_event(self):
        """
        Prints chosen songs in current Spotify playlist in console
        """
        print(f"Chosen songs modified: {self.spotify_songs_frame.get_checked_items()}")

    @staticmethod
    def easter_egg():
        """
        Just easter egg function
        """
        af.open_browser('https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley')

    def yt_login_button_pressed(self):
        """
        Handles the event when the YouTube login button is pressed.

        This function is typically triggered when the user presses the YouTube login button in the application and
        after connection in terminal failed, allowing user to authenticate manually.
        It handles the authentication process for YouTube and communicates the result to the user.
        """
        print("YT Login button pressed")
        if self.yt_connected:
            if self.message_window is None or not self.message_window.winfo_exists():
                self.message_window = MessageWindow(master=self, text='Already authenticated')
            return
        try:
            self.init_yt_oauth_terminal()
        except Exception as e:
            print(f'Error {e}. Please try again!')

    def spotify_login_button_pressed(self):
        """
        Handles the event when the Spotify login button is pressed.

        This function is typically triggered when the user presses the Spotify login button in the application and
        after connection in terminal failed, allowing user to authenticate manually.
        It handles the authentication process for Spotify and communicates the result to the user.
        """
        print("Spotify Login button pressed")
        if self.spotifyApi.access_token is not None:
            if self.message_window is None or not self.message_window.winfo_exists():
                self.message_window = MessageWindow(master=self, text='Already authenticated')
            return
        self.init_yt_oauth_terminal()

    def run(self):
        """
        Main function to start the SenyaFy Music Converter functionalities.

        Port from redirect_uri is necessary in order to allow to retrieve api token. It waits for user to open it
        if it has been used by other application

        This function is the entry point for running the SenyaFy Music Converter application.
        It sets up the necessary components, starts the Flask web server, and initiates the authentication processes.
        """
        self.initialize()

        while af.find_open_port(config.port, config.port) is None:
            time.sleep(2)
            print(f"Port {config.port} is unavailable. Open it to enable app functions")

        flask_thread = threading.Thread(target=self.run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        print("------SenyaFy Music converter------")
        af.clear_files()
        try:
            print("------Spotify authentication------")
            print("Please confirm in your browser")
            self.init_spotify_terminal()
        except Exception as e:
            print(f'Error: {e}')
        try:
            print("------YT Music authentication------")
            self.init_yt_oauth_terminal()
        except Exception as e:
            print(f'YTMusic auth Error, please connect manually: {e}')

    def update_playlists(self, spot=True, yt=True):
        """
        Updates the displayed playlists in the application.

        This function is typically called to refresh the list of displayed playlists in the application.
        It updates both Spotify and YouTube Music playlists based on the provided flags.
        """
        if self.spotifyApi is not None and spot:
            self.spotifyApi.get_all_playlists()
            for playlist in self.spotifyApi.spotify_playlists:
                self.spotify_playlists_frame.add_item(playlist)
        if self.ytMusic is not None and yt:
            self.ytMusic.get_current_playlists()

    def update_songs_frame(self):
        """
        Updates the frame displaying Spotify playlist songs in the application.

        This function is typically called when the user selects a different Spotify playlist.
        It updates the frame displaying the songs for the current playlist with the latest information.

        PS: After testing it was better to destroy frame altogether and create a new one, because after only updating
        songs some deleted text overlapped over new one, like it was pixelghosting
        """
        self.spotify_songs_frame.destroy()
        songs = self.spotifyApi.spotify_playlist_songs[self.current_playlist]
        self.spotify_songs_frame = ScrollableCheckBoxFrame(self.export_frame, width=300, height=200,
                                                           command=self.checkbox_frame_event,
                                                           item_list=songs,
                                                           label_text="Playlist Songs", )
        self.spotify_songs_frame.grid(row=1, column=0, padx=15, pady=15, sticky="new")


"""
def background_task(app):
    access_token_file, _ = find_files()

    while True:
        time.sleep(2)
        print("Checking access token")
        if os.path.getsize(access_token_file) > 0:
            print("Access token found. Updating playlists...")
            app.spotifyLogin.is_token_available()
            app.spotifyApi.access_token = app.spotifyLogin.access_token
            app.update_playlists()  # Call the method in your App class to update playlists
            break  # Exit the loop once the token is found and playlists are updated


if __name__ == "__main__":
    clear_files()
    app_instance = App()
    # app_instance.initialize()
    app_instance.run()

    access_token_thread = threading.Thread(target=background_task, daemon=True, args=(app_instance,))
    access_token_thread.start()

    app_instance.mainloop()
"""

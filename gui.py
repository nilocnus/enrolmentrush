# gui.py

import tkinter as tk
from tkinter import messagebox

import utils
import random
from client import ClientConnection
from socket_server import MAX_ROUNDS


class GUI:
    """ Main tkinter GUI window that can switch between different screens in-game. """
    def __init__(self):
        # tkinter window constructor
        self.root = tk.Tk()
        self.root.geometry("900x900")
        self.root.title("Enrolment Rush v1.0")
        self.current_round_courses = []
        self.local_username = None    # local username for client running this program; is set when player enters name
        self.game_has_ended = False

        # ─── Add these two flags for synchronisation ──────────────────────────
        self.has_picked_this_round = False
        self.in_waiting_screen = False
        # ───────────────────────────────────────────────────────────────────────        

        # handles when GUI window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        self.current_round = 1
        self.max_rounds = MAX_ROUNDS
        self.current_round_courses = []  # list of 5 dicts from server
        self.client_connection = None

        self.screens = {}
        self.init_screens()
        self.show_screen("menu")

        self.root.mainloop()

        # ------------ called by ClientConnection ------------------------------ #

    def on_seat_update(self, msg):
        """Called from the network thread -> marshal to Tk main loop first."""
        def apply():
            code = msg["course_code"]
            seats = msg.get("seats_left")
            denied = msg.get("denied", False)
            user = msg["username"]
            sel = self.screens["gameplay_course_selection"]

            # Update seat counts shown on the selection screen
            for course_info in self.current_round_courses:
                if course_info["code"] == code:
                    course_info["available_seats"] = seats
                    break

            sel.update_course_display(code, seats)

            # Only pop up to *this* client
            if user == self.local_username:
                if denied:
                    messagebox.showwarning(
                        "Seat Taken",
                        f"Sorry, you were too late: {code} is now full."
                    )
                    sel.selected_course.set("__NONE__")
                    self.show_screen("gameplay_course_selection")
                else:
                    messagebox.showinfo("Enrolled!", f"You successfully enrolled in {code}.")

                    # If the game ended while the modal dialog was open, do nothing else.
                    if self.game_has_ended:
                        return

                    # mark finished locally and move to waiting screen,
                    # but preserve any counts/points already shown
                    self.has_picked_this_round = True
                    self.in_waiting_screen = True

                    wait = self.screens["waiting"]
                    wait.title_text.config(text="Waiting for other players to finish...")
                    wait.back_button.pack_forget()
                    wait.reset_screen(preserve_count=True)
                    wait.round_label.config(text=f"Round {self.current_round}/{self.max_rounds}")
                    self.show_screen("waiting")

        self.root.after(0, apply)

    def on_game_over(self, msg):
        def apply():
            print("[GUI] applying game_over UI")
            self.game_has_ended = True
            self.in_waiting_screen = False
            self.has_picked_this_round = False

            winner = msg["winner"]
            scores = msg["final_scores"]
            self.screens["game_over"].update_game_over(winner, scores)
            self.show_screen("game_over")
        self.root.after(0, apply)

    def on_round_message(self, msg):
        """Called from the network thread -> marshal to Tk main loop first."""
        def apply():
            if self.game_has_ended:
                return

            kind = msg.get("type")

            # ─── round starts ──────────────────────────────────────────────
            if kind == "round_start":
                self.current_round = msg["round"]
                self.current_round_courses = msg["courses"]

                self.has_picked_this_round = False
                self.start_countdown(self.current_round)
                self.in_waiting_screen = False

            # ─── progress update (somebody finished) ───────────────────────
            elif kind == "round_wait":
                wait = self.screens["waiting"]
                wait.title_text.config(text="Waiting for other players to finish...")
                scores = msg.get("scores", {})
                finished_users = msg.get("users", [])

                if self.in_waiting_screen:
                    wait.network_update(msg["player_count"], finished_users, scores)
                elif self.has_picked_this_round or (self.local_username in finished_users):
                    wait.reset_screen(preserve_count=True)  # don't wipe points/UI
                    wait.round_label.config(text=f"Round {self.current_round}/{self.max_rounds}")
                    wait.network_update(msg["player_count"], finished_users, scores)
                    self.in_waiting_screen = True
                    self.show_screen("waiting")

            # ─── everybody finished the round ──────────────────────────────
            elif kind == "round_over":
                if msg.get("round") != self.current_round:
                    return

                wait = self.screens["waiting"]
                wait.title_text.config(text="Waiting for other players to finish...")

                final_users = msg.get("users", [])
                final_scores = msg.get("scores", {})

                wait.network_update(len(final_users), final_users, final_scores)
                self.in_waiting_screen = True
                self.show_screen("waiting")

        self.root.after(0, apply)

    def init_screens(self):
        """ Each screen is added to the container, and this GUI class is passed as the screen controller. """
        self.screens["menu"] = MenuScreen(self.container, self)
        self.screens["choose_name"] = ChooseNameScreen(self.container, self)
        self.screens["waiting"] = GeneralWaitingScreen(self.container, self)
        self.screens["gameplay_course_selection"] = CourseSelectionScreen(self.container, self)
        self.screens["gameplay_course_cart"] = CourseCartScreen(self.container, self)
        self.screens["game_over"] = GameOverScreen(self.container, self)

        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def show_screen(self, screen_name):
        """Bring an existing screen to the front."""
        # don't allow anything to replace the game over screen
        if self.game_has_ended and screen_name != "game_over":
            return

        screen = self.screens[screen_name]

        if screen_name == "gameplay_course_selection":
            screen.update_courses(self.current_round_courses or [])

        elif screen_name == "gameplay_course_cart":
            selected = self.screens["gameplay_course_selection"].selected_course.get()
            screen.update_cart(None if selected == "__NONE__" else selected)

        screen.tkraise()  # bring to front

    def next_round(self):
        # just send the player to the waiting screen; the server owns the count
        self.screens["waiting"].reset_screen()
        self.show_screen("waiting")

    def reset_game(self):
        self.current_round = 1
        self.screens["waiting"].reset_screen()
        self.screens["gameplay_course_selection"].update_courses([])
        self.screens["gameplay_course_cart"].update_cart(None)

        choose_name_screen = self.screens["choose_name"]
        choose_name_screen.textbox.delete('1.0', tk.END)
        choose_name_screen.local_username = None

    def on_closing(self):
        """Used both by closing main gui window, and quit option"""
        if messagebox.askyesno("Quit?", message="Are you sure you want to quit?"):
            self.root.destroy()

    def start_countdown(self, current_round):
        screen = None
        if current_round == 1:
            screen = self.screens["waiting"]
            screen.title_text.config(text="Waiting for other players to join...")
            screen.countdown_text1 = "Game"
            screen.countdown_text2 = "game"
        else:
            screen = self.screens["waiting"]
            screen.title_text.config(text="Waiting for other players to finish...")
            screen.countdown_text1 = "Next round"
            screen.countdown_text2 = "next round"

        # disable the back button once countdown starts so client does not end up in a broken state.
        # if the client backs out just before the server starts the countdown, the server will still
        # proceed with the countdown, and the game will continue with 3 players
        screen.back_button.config(state='disabled')

        screen.countdown_time = 3
        screen.countdown_active = True
        
        def update_countdown():
            if screen.countdown_active and screen.countdown_time > 0:
                screen.countdown_label.config(
                    text=f"{screen.countdown_text1} starting in {screen.countdown_time}..."
                )
                screen.countdown_time -= 1
                self.root.after(1000, update_countdown)  # 1000 ms
            elif screen.countdown_active:
                screen.countdown_label.config(text=f"Starting {screen.countdown_text2}!")

                # Delay between 50 and 400 ms delay between countdown and game start,
                # based on our location of vancouver and server in toronto.
                # This is to ensure fairness, so that network speed does not give an advantage or disadvantage.
                random_ms = random.randint(50, 400)

                self.root.after(random_ms, self.on_countdown_complete)
                
        update_countdown()
                
    def on_countdown_complete(self):
        self.show_screen("gameplay_course_selection")
        self.screens["gameplay_course_selection"].update_courses(
            self.current_round_courses
        )
        

class MenuScreen(tk.Frame):
    def __init__(self, parent, gui_controller):
        super().__init__(parent)
        self.gui_controller = gui_controller
        self.config(bg=utils.colours["background"])
        self.setup()

    def setup(self):
        title = tk.Label(self, text="ENROLMENT\nRUSH", font=('Arial', 48, 'bold'), fg=utils.colours["foreground"],
                         bg=utils.colours["background"])
        title.pack(padx=10, pady=10)

        subtitle = tk.Label(self, text="By Kazi, Colin, Jason, Cem", font=('Arial', 18, 'italic'),
                            fg=utils.colours["foreground"], bg=utils.colours["background"])
        subtitle.pack(padx=10, pady=10)

        start_button = tk.Button(self, text="START", font=('Arial', 32, 'bold', 'italic'), relief='flat', width=8,
                                 height=2, command=lambda: self.gui_controller.show_screen("choose_name"))
        start_button.pack(padx=10, pady=10)

        quit_button = tk.Button(self, text="QUIT", font=('Arial', 16, 'bold'), command=self.gui_controller.on_closing)
        quit_button.pack(padx=20, pady=20)


class ChooseNameScreen(tk.Frame):
    def __init__(self, parent, gui_controller):
        super().__init__(parent)
        self.local_username = None  # this will be the username for the specific client running this game
        self.textbox = None
        self.client_connection = None
        self.gui_controller = gui_controller
        self.config(bg=utils.colours["background"])
        self.setup()

    def setup(self):
        title = tk.Label(self, text="Enter your name", font=('Arial', 32, 'bold'), fg=utils.colours["foreground"],
                         bg=utils.colours["background"])
        title.pack(pady=(100, 10))

        self.textbox = tk.Text(self, height=1, font=('Arial', 20))
        self.textbox.pack(padx=200, pady=10)

        submit_button = tk.Button(self, text="SUBMIT", font=('Arial', 28, 'bold'), relief='flat',
                                  command=self.get_username)
        submit_button.pack(padx=10, pady=(10, 40))

        back_button = tk.Button(self, text="BACK", font=('Arial', 16, 'bold'), command=self.back_to_menu)
        back_button.pack(padx=20, pady=10)

        quit_button = tk.Button(self, text="QUIT", font=('Arial', 16, 'bold'), command=self.gui_controller.on_closing)
        quit_button.pack(padx=20, pady=10)

    def get_username(self):  # updated to strip and pass callback
        self.local_username = self.textbox.get('1.0', tk.END).strip()  # strip newline and whitespace
        print(f"[GUI] get_username -> {self.local_username!r}")  # debug
        self.gui_controller.local_username = self.local_username  # local username tracker
        
        # client-sided basic checks before we create a client
        if not self.local_username:
            messagebox.showerror(
                "Invalid Username",
                "Username cannot be empty."
            )
            return
        
        if len(self.local_username) > 16:
            messagebox.showerror(
                "Invalid Username",
                "Username must be 16 characters or fewer."
            )
            return

        waiting_screen = self.gui_controller.screens["waiting"]  # grab waiting screen
        waiting_screen.back_button.pack(padx=10, pady=20)  # ensure back button present
        waiting_screen.title_text.config(text="Waiting for other players to join...")

        def catch_duplicate_username():
            self.gui_controller.root.after(0, lambda: messagebox.showerror(
                "Username unavailable",
                "Username has already been taken"
            ))
            if self.client_connection:
                self.client_connection.disconnect()
                self.client_connection = None
                self.gui_controller.client_connection = None
            self.gui_controller.show_screen("choose_name")

        def catch_connection_error(err):  # Shows error if server isn't on
            print(f"Cannot establish connection with server! Check if the server is on.\nErr:{err}")
            self.gui_controller.root.after(0, lambda: messagebox.showerror(
                "Cannot establish connection with server",
                f"Please check if the server is running!\n{err}"
            ))

        def on_connection_success(established):  # If the json parses on the server, assume successful connection
            if established:
                print("Connection success")
                self.gui_controller.root.after(0, lambda: self.gui_controller.show_screen("waiting"))
            else:
                print("Connection not established")

        print(f"[GUI] waiting_screen.network_update = {waiting_screen.network_update}")  # debug

        self.client_connection = ClientConnection(  # keep reference so it isn't garbage-collected
            self.local_username,
            username_fail_callback=catch_duplicate_username,
            lobby_update_callback=waiting_screen.network_update,
            lobby_fail_callback=catch_connection_error,
            lobby_success_callback=on_connection_success,
            round_update_callback=self.gui_controller.on_round_message,
            seat_update_callback=self.gui_controller.on_seat_update,
            game_over_callback=self.gui_controller.on_game_over
        )
        self.gui_controller.client_connection = self.client_connection

        print("[GUI] ClientConnection created.")

    def back_to_menu(self):
        if self.client_connection:
            self.client_connection.disconnect()
            self.client_connection = None
        self.gui_controller.show_screen("menu")


class GeneralWaitingScreen(tk.Frame):
    """A base class used for waiting screens. There are two classes that extend this class:
    one for the beginning of the game (WaitingForPlayersScreen), and one for next rounds
    (WaitingForNextRoundScreen)."""
    def __init__(self, parent, gui_controller, title_text="Waiting...", waiting_type=0):
        super().__init__(parent)
        self.round_label = None
        self.players_frame = None
        self.countdown_label = None
        self.num_players_label = None
        self.back_button = None
        self.player_names = []
        self.num_finished = 0  # finished players reported by server
        self.player_name_labels = []
        self.gui_controller = gui_controller
        self.title_text = title_text
        self.countdown_time = 30  # seconds
        self.countdown_active = False
        self.config(bg=utils.colours["background"])
        self.waiting_type = waiting_type

        self.countdown_text1 = ""
        self.countdown_text2 = ""
        if waiting_type == 0:  # game
            self.countdown_text1 = "Game"
            self.countdown_text2 = "game"
        if waiting_type == 1:  # round
            self.countdown_text1 = "Next round"
            self.countdown_text2 = "next round"

        self.setup()

    # thread-safe lobby update method
    def network_update(self, player_count, users, scores=None):
        def apply():
            if self.gui_controller.game_has_ended:
                return
            print(f"[GUI] network_update invoked: {player_count} {users}")
            self.num_finished = player_count
            self.player_names = users.copy()
            self.update_player_display(scores)
        self.gui_controller.root.after(0, apply)  # marshal to main thread

    def setup(self):
        self.title_text = tk.Label(self, text="", font=('Arial', 36),
                                   fg=utils.colours["foreground"], bg=utils.colours["background"])
        self.title_text.pack(padx=10, pady=10)

        self.round_label = tk.Label(
            self,
            text=f"Round {self.gui_controller.current_round}/{self.gui_controller.max_rounds}",
            font=('Arial', 20),
            fg=utils.colours["foreground"],
            bg=utils.colours["background"]
        )
        self.round_label.pack(padx=10, pady=5)

        self.num_players_label = tk.Label(
            self,
            text=f"Players: {len(self.player_names)}/4",
            font=('Arial', 24),
            fg=utils.colours["foreground"],
            bg=utils.colours["background"]
        )
        self.num_players_label.pack(padx=10, pady=20)

        self.players_frame = tk.Frame(self, bg=utils.colours["background"], height=150)
        self.players_frame.pack(fill='both', expand=True, padx=20, pady=20)
        self.players_frame.pack_propagate(False)

        self.countdown_label = tk.Label(self, text="", font=('Arial', 32), fg="red",
                                        bg=utils.colours["background"])
        self.countdown_label.pack(padx=10, pady=30)

        button_frame = tk.Frame(self, bg=utils.colours["background"], height=150)
        button_frame.pack(side='bottom', expand=True, padx=20, pady=20)

        self.setup_buttons(button_frame)

    def setup_buttons(self, button_frame):
        self.back_button = tk.Button(button_frame, text="Back", font=('Arial', 16, 'bold'), relief='flat', width=14,
                                height=2, command=self.on_back_pressed)
        self.back_button.pack(padx=10, pady=20)

    def on_back_pressed(self):
        # Safely disconnect and delete client connection
        if self.gui_controller.client_connection:
            self.gui_controller.client_connection.disconnect()
            self.gui_controller.client_connection = None

        # Show the choose_name screen
        self.gui_controller.show_screen("choose_name")

    def update_player_display(self, scores=None):
        self.num_players_label.config(text=f"Players: {self.num_finished}/4")
        self.round_label.config(
            text=f"Round {self.gui_controller.current_round}/{self.gui_controller.max_rounds}"
        )

        for label in self.player_name_labels:
            label.destroy()
        self.player_name_labels.clear()

        local_username = self.gui_controller.local_username  # grab local name

        for name in self.player_names:
            player_frame = tk.Frame(self.players_frame, bg=utils.colours["background"])
            player_frame.pack(pady=2, anchor='center')

            if name == local_username:
                name_label = tk.Label(player_frame, text=name, font=('Arial', 18, 'bold'),
                                      fg=utils.colours["player_name_foreground"], bg=utils.colours["background"])
            else:
                name_label = tk.Label(player_frame, text=name, font=('Arial', 18, 'bold'),
                                      fg=utils.colours["foreground"], bg=utils.colours["background"])

            name_label.pack(side='left')

            # messagetype for joined depending on waitingtype
            if self.waiting_type == 0:
                joined_text = " joined."
            elif self.waiting_type == 1:
                joined_text = " is ready."

            joined_label = tk.Label(player_frame, text=joined_text, font=('Arial', 18, 'italic'),
                                    fg=utils.colours["foreground"], bg=utils.colours["background"])
            joined_label.pack(side='left')

            # points label with safe access
            if scores and name in scores:
                points_text = f" Points: {scores[name]}"
            elif self.waiting_type == 0:
                points_text = ""
            else:
                points_text = " Points: 0"

            points_label = tk.Label(player_frame, text=points_text, font=('Arial', 18),
                                    fg=utils.colours["foreground"], bg=utils.colours["background"])
            points_label.pack(side='left')

            # for cleanup - add both labels
            self.player_name_labels.extend([player_frame, name_label, joined_label, points_label])

    "Countdown logic moved to top-level GUI controller"
    def reset_screen(self, preserve_count=False):
        self.countdown_time = 3
        self.countdown_active = False

        # only clear counts and names if we are not preserving
        if not preserve_count:
            self.num_finished = 0
            self.player_names.clear()
            self.num_players_label.config(text=f"Players: {self.num_finished}/4")
            # clear the rendered list
            for label in self.player_name_labels:
                label.destroy()
            self.player_name_labels.clear()

        # always update round label and countdown text
        self.round_label.config(
            text=f"Round {self.gui_controller.current_round}/{self.gui_controller.max_rounds}"
        )
        self.countdown_label.config(text="")


class CourseSelectionScreen(tk.Frame):
    def __init__(self, parent, gui_controller):
        super().__init__(parent)
        self.courses_frame = None
        self.none_button = None
        self.selected_course = tk.StringVar()
        self.selected_course.set("")
        self.course_vars = {}
        self.check = None
        self.check_state = None
        self.gui_controller = gui_controller
        self.config(bg=utils.colours["background"])
        self.setup()

    def setup(self):
        title = tk.Label(self, text="Course selection", font=('Arial', 42, 'bold'), fg=utils.colours["foreground"],
                         bg=utils.colours["background"])
        title.pack(anchor='nw', padx=20, pady=10)

        main_frame = tk.Frame(self, bg=utils.colours["background"])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        self.courses_frame = tk.Frame(main_frame, bg=utils.colours["background"])
        self.courses_frame.pack(side='left', fill='both', expand=True)

        right_frame = tk.Frame(main_frame, bg=utils.colours["background"], width=250)
        right_frame.pack(side='right', fill='y', padx=(40, 0))
        right_frame.pack_propagate(False)

        add_to_cart_button = tk.Button(right_frame, text="Add to Course Cart", font=('Arial', 16, 'bold'),
                                       relief='flat', width=14, height=2, command=self.add_to_cart)
        add_to_cart_button.pack(side='bottom', padx=10, pady=10)

    def add_to_cart(self):
        if self.selected_course.get() in ("__NONE__", ""):
            tk.messagebox.showwarning("No Selection", "Please select a course before adding to cart.")
            self.gui_controller.root.focus_force()
        else:
            self.gui_controller.show_screen("gameplay_course_cart")

    def update_courses(self, course_list):
        # clear any existing widgets
        for w in self.courses_frame.winfo_children():
            w.destroy()
        self.course_vars.clear()
        self.selected_course.set("__NONE__")

        if not course_list:      # nothing to show yet
            return

        # build UI from the server’s list of dicts
        self.create_course_boxes(self.courses_frame, course_list)

    def update_course_display(self, code, seats_left):
        """Updates a course's seat count and disables it if full."""
        # check if we have stored widgets for this course
        course_widgets = self.course_vars.get(code)
        if not course_widgets:
            return

        # update the text of the seat count label
        seat_label = course_widgets['seat_label']
        seat_label.config(text=f"Seats available: {seats_left}")

        # disable the radio button if seats are zero
        if seats_left <= 0:
            button = course_widgets['button']
            button.config(state='disabled')

    def create_course_boxes(self, parent, course_list):
        # remove any old “none” radio button
        if hasattr(self, 'none_button') and self.none_button:
            self.none_button.destroy()

        # hidden radio for no selection
        self.none_button = tk.Radiobutton(
            parent,
            variable=self.selected_course,
            value="__NONE__",
            bg=utils.colours["background"]
        )
        self.none_button.pack_forget()
        self.selected_course.set("__NONE__")

        for c in course_list:
            code = c["code"]
            info = c

            # frame container
            frame = tk.Frame(parent, bg=utils.colours["course_container"], padx=20, pady=20)
            frame.pack(fill='x', pady=(0,15))

            # left: code + name
            left = tk.Frame(frame, bg=utils.colours["label_container"])
            left.pack(side='left', fill='both', expand=True)
            tk.Label(left, text=code, font=('Arial',16,'bold'), fg=utils.colours["course_text"],
                     bg=utils.colours["course_container"]
            ).pack(anchor='w')
            tk.Label(left, text=info["name"], font=('Arial',11), fg=utils.colours["course_text"],
                     bg=utils.colours["course_container"]).pack(anchor='w', pady=(2,0))

            # right: seats, radio, points
            right = tk.Frame(frame, bg=utils.colours["course_container"])
            right.pack(side='right', padx=(10,0))

            seat_label = tk.Label(right, text=f"Seats available: {info['available_seats']}", font=('Arial',12,'bold'),
                                  fg=utils.colours["course_text"], bg=utils.colours["course_container"])
            seat_label.pack(anchor='center')

            btn = tk.Radiobutton(
                right,
                variable=self.selected_course,
                value=code,
                bg=utils.colours["course_container"],
                activebackground=utils.colours["course_container"],
                selectcolor='white',
                font=('Arial',16),
                bd=2, highlightthickness=0,
                command=lambda name=code: self.on_course_select(name)
            )

            # if seats = 0, make button disabled state from the start
            if info['available_seats'] <= 0:
                btn.config(state='disabled')

            btn.pack(anchor='center', pady=2)

            tk.Label(right, text=f"Points: {info['points']}", font=('Arial',10,'bold'), fg=utils.colours["course_text"],
                     bg=utils.colours["course_container"]).pack(anchor='center')

            # store button and seat label for access later
            self.course_vars[code] = {'button': btn, 'seat_label': seat_label}

    def on_course_select(self, course_code):
        pass


class CourseCartScreen(tk.Frame):
    def __init__(self, parent, gui_controller):
        super().__init__(parent)
        self.courses_frame = None
        self.gui_controller = gui_controller
        self.course_code = None
        self.config(bg=utils.colours["background"])
        self.setup()

    def setup(self):
        title = tk.Label(self, text="Course Cart", font=('Arial', 42, 'bold'), fg=utils.colours["foreground"],
                         bg=utils.colours["background"])
        title.pack(anchor='nw', padx=20, pady=10)

        main_frame = tk.Frame(self, bg=utils.colours["background"])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        button_frame = tk.Frame(main_frame, bg=utils.colours["background"])
        button_frame.pack(side='bottom', fill='x', pady=(20, 0))

        self.courses_frame = tk.Frame(main_frame, bg=utils.colours["background"])
        self.courses_frame.pack(side='left', fill='both', expand=True)

        right_frame = tk.Frame(main_frame, bg=utils.colours["background"], width=250)
        right_frame.pack(side='right', fill='y', padx=(40, 0))
        right_frame.pack_propagate(False)

        back_button = tk.Button(button_frame, text="Back", font=('Arial', 16, 'bold'), relief='flat', width=14,
                                height=2, command=lambda: self.gui_controller.show_screen("gameplay_course_selection"))
        back_button.pack(side='left')

        enrol_button = tk.Button(button_frame, text="Finish Enrolling", font=('Arial', 16, 'bold'), relief='flat',
                                 width=14, height=2, command=self.enrol)
        enrol_button.pack(side='right')

    def enrol(self):
        if not self.course_code:
            return
        if not messagebox.askyesno("Confirm", f"Enrol in {self.course_code}?"):
            return

        # tell the server what we picked – the server will decide
        self.gui_controller.client_connection.send({"type": "select_course",
                                                    "course_code": self.course_code,
                                                    "username": self.gui_controller.local_username})

        # optimistic local feedback; the server will correct us if seat is gone
        messagebox.showinfo("Submitted", "Request sent. Waiting for other players…")

    def update_cart(self, course_code):
        """update the cart with the selected course"""
        self.course_code = course_code
        for widget in self.courses_frame.winfo_children():
            widget.destroy()
        self.populate_course_cart()

    def populate_course_cart(self):
        if self.course_code is not None:
            course_frame = tk.Frame(self.courses_frame, bg=utils.colours["course_container"], padx=20, pady=30)
            course_frame.pack(fill='x', pady=(0, 15))

            label_frame = tk.Frame(course_frame, bg=utils.colours["course_container"])
            label_frame.pack(side='left', fill='both', expand=True)

            code_label = tk.Label(label_frame, text=self.course_code, font=('Arial', 16, 'bold'),
                                  fg=utils.colours["course_text"], bg=utils.colours["course_container"])
            code_label.pack(anchor='w')

            value_label = tk.Label(label_frame, text=f"{utils.cmpt_courses[self.course_code]['name']}", font=('Arial', 11),
                                   fg=utils.colours["course_text"], bg=utils.colours["course_container"])
            value_label.pack(anchor='w', pady=(2, 0))
        else:
            no_course = tk.Label(self.courses_frame, text="No course selected.",font=('Arial', 24),
                                 fg=utils.colours["foreground"], bg=utils.colours["background"])
            no_course.pack(anchor='nw', padx=20, pady=10)


class GameOverScreen(tk.Frame):
    def __init__(self, parent, gui_controller):
        super().__init__(parent)
        self.gui_controller = gui_controller
        self.config(bg=utils.colours["background"])
        self.title_label = None
        self.players_frame = None
        self.player_name_labels = []
        self.setup()

    def setup(self):
        self.title_label = tk.Label(
            self,
            text="GAME OVER",
            font=('Arial', 48, 'bold'),
            fg=utils.colours["foreground"],
            bg=utils.colours["background"]
        )
        self.title_label.pack(padx=10, pady=50)

        self.players_frame = tk.Frame(self, bg=utils.colours["background"], height=150)
        self.players_frame.pack(fill='both', expand=True, padx=20, pady=20)
        self.players_frame.pack_propagate(False)

        exit_button = tk.Button(
            self,
            text="EXIT TO MENU",
            font=('Arial', 16, 'bold'),
            command=self.on_exit_to_menu
        )
        exit_button.pack(padx=20, pady=20)

    def update_game_over(self, winner, scores):
        self.title_label.config(text=f"{winner} Wins!")

        score_list = list(scores.items())

        # Sort by score desc; ensure winner appears on top for tie cases
        def sort_key(item):
            username, score = item
            is_not_winner = (username != winner)
            return (is_not_winner, -score)

        score_list.sort(key=sort_key)

        for username, score in score_list:
            frame = tk.Frame(self.players_frame, bg=utils.colours["background"])
            frame.pack(pady=2, anchor='center')

            if username == self.gui_controller.local_username:
                fg_colour = utils.colours["player_name_foreground"]
            else:
                fg_colour = utils.colours["foreground"]

            name_label = tk.Label(
                frame,
                text=username,
                font=('Arial', 18, 'bold'),
                fg=fg_colour,
                bg=utils.colours["background"]
            )
            name_label.pack(side='left')

            points_label = tk.Label(
                frame,
                text=f" Points: {score}",
                font=('Arial', 18),
                fg=utils.colours["foreground"],
                bg=utils.colours["background"]
            )
            points_label.pack(side='left')

            self.player_name_labels.extend([frame, name_label, points_label])

    def on_exit_to_menu(self):
        # client socket should already be closed by on_game_over, but be safe
        if self.gui_controller.client_connection:
            self.gui_controller.client_connection.disconnect()
            self.gui_controller.client_connection = None

        # allow navigation again (we block non-game-over screens while True)
        self.gui_controller.game_has_ended = False

        # reset local game state/UI for a fresh start
        self.gui_controller.reset_game()

        # Go back to main menu
        self.gui_controller.show_screen("menu")
"""Concourse

(C) Stratos Staboulis, 2020

"""
import argparse
import csv
import curses
from curses.textpad import Textbox
import json
import os
import time


# FIXME: Crashes if lines exceed window
# TODO: Refactor print function definition to one place
#       - Perhaps a generator function per print
# TODO: Add export results
# TODO: Add display shares function
# TODO: Add back to main menu function
# TODO: Check that shares sum up to 100%
# TODO: Tests: example json and csv input
#       should return same reasonable results
# NOTE: Rendering very big tables won't make the app crash but
#       will look weird due to the default line breaking


LOGO = [
    " ██ ▄█▀ ▒█████   ███▄    █  ██ ▄█▀ ██ ▄█▀▄▄▄      ",
    " ██▄█▒ ▒██▒  ██▒ ██ ▀█   █  ██▄█▒  ██▄█▒▒████▄    ",
    "▓███▄░ ▒██░  ██▒▓██  ▀█ ██▒▓███▄░ ▓███▄░▒██  ▀█▄  ",
    "▓██ █▄ ▒██   ██░▓██▒  ▐▌██▒▓██ █▄ ▓██ █▄░██▄▄▄▄██ ",
    "▒██▒ █▄░ ████▓▒░▒██░   ▓██░▒██▒ █▄▒██▒ █▄▓█   ▓██▒",
    "▒ ▒▒ ▓▒░ ▒░▒░▒░ ░ ▒░   ▒ ▒ ▒ ▒▒ ▓▒▒ ▒▒ ▓▒▒▒   ▓▒█░",
    "░ ░▒ ▒░  ░ ▒ ▒░ ░ ░░   ░ ▒░░ ░▒ ▒░░ ░▒ ▒░ ▒   ▒▒ ░",
    "░ ░░ ░ ░ ░ ░ ▒     ░   ░ ░ ░ ░░ ░ ░ ░░ ░  ░   ▒   ",
    "░  ░       ░ ░           ░ ░  ░   ░  ░        ░  ░",
]



#
# Generic tools and state management
#


def update_dict(x: dict, y: dict) -> dict:
    """Update the given (key, value) pairs

    """
    return {**x, **y}


def check_bill(bill):
    total_share = sum([v["share"] for (user, v) in bill.items()])
    assert abs(total_share - 1.0) < 1e-8, "Shares of must sum up to 1.0 for every bill."
    return bill


class State:
    """Program state manipulation

    """

    def __init__(self, users, bills, name=None, workspace=None):
        self.name = name
        self.workspace = workspace
        self.users = sorted(users, key=len)
        self.bills = {k: check_bill(v) for (k, v) in bills.items()}

    @property
    def filepath(self):
        return os.path.join(self.workspace, self.name + ".json")

    def save(self):
        """Save to the pre-defined file

        """
        with open(self.filepath, "w+") as f:
            json.dump(self.__dict__, f)

    @classmethod
    def load(cls, filepath):
        """Load state from a path

        """
        with open(filepath, "r") as f:
            raw = json.load(f)
        return cls(
            users=raw["users"],
            bills=raw["bills"],
            name=raw["name"],
            workspace=raw["workspace"]
        )

    def calculate_balance(self) -> dict:
        """Calculate total balance from all events

        """
        total = {
            bill_id: sum([
                v[u]["payment"] for u in self.users
            ]) for (bill_id, v) in self.bills.items()
        }
        return {
            u: sum([
                (
                    v[u]["payment"] -
                    v[u]["share"] * total[bill_id]
                ) for (bill_id, v) in self.bills.items()
            ]) for u in self.users
        }

    def calculate_flow(self):
        """Calculate suggested money flow

        The idea is to balance out with a minimal number of transactions.

        """

        flow = []
        balance = self.calculate_balance()
        while max(balance.values()) > 1e-6:
            u_min = min(balance, key=balance.get)
            u_max = max(balance, key=balance.get)
            payment = min(abs(balance[u_min]), abs(balance[u_max]))
            # Update balance with one more transaction
            balance = update_dict(
                balance,
                # Most indebted pays to most borrowed
                {
                    u_min: balance[u_min] + payment,
                    u_max: balance[u_max] - payment,
                }
            )
            flow += [(u_min, u_max, payment)]

        return flow


#
# CLI handling utils
#


def Parser():
    """Parser for CLI arguments

    File should be named "ProjectName.csv"

    """

    def convert_csv(filepath):
        name = os.path.basename(filepath).split(".")[0]
        workspace = os.path.dirname(filepath)

        with open(filepath, "r") as csvfile:
            rows = [
                row for row in csv.reader(csvfile, delimiter=",", quotechar="|")
            ]
            users = rows[0][1:]
            bills = {
                p_row[0]: {
                    u: {
                        "payment": float(p_row[j+1]),
                        "share": float(s_row[j+1]) / 100
                    } for (j, u) in enumerate(users)
                } for (p_row, s_row) in zip(rows[1::2], rows[2::2])
            }

        return State(
            users=users,
            bills=bills,
            name=name,
            workspace=workspace,
        )

    parser = argparse.ArgumentParser(
        description="Process concourse CL arguments"
    )
    parser.add_argument(
        "--book", "-b",
        default=None,
        help="path to CSV containing bill information",
        type=convert_csv
    )
    parser.add_argument(
        "--state", "-s",
        default=None,
        help="path to JSON state file",
        type=State.load
    )
    return parser


def cursor(func):
    """Decorator for turning cursor on

    """

    def decorated(*args, **kwargs):
        curses.curs_set(1)
        val = func(*args, **kwargs)
        curses.curs_set(0)
        return val

    return decorated


class Screen:

    def __init__(self, stdscr):
        self.stdscr = stdscr

    def clean_refresh(self, func):
        """Creates a decorator that resets screen

        """

        def decorated(*args, **kwargs):
            self.stdscr.clear()
            val = func(*args, **kwargs)
            self.stdscr.refresh()
            return val

        return decorated

    def create_color_setter(self, color):
        """Creates a color setter function

        """

        def color_setter(func):
            self.stdscr.attron(color)
            func()
            self.stdscr.attroff(color)

        return color_setter

    def center_x(self, s: str):
        """Horizontal center position for word

        """
        (h, w) = self.stdscr.getmaxyx()
        return int((w // 2) - (len(s) // 2) - len(s) % 2)

    def center_y(self, s: str):
        """Vertical center position for word

        """
        (h, w) = self.stdscr.getmaxyx()
        return int((h // 2) - 2)

    def render_title(self, text, color_pair, h0=0):
        """Render title with color

        """

        (h, w) = self.stdscr.getmaxyx()
        x = int((w // 4) - (len(text) // 4) - len(text) % 2)
        y = int((h // 2 + h0) - 2)

        self.stdscr.attron(color_pair)
        self.stdscr.attron(curses.A_BOLD)
        self.stdscr.addstr(y, x, text)
        self.stdscr.attroff(color_pair)
        self.stdscr.attroff(curses.A_BOLD)

        return (y, x)

    def render_menu(
            self,
            title: str,
            items: dict,
            color_pair,
            key_hook=lambda f: f(),
            h0=0
    ):
        """Render menu with title

        """

        # Render title
        (y, x) = self.render_title(
            text=title,
            color_pair=color_pair,
            h0=h0
        )
        render_key = lambda z, key: key_hook(
            lambda: self.stdscr.addstr(z, x, key)
        )
        render_value = lambda z, key, value: self.stdscr.addstr(
            z, x + len(key) + 1, value
        )

        # Render menu
        for (i, (key, value)) in enumerate(items.items()):
            render_key(y + 2 + i, key)
            render_value(y + 2 + i, key, value)

    def render_statusbar(self, text: str, color_pair):
        """Render status bar

        """
        (h, w) = self.stdscr.getmaxyx()
        self.stdscr.attron(color_pair)
        self.stdscr.addstr(h - 1, 0, text)
        self.stdscr.addstr(
            h - 1, len(text),
            " " * (w - len(text) - 1)
        )
        self.stdscr.attroff(color_pair)

    def user_input(
            self,
            y,
            x,
            descr,
            nlines=1,
            ncols=30,
            descr_hook=lambda f: f()
    ):
        """User input with description

        """
        descr_hook(lambda: self.stdscr.addstr(y, x, descr))
        editwin = curses.newwin(nlines, ncols, y + 1, x)
        self.stdscr.refresh()
        box = Textbox(editwin)
        box.edit()
        return box.gather().strip()  # NOTE: adds one space


def App(stdscr):

    # Curses initial definitions --------------------------------
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.curs_set(0)
    # -----------------------------------------------------------

    screen = Screen(stdscr)
    blue = screen.create_color_setter(curses.color_pair(5))
    green = screen.create_color_setter(curses.color_pair(4))
    user_input = lambda y, x, descr: screen.user_input(
        y, x, descr, ncols=50, descr_hook=green
    )
    title = lambda text, h0=0: screen.render_title(
        text="\u25c6 " + text + " \u25c6 ",
        color_pair=curses.color_pair(4),
        h0=h0
    )
    menu = lambda title, items, h0=0: screen.render_menu(
        title="\u25cf " + title + " \u25cf",
        items=items,
        color_pair=curses.color_pair(2),
        key_hook=blue,
        h0=h0
    )

    info_text = "Press any key to exit to project menu"
    user_input_text = (
        "<Enter> Send <Ctrl-d> Delete backwards <Ctrl-f/b> Move right/left"
    )

    def statusbar(text):
        """Helper decorator for invoking a statusbar with given text

        """

        def decorator(func):

            def decorated(*args, **kwargs):
                screen.render_statusbar(
                    text,
                    curses.color_pair(3)
                )
                return func(*args, **kwargs)

            return decorated

        return decorator

    #
    # Define features / pages ---------------------------
    #

    @screen.clean_refresh
    @statusbar(info_text)
    def display_balance(state):
        (y, x) = title("Balance")
        balance = state.calculate_balance()

        for (i, u) in enumerate(state.users):
            screen.stdscr.addstr(
                y + i + 2,
                x,
                u + ": " + str(round(balance[u], 2))
            )

        screen.stdscr.getch()
        return state

    @screen.clean_refresh
    @statusbar(info_text)
    def display_results(state):
        (y, x) = title("Results")
        flow = state.calculate_flow()

        for (i, (u_from, u_to, payment)) in enumerate(flow):
            screen.stdscr.addstr(
                y + i + 2,
                x,
                "{0} \u2bc8 {1} \u2bc8 {2}".format(
                    u_from, round(payment, 2), u_to
                )
            )

        screen.stdscr.getch()
        return state

    @screen.clean_refresh
    @statusbar(info_text)
    def display_bills(state):
        (y, x) = title("Current bills")
        row_format = "{:<12}" * (len(state.users) + 1)

        green(
            lambda: screen.stdscr.addstr(
                y + 2,
                x,
                row_format.format("", *state.users)
            )
        )
        for (i, (bill_id, v)) in enumerate(state.bills.items()):
            screen.stdscr.addstr(
                y + i + 3,
                x,
                row_format.format(bill_id, *[v[u]["payment"] for u in state.users])
            )

        screen.stdscr.getch()
        return state

    def save(state):
        state.save()
        screen.render_statusbar(
            "Saved as " + state.filepath, curses.color_pair(3)
        )
        screen.stdscr.refresh()
        time.sleep(1)
        return state

    @screen.clean_refresh
    @cursor
    @statusbar(user_input_text)
    def load():
        (y, x) = title("Load project")
        filepath = user_input(y + 2, x, "<Filepath> ")
        return State.load(filepath)

    @screen.clean_refresh
    @cursor
    @statusbar(user_input_text)
    def add_bill(state):
        (y, x) = title("Add bill")
        bill_id = user_input(y + 2, x, "<Identifier> ")
        equal = user_input(y + 4, x, "<Equal shares (y/n)> ")
        payments = {
            u: {
                "payment": float(
                    user_input(y + 6, x, "<{0} paid> ".format(u))
                ),
                "share": (
                    1.0 / len(state.users) if (
                        equal == "" or equal == "y"
                    ) else
                    0.01 * float(
                        user_input(
                            y + 8, x, "<{0}'s percentage> ".format(u)
                        )
                    )
                )
            } for (i, u) in enumerate(state.users)
        }
        bills = update_dict(
            state.bills,
            {bill_id: payments}
        )

        return State(
            users=state.users,
            bills=bills,
            name=state.name,
            workspace=state.workspace
        )

    @screen.clean_refresh
    @cursor
    @statusbar(user_input_text)
    def new_project():
        (y, x) = title("New project")
        name = user_input(y + 2, x, "<Project name> ")
        workspace = user_input(y + 4, x, "<Working directory> ")
        num = int(user_input(y + 6, x, "<Number of users> "))
        users = [
            user_input(
                y + 8, x, "<User #{0}> ".format(i + 1)
            ) for i in range(num)
        ]
        return State(
            users=users,
            bills={},
            name=name,
            workspace=workspace
        )


    @screen.clean_refresh
    @statusbar("Pressing other keys quits program")
    def project_menu(state):

        def event_loop(ch, state):
            return project_menu(
                add_bill(state)        if ch == ord("a") else
                display_bills(state)   if ch == ord("b") else
                display_balance(state) if ch == ord("c") else
                display_results(state) if ch == ord("r") else
                save(state)            if ch == ord("s") else
                quit()
            )

        menu(
            "Project menu",
            {
                "[a]": "Add bill",
                "[b]": "Display bills",
                "[c]": "Display balance",
                "[r]": "Display results",
                "[s]": "Save"
            }
        )

        return event_loop(screen.stdscr.getch(), state)

    @screen.clean_refresh
    @statusbar("Pressing other keys quits program")
    def main_menu():

        def event_loop(ch):
            return project_menu(
                new_project() if ch == ord("n") else
                load()        if ch == ord("l") else
                quit()
            )

        def render_logo():
            x = screen.center_x(LOGO[0])
            y = 2
            for (i, row) in enumerate(LOGO):
                screen.stdscr.addstr(i + y, x, row)

        green(render_logo)

        menu(
            "Main menu",
            {
                "[n]": "New project",
                "[l]": "Load project",
            }
        )

        return event_loop(screen.stdscr.getch())

    main_menu()

    return True


def main(state=None):
    """Main script

    """
    if state is None:
        try:
            # Calls App automatically with the stdscr argument
            exit_status = curses.wrapper(App)
        except KeyboardInterrupt:
            pass
        finally:
            print("\n".join([""] + LOGO + [""]))
    else:
        flow = state.calculate_flow()
        for (u_from, u_to, payment) in flow:
            print(
                "{0} \u2bc8 {1} \u2bc8 {2}".format(
                    u_from, round(payment, 2), u_to
                )
            )


if __name__ == "__main__":
    namespace = Parser().parse_args()
    main(
        namespace.book or namespace.state
    )

"""Concourse terminal application for sharing costs

"""
import curses
from curses.textpad import Textbox, rectangle
import json
import os


#
# Generic tools and state management
#


def update_dict(x: dict, y: dict) -> dict:
    """Update the given (key, value) pairs

    """
    return {**x, **y}


class State:
    """Program state manipulation

    """

    def __init__(self, name, workspace, users, bills):
        self.name = name
        self.workspace = workspace
        self.users = users
        self.bills = bills
        self.filepath = os.path.join(
            workspace, name + ".json"
        )

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
            name=raw["name"],
            workspace=raw["workspace"],
            users=raw["users"],
            bills=raw["bills"]
        )


def calculate_balance(state) -> dict:
    """Calculate total balance from all events

    """
    total = {
        bill_id: sum([
            v[u]["payment"] for u in state.users
        ]) for (bill_id, v) in state.bills.items()
    }
    return {
        u: sum([
            (
                v[u]["payment"] -
                v[u]["share"] * total[bill_id]
            ) for (bill_id, v) in state.bills.items()
        ]) for u in state.users
    }


def calculate_flow(state):
    """Calculate suggested money flow

    The idea is to balance out with a minimal number of transactions.

    """

    def deduce(b):
        # Most indebted pays to most borrowd
        u_min = min(b, key=b.get)
        u_max = max(b, key=b.get)
        payment = min(abs(b[u_min]), abs(b[u_max]))
        return (u_min, u_max, payment)

    def pay(b, u_from, u_to, payment):
        # Update balance with one transaction
        return update_dict(b, {
            u_from: b[u_from] + payment,
            u_to: b[u_to] - payment
        })

    def flowflow(b, flow: list=[]):
        # Balance out until everybody at zero
        tract = deduce(b)
        return (
            flowflow(pay(b, *tract), flow + [tract])
            if max(b.values()) > 1e-6 else
            flow
        )

    return flowflow(calculate_balance(state))


#
# CLI handling utils
#


def cursor(func):

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

        def decorated(*args, **kwargs):
            self.stdscr.clear()
            val = func(*args, **kwargs)
            self.stdscr.refresh()
            return val

        return decorated

    def create_color_setter(self, color):

        def color_setter(func):
            self.stdscr.attron(color)
            func()
            self.stdscr.attroff(color)

        return color_setter

    def render_title(self, text, color):
        # TODO: Rectangle around title

        (h, w) = self.stdscr.getmaxyx()
        x = int((w // 2) - (len(text) // 2) - len(text) % 2)
        y = int((h // 4) - 2)

        self.stdscr.attron(color)
        self.stdscr.attron(curses.A_BOLD)
        self.stdscr.addstr(y, x, text)
        self.stdscr.attroff(color)
        self.stdscr.attroff(curses.A_BOLD)

        return (y, x)

    def render_menu(
            self,
            title: str,
            items: tuple,
            color_pair=curses.color_pair(4)
    ):

        # Render title
        (y, x) = self.render_title(title, color_pair)
        render_item = lambda z, text: self.stdscr.addstr(z, x, text)

        # Render menu
        for (i, item) in enumerate(items):
            render_item(y + 2 + i, item)

    def render_statusbar(self, text: str, color_pair=curses.color_pair(3)):
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
            map_descr=lambda x: x
    ):
        map_descr(lambda: self.stdscr.addstr(y, x, descr))
        editwin = curses.newwin(nlines, ncols, y, x + len(descr))
        self.stdscr.refresh()
        box = Textbox(editwin)
        box.edit()
        return box.gather()


def run(stdscr):
    """Run the app

    NOTE: It makes sense to have define the actions outside of this script
          but main_menu and venture_menu here as they are app specific whereas
          the actions could be used anywhere. Also, then we don't need to
          pass the argument stdscr to all menu functions.

    TODO: Display tabular data

    """
    app = App(stdscr)

    # Initializations -------------------------------------------
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.curs_set(0)
    # -----------------------------------------------------------

    green = app.create_color_setter(curses.color_pair(4))

    @clean_refresh
    @cursor
    def add_bill(state):

        (y, x) = render_title("*** Add bill ***", curses.color_pair(2))
        render_statusbar("<C-G> Send <C-d> Delete <C-f/b> Move right/left")

        msg = user_input(y + 2, x, "Test insert> ")
        msg2 = user_input(y + 3, x, "Another thing> ")

    # @reset
    # def main_menu():

    #     def do(ch, state):
    #         return venture_menu(
    #             new_venture(stdscr) if ch == ord("n") else
    #             load(stdscr)        if ch == ord("l") else
    #             quit()              if ch == ord("q") else
    #             unknown(stdscr)
    #         )

    #     render_menu(stdscr, "Test", {})

    #     # TODO: Render a nice front title
    #     # TODO: Render the menu here
    #     # stdscr.addstr(0, 0, "Test", curses.color_pair(1))

    #     return do(stdscr.getch(), {})

    # @reset
    # def venture_menu(state):

    #     def do(ch, state):
    #         return venture_menu(
    #             add_bill(stdscr, state)        if ch == ord("a") else
    #             display_balance(stdscr, state) if ch == ord("b") else
    #             export_results(stdscr, state)  if ch == ord("e") else
    #             log_bills(stdscr, state)       if ch == ord("l") else
    #             display_results(stdscr, state) if ch == ord("r") else
    #             quit()                         if ch == ord("q") else
    #             save(stdscr, state)            if ch == ord("s") else
    #             unknown(stdscr, state)
    #         )

    #     # TODO: Render stuff here

    #     return do(stdscr.getch(), state)

    # main_menu()

    @clean_refresh
    def test():
        render_menu(
            "*** Main menu ***",
            (
                "[q] Quit",
                "[h] Help"
            )
        )
        render_statusbar("(C) Greeks of Malmi, 2020")
        # stdscr.getstr(10, 0, 10)  # get chars
        add_bill(None)
        k = stdscr.getch()
        if k == ord("q"):
            quit()

    test()


def main():
    """Main loop

    """
    curses.wrapper(run)


if __name__ == "__main__":
    main()

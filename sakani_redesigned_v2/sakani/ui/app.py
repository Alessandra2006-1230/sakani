"""Main application window, authentication switching and page navigation."""

import tkinter as tk

from config import APP_NAME, COLORS, WINDOW_MIN, WINDOW_SIZE
from ui import theme
from ui.add_transaction_page import AddTransactionPage
from ui.budget_page import BudgetPage
from ui.cycles_page import CyclesPage
from ui.dashboard_page import DashboardPage
from ui.history_page import HistoryPage
from ui.login_page import LoginPage
from ui.sidebar import Sidebar
from ui.signup_page import SignupPage
from ui.summary_page import SummaryPage

PAGE_CLASSES = {
    "dashboard": DashboardPage,
    "add": AddTransactionPage,
    "history": HistoryPage,
    "summary": SummaryPage,
    "cycles": CyclesPage,
    "budgets": BudgetPage,
}


class MainLayout(tk.Frame):
    """Sidebar plus a content area that swaps between the four pages."""

    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["background"])
        self.app = app
        self.sidebar = Sidebar(self, app)
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(self, bg=COLORS["background"])
        self.content.pack(side="left", fill="both", expand=True)

        self.pages = {}
        self.current = None

    def show(self, name):
        """Show one page, creating it the first time it is opened."""
        if name not in PAGE_CLASSES:
            return
        if self.current is not None:
            self.current.pack_forget()
        page = self.pages.get(name)
        if page is None:
            page = PAGE_CLASSES[name](self.content, self.app)
            self.pages[name] = page
        page.pack(fill="both", expand=True)
        if hasattr(page, "refresh"):
            page.refresh()
        self.current = page
        self.sidebar.set_active(name)


class SakaniApp(tk.Tk):
    """The main Tkinter window for Sakani."""

    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.minsize(*WINDOW_MIN)
        self.configure(bg=COLORS["background"])
        theme.setup_theme(self)
        self._center_window()

        self.current_user = None
        self.main_layout = None
        self.container = tk.Frame(self, bg=COLORS["background"])
        self.container.pack(fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.show_login()

    def _center_window(self):
        """Place the window in the middle of the screen."""
        try:
            width, height = (int(part) for part in WINDOW_SIZE.split("x"))
        except ValueError:
            width, height = 1100, 700
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry("%dx%d+%d+%d" % (width, height, x, y))

    def _clear(self):
        """Destroy every child of the container and reset layout state."""
        for child in self.container.winfo_children():
            child.destroy()
        self.main_layout = None

    def show_login(self):
        """Show the login page."""
        self.current_user = None
        self._clear()
        page = LoginPage(self.container, self)
        page.pack(fill="both", expand=True)
        page.refresh()

    def show_signup(self):
        """Show the sign-up page."""
        self._clear()
        page = SignupPage(self.container, self)
        page.pack(fill="both", expand=True)
        page.refresh()

    def login_success(self, user):
        """Store the logged-in user and open the main layout."""
        self.current_user = user
        self._clear()
        self.main_layout = MainLayout(self.container, self)
        self.main_layout.pack(fill="both", expand=True)
        self.open_page("dashboard")

    def open_page(self, name):
        """Navigate to a main page by name."""
        if self.main_layout is not None:
            self.main_layout.show(name)

    def logout(self):
        """Return to the login screen and forget the current user."""
        self.show_login()

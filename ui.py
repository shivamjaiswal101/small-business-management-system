"""Polished Tkinter interface for the local Business Manager application."""

import calendar as calendar_module
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import business
import reports
import services
import transactions


NAVY = "#111B2E"
NAVY_LIGHT = "#1C2A42"
INK = "#1D2939"
MUTED = "#748198"
ACCENT = "#536DFE"
ACCENT_DARK = "#4058E8"
MINT = "#26B893"
BG = "#F3F5F9"
WHITE = "#FFFFFF"
LINE = "#E5E9F0"


def _money(amount_minor: int) -> str:
    return f"₹{Decimal(amount_minor) / 100:,.2f}"


def _display_time(iso_timestamp: str) -> str:
    value = datetime.fromisoformat(iso_timestamp)
    return value.astimezone().strftime("%d %b %Y  •  %H:%M")


class DatePicker:
    """Small month calendar used by the report and overview date controls."""

    def __init__(self, parent, initial_date: str, on_select):
        try:
            self.selected = date.fromisoformat(initial_date)
        except ValueError:
            self.selected = date.today()
        self.month = self.selected.replace(day=1)
        self.on_select = on_select
        self.window = tk.Toplevel(parent)
        self.window.title("Choose a date")
        self.window.resizable(False, False)
        self.window.configure(bg=WHITE)
        self.window.transient(parent)
        self.window.bind("<Escape>", lambda _event: self.window.destroy())

        header = tk.Frame(self.window, bg=WHITE, padx=12, pady=12)
        header.pack(fill="x")
        self._nav_button(header, "‹", -1).pack(side="left")
        self.month_button = tk.Button(header, command=self.show_months, bg=WHITE, fg=INK,
                                      activebackground="#EEF1F6", relief="flat", bd=0,
                                      cursor="hand2", font=("Segoe UI Semibold", 11))
        self.month_button.pack(side="left", expand=True)
        self.year_button = tk.Button(header, command=self.show_years, bg=WHITE, fg=ACCENT,
                                     activebackground="#EEF1F6", relief="flat", bd=0,
                                     cursor="hand2", font=("Segoe UI Semibold", 11))
        self.year_button.pack(side="left", padx=(3, 0))
        self._nav_button(header, "›", 1).pack(side="right")
        self.grid = tk.Frame(self.window, bg=WHITE, padx=12)
        self.grid.pack(pady=(0, 12))
        self.draw_month()
        self.window.update_idletasks()
        x = max(0, parent.winfo_rootx() + (parent.winfo_width() - self.window.winfo_width()) // 2)
        y = max(0, parent.winfo_rooty() + (parent.winfo_height() - self.window.winfo_height()) // 2)
        self.window.geometry(f"+{x}+{y}")
        self.window.grab_set()

    def _nav_button(self, parent, text, offset):
        return tk.Button(parent, text=text, width=3, command=lambda: self.navigate(offset),
                         bg=WHITE, fg=INK, activebackground="#EEF1F6", relief="flat",
                         bd=0, cursor="hand2", font=("Segoe UI Semibold", 12))

    def navigate(self, offset):
        if self.mode == "years":
            self.year_decade += offset * 10
            self.draw_years()
        elif self.mode == "months":
            self.month = date(self.month.year + offset, self.month.month, 1)
            self.draw_months()
        else:
            month_index = self.month.month - 1 + offset
            year = self.month.year + month_index // 12
            month = month_index % 12 + 1
            self.month = date(year, month, 1)
            self.draw_month()

    def clear_grid(self):
        for child in self.grid.winfo_children():
            child.destroy()

    def draw_month(self):
        self.mode = "days"
        self.clear_grid()
        self.month_button.configure(text=self.month.strftime("%B"))
        self.year_button.configure(text=str(self.month.year))
        for column, day_name in enumerate(("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")):
            tk.Label(self.grid, text=day_name, width=4, bg=WHITE, fg=MUTED,
                     font=("Segoe UI Semibold", 8)).grid(row=0, column=column, pady=(0, 5))
        self.day_buttons = {}
        for row_index, week in enumerate(calendar_module.monthcalendar(self.month.year, self.month.month), start=1):
            for column, day_number in enumerate(week):
                if not day_number:
                    tk.Label(self.grid, text="", width=4, bg=WHITE).grid(row=row_index, column=column, pady=2)
                    continue
                chosen = date(self.month.year, self.month.month, day_number)
                active = chosen == self.selected
                color = ACCENT if active else WHITE
                foreground = WHITE if active else INK
                button = tk.Button(
                    self.grid, text=str(day_number), width=4, relief="flat", bd=0,
                    bg=color, fg=foreground, activebackground="#E9EDFF",
                    activeforeground=INK, cursor="hand2", font=("Segoe UI", 9),
                    command=lambda value=chosen: self.choose(value),
                )
                button.grid(row=row_index, column=column, pady=2, ipady=4)
                self.day_buttons[day_number] = button

    def show_months(self):
        self.mode = "months"
        self.clear_grid()
        self.month_button.configure(text="Choose month")
        self.year_button.configure(text=str(self.month.year))
        self.month_buttons = {}
        for month_number in range(1, 13):
            name = calendar_module.month_name[month_number]
            button = tk.Button(
                self.grid, text=name, width=11, relief="flat", bd=0,
                bg=ACCENT if month_number == self.month.month else WHITE,
                fg=WHITE if month_number == self.month.month else INK,
                activebackground="#E9EDFF", activeforeground=INK, cursor="hand2",
                font=("Segoe UI", 9), command=lambda value=month_number: self.choose_month(value),
            )
            button.grid(row=(month_number - 1) // 3, column=(month_number - 1) % 3,
                        padx=3, pady=4, ipady=7)
            self.month_buttons[month_number] = button

    def choose_month(self, month_number):
        self.month = date(self.month.year, month_number, 1)
        self.draw_month()

    def show_years(self):
        self.mode = "years"
        self.year_decade = (self.month.year // 10) * 10
        self.draw_years()

    def draw_years(self):
        self.mode = "years"
        self.clear_grid()
        first_year = self.year_decade
        self.month_button.configure(text=self.month.strftime("%B"))
        self.year_button.configure(text=f"{first_year}–{first_year + 9}")
        self.year_buttons = {}
        for offset in range(10):
            year = first_year + offset
            button = tk.Button(
                self.grid, text=str(year), width=8, relief="flat", bd=0,
                bg=ACCENT if year == self.month.year else WHITE,
                fg=WHITE if year == self.month.year else INK,
                activebackground="#E9EDFF", activeforeground=INK, cursor="hand2",
                font=("Segoe UI", 9), command=lambda value=year: self.choose_year(value),
            )
            button.grid(row=offset // 5, column=offset % 5, padx=3, pady=5, ipady=7)
            self.year_buttons[year] = button

    def choose_year(self, year):
        self.month = date(year, self.month.month, 1)
        self.draw_month()

    def choose(self, value):
        self.on_select(value.isoformat())
        self.window.destroy()


class SetupWindow:
    """First-run setup view."""

    def __init__(self, root: tk.Tk, on_complete):
        self.root = root
        self.on_complete = on_complete
        self.service_names: list[str] = []
        root.title("Business Manager — Welcome")
        root.geometry("1040x720")
        root.minsize(900, 640)
        root.configure(bg=BG)

        shell = tk.Frame(root, bg=BG)
        shell.pack(fill="both", expand=True)
        brand = tk.Frame(shell, bg=NAVY, width=330)
        brand.pack(side="left", fill="y")
        brand.pack_propagate(False)
        logo = tk.Label(brand, text="B", bg=ACCENT, fg=WHITE,
                        font=("Segoe UI Semibold", 19), width=2, height=1)
        logo.pack(anchor="w", padx=36, pady=(42, 16))
        tk.Label(brand, text="BUSINESS MANAGER", bg=NAVY, fg=WHITE,
                 font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=36)
        tk.Label(brand, text="A calmer way to run\nyour business.", bg=NAVY,
                 fg="#E8ECF5", justify="left", font=("Segoe UI Semibold", 25),
                 wraplength=250).pack(anchor="w", padx=36, pady=(76, 12))
        tk.Label(brand, text="Your services, transactions and daily\nfigures — all in one clear workspace.",
                 bg=NAVY, fg="#A8B5C8", justify="left", font=("Segoe UI", 11),
                 wraplength=250).pack(anchor="w", padx=36)
        tk.Label(brand, text="VERSION 2  ·  PRIVATE LOCAL WORKSPACE", bg=NAVY,
                 fg="#8292AA", font=("Segoe UI Semibold", 8)).pack(side="bottom", anchor="w", padx=36, pady=32)

        content = tk.Frame(shell, bg=BG, padx=58, pady=38)
        content.pack(side="left", fill="both", expand=True)
        tk.Label(content, text="Let's get you set up", bg=BG, fg=INK,
                 font=("Segoe UI Semibold", 26)).pack(anchor="w", pady=(8, 6))
        tk.Label(content, text="Start with your business name and the services you offer.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 28))
        tk.Label(content, text="BUSINESS NAME", bg=BG, fg="#475467",
                 font=("Segoe UI Semibold", 9)).pack(anchor="w", pady=(0, 7))
        self.business_entry = self._entry(content)
        self.business_entry.pack(fill="x", ipady=11, pady=(0, 20))
        tk.Label(content, text="YOUR SERVICES", bg=BG, fg="#475467",
                 font=("Segoe UI Semibold", 9)).pack(anchor="w", pady=(0, 7))
        service_row = tk.Frame(content, bg=BG)
        service_row.pack(fill="x")
        self.service_entry = self._entry(service_row)
        self.service_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self._button(service_row, "Add service", self._add_service, primary=False).pack(side="left", padx=(9, 0), ipady=7)
        list_card = tk.Frame(content, bg=WHITE, highlightbackground=LINE, highlightthickness=1)
        list_card.pack(fill="both", expand=True, pady=(14, 9))
        self.service_list = tk.Listbox(list_card, height=9, font=("Segoe UI", 10),
                                       relief="flat", bd=0, activestyle="none",
                                       bg=WHITE, fg=INK, selectbackground="#E9EDFF",
                                       selectforeground=INK, highlightthickness=0)
        self.service_list.pack(fill="both", expand=True, padx=12, pady=12)
        self._button(content, "Remove selected", self._remove_service, primary=False).pack(anchor="w")
        self._button(content, "Create workspace  →", self._save).pack(fill="x", pady=(22, 0), ipady=8)
        self.service_entry.bind("<Return>", lambda _event: self._add_service())
        self.business_entry.focus_set()

    @staticmethod
    def _entry(parent):
        return tk.Entry(parent, bg=WHITE, fg=INK, insertbackground=ACCENT,
                        relief="flat", bd=0, highlightthickness=1,
                        highlightbackground=LINE, highlightcolor=ACCENT,
                        font=("Segoe UI", 11))

    @staticmethod
    def _button(parent, text, command, primary=True):
        return tk.Button(parent, text=text, command=command, cursor="hand2",
                         bg=ACCENT if primary else WHITE,
                         activebackground=ACCENT_DARK if primary else "#F2F4F7",
                         fg=WHITE if primary else INK, activeforeground=WHITE if primary else INK,
                         relief="flat", bd=0, padx=16, pady=9,
                         font=("Segoe UI Semibold", 9), highlightthickness=1 if not primary else 0,
                         highlightbackground=LINE)

    def _add_service(self):
        value = self.service_entry.get().strip()
        if not value:
            return
        if any(name.casefold() == value.casefold() for name in self.service_names):
            messagebox.showerror("Duplicate service", "That service is already in the list.", parent=self.root)
            return
        self.service_names.append(value)
        self.service_list.insert("end", value)
        self.service_entry.delete(0, "end")
        self.service_entry.focus_set()

    def _remove_service(self):
        selection = self.service_list.curselection()
        if selection:
            index = selection[0]
            self.service_list.delete(index)
            self.service_names.pop(index)

    def _save(self):
        try:
            result = business.configure_business(self.business_entry.get(), self.service_names)
        except ValueError as error:
            messagebox.showerror("Setup incomplete", str(error), parent=self.root)
            return
        self.on_complete(result)


class BusinessManagerApp:
    PAGE_INFO = {
        "dashboard": ("Overview", "A clear picture of your selected day"),
        "services": ("Services", "Manage the work your business offers"),
        "reports": ("Reports", "Understand revenue across any date range"),
        "settings": ("Settings", "Your business workspace preferences"),
    }

    def __init__(self, root: tk.Tk, configured_business: dict):
        self.root = root
        self.business = configured_business
        self.last_report: dict | None = None
        self.dashboard_date = date.today()
        self.page_frames = {}
        self.nav_buttons = {}
        root.title("Business Manager")
        root.geometry("1320x850")
        root.minsize(1080, 700)
        root.configure(bg=BG)
        self._configure_tree_style()
        self._build_shell()
        self.refresh_dashboard()
        self.refresh_services()
        self.load_report(show_error=False)
        self.show_page("dashboard")

    def _configure_tree_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Premium.Treeview", background=WHITE, fieldbackground=WHITE,
                        foreground=INK, rowheight=38, borderwidth=0,
                        font=("Segoe UI", 9))
        style.configure("Premium.Treeview.Heading", background="#F7F8FB", foreground=MUTED,
                        font=("Segoe UI Semibold", 9), relief="flat", padding=(12, 11))
        style.map("Premium.Treeview", background=[("selected", "#E8EDFF")],
                  foreground=[("selected", INK)])

    def _build_shell(self):
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(shell, bg=NAVY, width=236)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        main = tk.Frame(shell, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        brand_row = tk.Frame(self.sidebar, bg=NAVY)
        brand_row.pack(fill="x", padx=22, pady=(27, 28))
        tk.Label(brand_row, text="B", bg=ACCENT, fg=WHITE, width=2, height=1,
                 font=("Segoe UI Semibold", 16)).pack(side="left")
        brand_text = tk.Frame(brand_row, bg=NAVY)
        brand_text.pack(side="left", padx=(10, 0))
        tk.Label(brand_text, text="BUSINESS", bg=NAVY, fg=WHITE,
                 font=("Segoe UI Semibold", 10)).pack(anchor="w")
        tk.Label(brand_text, text="MANAGER", bg=NAVY, fg="#94A3B8",
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(1, 0))

        tk.Label(self.sidebar, text="WORKSPACE", bg=NAVY, fg="#6E7F98",
                 font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=25, pady=(0, 9))
        for key, label in (("dashboard", "Overview"), ("services", "Services"), ("reports", "Reports")):
            button = tk.Button(self.sidebar, text=f"  {label}", command=lambda page=key: self.show_page(page),
                               anchor="w", cursor="hand2", relief="flat", bd=0,
                               bg=NAVY, fg="#BCC7D7", activebackground=NAVY_LIGHT,
                               activeforeground=WHITE, padx=14, pady=12,
                               font=("Segoe UI Semibold", 10), highlightthickness=0)
            button.pack(fill="x", padx=13, pady=2)
            self.nav_buttons[key] = button
        tk.Label(self.sidebar, text="PREFERENCES", bg=NAVY, fg="#6E7F98",
                 font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=25, pady=(24, 9))
        button = tk.Button(self.sidebar, text="  Settings", command=lambda: self.show_page("settings"),
                           anchor="w", cursor="hand2", relief="flat", bd=0,
                           bg=NAVY, fg="#BCC7D7", activebackground=NAVY_LIGHT,
                           activeforeground=WHITE, padx=14, pady=12,
                           font=("Segoe UI Semibold", 10), highlightthickness=0)
        button.pack(fill="x", padx=13, pady=2)
        self.nav_buttons["settings"] = button

        profile = tk.Frame(self.sidebar, bg=NAVY_LIGHT, padx=12, pady=12)
        profile.pack(side="bottom", fill="x", padx=14, pady=(0, 16))
        tk.Label(profile, text="ACTIVE BUSINESS", bg=NAVY_LIGHT, fg="#91A0B5",
                 font=("Segoe UI Semibold", 7)).pack(anchor="w")
        self.sidebar_business = tk.Label(profile, text=self.business["name"], bg=NAVY_LIGHT,
                                         fg=WHITE, font=("Segoe UI Semibold", 10),
                                         wraplength=180, justify="left")
        self.sidebar_business.pack(anchor="w", pady=(5, 7))
        tk.Label(profile, text="●  LOCAL WORKSPACE", bg=NAVY_LIGHT, fg="#73D8B9",
                 font=("Segoe UI Semibold", 7)).pack(anchor="w")
        tk.Label(self.sidebar, text="VERSION 2.0", bg=NAVY, fg="#728199",
                 font=("Segoe UI Semibold", 8)).pack(side="bottom", anchor="w", padx=25, pady=(0, 12))

        header = tk.Frame(main, bg=WHITE, height=104, highlightbackground=LINE, highlightthickness=1)
        header.pack(fill="x")
        header.pack_propagate(False)
        heading = tk.Frame(header, bg=WHITE)
        heading.pack(side="left", fill="y", padx=30, pady=18)
        self.page_title = tk.Label(heading, text="Overview", bg=WHITE, fg=INK,
                                   font=("Segoe UI Semibold", 21))
        self.page_title.pack(anchor="w")
        self.page_subtitle = tk.Label(heading, text="", bg=WHITE, fg=MUTED,
                                      font=("Segoe UI", 9))
        self.page_subtitle.pack(anchor="w", pady=(3, 0))
        actions = tk.Frame(header, bg=WHITE)
        actions.pack(side="right", padx=28)
        tk.Label(actions, text=f"{date.today().strftime('%A, %d %B %Y')}", bg=WHITE,
                 fg=MUTED, font=("Segoe UI", 9)).pack(side="left", padx=(0, 14))
        self._button(actions, "＋  New transaction", self.start_transaction).pack(side="left", ipady=4)
        self.page_host = tk.Frame(main, bg=BG)
        self.page_host.pack(fill="both", expand=True, padx=26, pady=24)

        for key, builder in (("dashboard", self._build_dashboard),
                             ("services", self._build_services),
                             ("reports", self._build_reports),
                             ("settings", self._build_settings)):
            frame = tk.Frame(self.page_host, bg=BG)
            self.page_frames[key] = frame
            builder(frame)

    @staticmethod
    def _button(parent, text, command, primary=True):
        return tk.Button(parent, text=text, command=command, cursor="hand2",
                         bg=ACCENT if primary else WHITE,
                         activebackground=ACCENT_DARK if primary else "#F2F4F7",
                         fg=WHITE if primary else INK, activeforeground=WHITE if primary else INK,
                         relief="flat", bd=0, padx=16, pady=10,
                         font=("Segoe UI Semibold", 9), highlightthickness=1 if not primary else 0,
                         highlightbackground=LINE)

    @staticmethod
    def _entry(parent, width=None):
        return tk.Entry(parent, width=width, bg=WHITE, fg=INK, insertbackground=ACCENT,
                        relief="flat", bd=0, highlightthickness=1,
                        highlightbackground=LINE, highlightcolor=ACCENT,
                        font=("Segoe UI", 10))

    @staticmethod
    def _card(parent, padx=18, pady=16):
        return tk.Frame(parent, bg=WHITE, padx=padx, pady=pady,
                        highlightbackground=LINE, highlightthickness=1)

    def _section_heading(self, parent, title, detail=None):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=(0, 13))
        tk.Label(row, text=title, bg=BG, fg=INK,
                 font=("Segoe UI Semibold", 14)).pack(side="left")
        if detail:
            tk.Label(row, text=detail, bg=BG, fg=MUTED,
                     font=("Segoe UI", 9)).pack(side="right")
        return row

    def _metric_cards(self, parent, metrics):
        strip = tk.Frame(parent, bg=BG)
        strip.value_labels = []
        strip.pack(fill="x", pady=(0, 20))
        for index, (label, value, hint, accent) in enumerate(metrics):
            strip.grid_columnconfigure(index, weight=1, uniform="metrics")
            card = self._card(strip, padx=17, pady=16)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0 if index == len(metrics) - 1 else 8))
            top = tk.Frame(card, bg=WHITE)
            top.pack(fill="x")
            tk.Label(top, text=label.upper(), bg=WHITE, fg=MUTED,
                     font=("Segoe UI Semibold", 8)).pack(side="left")
            tk.Label(top, text="●", bg=WHITE, fg=accent,
                     font=("Segoe UI", 10)).pack(side="right")
            value_label = tk.Label(card, text=value, bg=WHITE, fg=INK,
                                   font=("Segoe UI Semibold", 22))
            value_label.pack(anchor="w", pady=(13, 2))
            strip.value_labels.append(value_label)
            tk.Label(card, text=hint, bg=WHITE, fg=MUTED,
                     font=("Segoe UI", 8)).pack(anchor="w")
        return strip

    def _build_dashboard(self, page):
        heading = self._section_heading(page, "Performance for selected day")
        tk.Label(heading, text="DATE", bg=BG, fg=MUTED,
                 font=("Segoe UI Semibold", 8)).pack(side="right", padx=(8, 0))
        self.dashboard_date_entry = self._entry(heading, width=13)
        self.dashboard_date_entry.insert(0, self.dashboard_date.isoformat())
        self._make_date_field(self.dashboard_date_entry, self.select_dashboard_date)
        self.dashboard_date_entry.pack(side="right", ipady=7)
        self.dashboard_metrics = self._metric_cards(page, [
            ("Revenue", "₹0.00", "Selected day total", ACCENT),
            ("Transactions", "0", "On selected day", MINT),
            ("Cash", "₹0.00", "Cash payments", "#D89B31"),
            ("Online", "₹0.00", "Online payments", "#59A6D8"),
        ])
        card = self._card(page, padx=0, pady=0)
        card.pack(fill="both", expand=True)
        toolbar = tk.Frame(card, bg=WHITE, padx=18, pady=15)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text="Recent transactions", bg=WHITE, fg=INK,
                 font=("Segoe UI Semibold", 12)).pack(side="left")
        tk.Label(toolbar, text="Search selected day", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="right", padx=(8, 0))
        self.search_entry = self._entry(toolbar, width=28)
        self.search_entry.pack(side="right", ipady=8, padx=(14, 0))
        self.search_entry.bind("<Return>", lambda _event: self.refresh_dashboard())
        self._button(toolbar, "Search", self.refresh_dashboard, primary=False).pack(side="right", ipady=3)
        table_holder = tk.Frame(card, bg=WHITE)
        table_holder.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.dashboard_tree = self._tree(
            table_holder,
            ("id", "service", "amount", "payment", "created"),
            ("Transaction ID", "Service", "Amount", "Payment", "Date & time"),
            (220, 190, 135, 125, 205),
        )

    def _build_services(self, page):
        top = self._section_heading(page, "Your service catalog", "Active services are available when recording a transaction")
        self._button(top, "＋  Add service", self.add_service).pack(side="right", ipady=4)
        card = self._card(page, padx=0, pady=0)
        card.pack(fill="both", expand=True)
        toolbar = tk.Frame(card, bg=WHITE, padx=18, pady=15)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text="Services", bg=WHITE, fg=INK,
                 font=("Segoe UI Semibold", 12)).pack(side="left")
        for label, command in (("Edit", self.edit_service), ("Activate / deactivate", self.toggle_service)):
            self._button(toolbar, label, command, primary=False).pack(side="right", padx=(8, 0), ipady=4)
        table_holder = tk.Frame(card, bg=WHITE)
        table_holder.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.services_tree = self._tree(table_holder, ("id", "name", "status"),
                                        ("ID", "Service name", "Status"), (100, 550, 170))

    def _build_reports(self, page):
        self._section_heading(page, "Revenue report", "Choose a period to see your business performance")
        filter_card = self._card(page, padx=18, pady=14)
        filter_card.pack(fill="x", pady=(0, 16))
        tk.Label(filter_card, text="FROM", bg=WHITE, fg=MUTED,
                 font=("Segoe UI Semibold", 8)).pack(side="left", padx=(0, 8))
        today = date.today()
        self.start_entry = self._entry(filter_card, width=13)
        self.start_entry.insert(0, today.replace(day=1).isoformat())
        self._make_date_field(self.start_entry, lambda: self.select_report_date(self.start_entry))
        self.start_entry.pack(side="left", ipady=8, padx=(0, 16))
        tk.Label(filter_card, text="TO", bg=WHITE, fg=MUTED,
                 font=("Segoe UI Semibold", 8)).pack(side="left", padx=(0, 8))
        self.end_entry = self._entry(filter_card, width=13)
        self.end_entry.insert(0, today.isoformat())
        self._make_date_field(self.end_entry, lambda: self.select_report_date(self.end_entry))
        self.end_entry.pack(side="left", ipady=8, padx=(0, 16))
        self._button(filter_card, "Generate report", self.load_report).pack(side="left", ipady=3)
        self._button(filter_card, "Export Excel  ↓", self.export_excel).pack(side="right", ipady=3)
        self._button(filter_card, "Export CSV", self.export_csv, primary=False).pack(side="right", padx=(0, 8), ipady=3)

        self.report_metrics = self._metric_cards(page, [
            ("Transactions", "0", "In selected period", ACCENT),
            ("Revenue", "₹0.00", "Total revenue", MINT),
            ("Cash", "₹0.00", "Cash revenue", "#D89B31"),
            ("Online", "₹0.00", "Online revenue", "#59A6D8"),
        ])
        self.report_service_card = self._card(page, padx=0, pady=0)
        self.report_service_card.pack(fill="both", expand=True)
        tk.Label(self.report_service_card, text="Service breakdown", bg=WHITE, fg=INK,
                 font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=18, pady=(15, 10))
        table_holder = tk.Frame(self.report_service_card, bg=WHITE)
        table_holder.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.report_tree = self._tree(table_holder, ("service", "count", "revenue"),
                                      ("Service", "Transactions", "Revenue"), (480, 180, 220))

    def _build_settings(self, page):
        self._section_heading(page, "Business profile", "This name appears across your workspace")
        card = self._card(page, padx=24, pady=22)
        card.pack(fill="x", anchor="n")
        tk.Label(card, text="BUSINESS NAME", bg=WHITE, fg=MUTED,
                 font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(4, 8))
        row = tk.Frame(card, bg=WHITE)
        row.pack(fill="x")
        self.business_entry = self._entry(row)
        self.business_entry.insert(0, self.business["name"])
        self.business_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self._button(row, "Save changes", self.save_business_name).pack(side="left", padx=(12, 0), ipady=4)
        note = self._card(page, padx=24, pady=19)
        note.pack(fill="x", pady=(16, 0))
        tk.Label(note, text="Your data stays on this computer", bg=WHITE, fg=INK,
                 font=("Segoe UI Semibold", 11)).pack(anchor="w")
        tk.Label(note, text="Transactions and settings are stored in your local SQLite database.",
                 bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 0))

    @staticmethod
    def _tree(parent, columns, headings, widths):
        wrapper = tk.Frame(parent, bg=WHITE)
        wrapper.pack(fill="both", expand=True)
        tree = ttk.Treeview(wrapper, columns=columns, show="headings", style="Premium.Treeview")
        for column, heading, width in zip(columns, headings, widths):
            tree.heading(column, text=heading)
            tree.column(column, width=width, minwidth=80, anchor="w")
        tree.tag_configure("inactive", foreground="#98A2B3")
        scroll = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def show_page(self, page_key):
        # Keep one page managed at a time. Raising several packed, expanding
        # siblings can leave geometry allocated to the hidden pages.
        for key, frame in self.page_frames.items():
            if key == page_key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        title, subtitle = self.PAGE_INFO[page_key]
        self.page_title.configure(text=title)
        self.page_subtitle.configure(text=subtitle)
        for key, button in self.nav_buttons.items():
            active = key == page_key
            button.configure(bg=NAVY_LIGHT if active else NAVY,
                             fg=WHITE if active else "#BCC7D7")

    def select_report_date(self, entry):
        self.date_picker = DatePicker(self.root, entry.get().strip(),
                                      lambda value: self._set_date_entry(entry, value))
        return "break"

    @staticmethod
    def _make_date_field(entry, open_picker):
        entry.configure(state="readonly", readonlybackground=WHITE, cursor="hand2")
        entry.bind("<Button-1>", lambda _event: open_picker())
        entry.bind("<Return>", lambda _event: open_picker())

    @staticmethod
    def _set_date_entry(entry, value):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, value)
        entry.configure(state="readonly")

    def select_dashboard_date(self):
        self.date_picker = DatePicker(self.root, self.dashboard_date.isoformat(), self._set_dashboard_date)
        return "break"

    def _set_dashboard_date(self, value):
        self.dashboard_date = date.fromisoformat(value)
        self._set_date_entry(self.dashboard_date_entry, value)
        self.refresh_dashboard()

    def refresh_dashboard(self):
        selected_date = self.dashboard_date.isoformat()
        report = reports.get_report(self.business["id"], selected_date, selected_date)
        values = (_money(report["revenue_minor"]), str(report["transaction_count"]),
                  _money(report["cash_minor"]), _money(report["online_minor"]))
        for value_label, value in zip(self.dashboard_metrics.value_labels, values):
            value_label.configure(text=value)
        for item in self.dashboard_tree.get_children():
            self.dashboard_tree.delete(item)
        search = self.search_entry.get().strip()
        rows = transactions.list_transactions(
            self.business["id"], search=search,
            start_date=selected_date,
            end_date=selected_date,
            limit=500,
        )
        for row in rows:
            self.dashboard_tree.insert("", "end", values=(
                row["transaction_id"], row["service_name"], _money(row["amount_minor"]),
                row["payment_type"], _display_time(row["created_at"]),
            ))

    def refresh_services(self):
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)
        for row in services.list_services(self.business["id"], include_inactive=True):
            self.services_tree.insert(
                "", "end", iid=str(row["id"]),
                values=(row["id"], row["name"], "Active" if row["active"] else "Inactive"),
                tags=() if row["active"] else ("inactive",),
            )

    def _selected_service_id(self):
        selected = self.services_tree.selection()
        if not selected:
            messagebox.showinfo("Select a service", "Select a service first.", parent=self.root)
            return None
        return int(selected[0])

    def add_service(self):
        name = simpledialog.askstring("Add service", "Service name:", parent=self.root)
        if name is None:
            return
        try:
            services.add_service(self.business["id"], name)
            self.refresh_services()
        except ValueError as error:
            messagebox.showerror("Could not add service", str(error), parent=self.root)

    def edit_service(self):
        service_id = self._selected_service_id()
        if service_id is None:
            return
        current = self.services_tree.item(str(service_id), "values")[1]
        name = simpledialog.askstring("Edit service", "Service name:", initialvalue=current, parent=self.root)
        if name is None:
            return
        try:
            services.edit_service(self.business["id"], service_id, name)
            self.refresh_services()
        except ValueError as error:
            messagebox.showerror("Could not edit service", str(error), parent=self.root)

    def toggle_service(self):
        service_id = self._selected_service_id()
        if service_id is None:
            return
        status = self.services_tree.item(str(service_id), "values")[2]
        try:
            if status == "Active":
                services.deactivate_service(self.business["id"], service_id)
            else:
                services.activate_service(self.business["id"], service_id)
            self.refresh_services()
        except ValueError as error:
            messagebox.showerror("Could not update service", str(error), parent=self.root)

    def start_transaction(self):
        active_services = services.list_services(self.business["id"])
        dialog = tk.Toplevel(self.root)
        dialog.title("New transaction")
        dialog.geometry("470x465")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        panel = tk.Frame(dialog, bg=WHITE, padx=28, pady=25,
                         highlightbackground=LINE, highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(panel, text="New transaction", bg=WHITE, fg=INK,
                 font=("Segoe UI Semibold", 20)).pack(anchor="w")
        tk.Label(panel, text="Choose a service or type a new one. New names are saved to Services.", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 22))
        tk.Label(panel, text="SERVICE", bg=WHITE, fg=MUTED,
                 font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 6))
        service_choice = tk.StringVar(value="Type or select a service")
        service_combo = ttk.Combobox(
            panel, textvariable=service_choice,
            values=[item["name"] for item in active_services], state="normal",
        )
        service_combo.pack(fill="x", ipady=5, pady=(0, 16))

        def clear_service_prompt(_event=None):
            if service_choice.get() == "Type or select a service":
                service_choice.set("")

        service_combo.bind("<FocusIn>", clear_service_prompt)
        service_combo.bind("<Button-1>", clear_service_prompt)
        tk.Label(panel, text="AMOUNT  (₹)", bg=WHITE, fg=MUTED,
                 font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 6))
        amount = self._entry(panel)
        amount.pack(fill="x", ipady=10, pady=(0, 16))
        tk.Label(panel, text="PAYMENT TYPE", bg=WHITE, fg=MUTED,
                 font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 6))
        payment = tk.StringVar(value="Cash")
        ttk.Combobox(panel, textvariable=payment, values=transactions.PAYMENT_TYPES,
                     state="readonly").pack(fill="x", ipady=5, pady=(0, 20))

        def save():
            try:
                row = transactions.create_transaction_for_service_name(
                    self.business["id"], service_choice.get(), amount.get(), payment.get()
                )
            except ValueError as error:
                messagebox.showerror("Invalid transaction", str(error), parent=dialog)
                return
            dialog.destroy()
            self.refresh_dashboard()
            self.load_report(show_error=False)
            messagebox.showinfo("Transaction saved", f"Saved {row['transaction_id']}", parent=self.root)

        self._button(panel, "Save transaction", save).pack(fill="x", ipady=6)
        amount.focus_set()

    def save_business_name(self):
        try:
            self.business = business.set_business(self.business_entry.get())
        except ValueError as error:
            messagebox.showerror("Invalid business name", str(error), parent=self.root)
            return
        self.sidebar_business.configure(text=self.business["name"])
        messagebox.showinfo("Saved", "Business name updated.", parent=self.root)

    def load_report(self, show_error=True):
        try:
            report = reports.get_report(
                self.business["id"], self.start_entry.get().strip(), self.end_entry.get().strip()
            )
        except ValueError as error:
            self.last_report = None
            if show_error:
                messagebox.showerror("Invalid date range", str(error), parent=self.root)
            return
        self.last_report = report
        values = (str(report["transaction_count"]), _money(report["revenue_minor"]),
                  _money(report["cash_minor"]), _money(report["online_minor"]))
        for value_label, value in zip(self.report_metrics.value_labels, values):
            value_label.configure(text=value)
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        for row in report["services"]:
            self.report_tree.insert("", "end", values=(
                row["service_name"], row["transaction_count"], _money(row["revenue_minor"])
            ))

    def export_csv(self):
        self._export_report("csv")

    def export_excel(self):
        self._export_report("xlsx")

    def _export_report(self, file_format):
        if not self.last_report:
            self.load_report()
        if not self.last_report:
            return
        if file_format == "xlsx":
            extension = ".xlsx"
            types = [("Excel workbook", "*.xlsx")]
            initial_name = "business-report.xlsx"
        else:
            extension = ".csv"
            types = [("CSV file", "*.csv")]
            initial_name = "business-report.csv"
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Export report", defaultextension=extension,
            filetypes=types, initialfile=initial_name,
        )
        if not path:
            return
        try:
            if file_format == "xlsx":
                reports.export_report_xlsx(self.last_report, Path(path))
            else:
                reports.export_report_csv(self.last_report, Path(path))
        except OSError as error:
            messagebox.showerror("Export failed", str(error), parent=self.root)
            return
        messagebox.showinfo("Export complete", f"Report saved to:\n{path}", parent=self.root)


def run_app():
    root = tk.Tk()
    root.withdraw()
    from database import initialize_database
    initialize_database()
    configured = business.get_business()
    root.deiconify()
    if configured:
        BusinessManagerApp(root, configured)
    else:
        SetupWindow(root, lambda _business: _complete_setup(root))
    root.mainloop()


def _complete_setup(root):
    for child in root.winfo_children():
        child.destroy()
    configured = business.get_business()
    BusinessManagerApp(root, configured)

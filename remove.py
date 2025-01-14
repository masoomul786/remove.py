import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import importlib
import json
import threading
import webbrowser


class DependencyManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Dependency Manager")
        self.geometry("900x700")
        self.configure(bg="#2C2F33")
        self.resizable(False, False)

        # Variables
        self.packages_data = []

        # UI Setup
        self.create_styles()
        self.create_widgets()
        self.fetch_packages()

    def create_styles(self):
        """Create custom styles for the app."""
        style = ttk.Style(self)
        style.theme_use("clam")

        # Treeview Styles
        style.configure(
            "Treeview",
            background="#3A3F44",
            foreground="#EAEAEA",
            rowheight=30,
            fieldbackground="#3A3F44",
            font=("Segoe UI", 11),
        )
        style.configure(
            "Treeview.Heading",
            background="#4CAF50",
            foreground="white",
            font=("Segoe UI", 12, "bold"),
        )
        style.map("Treeview", background=[("selected", "#4CAF50")])

        # Button Styles
        style.configure(
            "TButton",
            background="#4CAF50",
            foreground="white",
            font=("Segoe UI", 11),
            borderwidth=0,
            focuscolor="#2C2F33",
        )
        style.map(
            "TButton",
            background=[("active", "#45A049")],
            relief=[("pressed", "sunken")],
        )

        # Progress Bar
        style.configure("TProgressbar", troughcolor="#2C2F33", background="#4CAF50")

    def create_widgets(self):
        """Create all UI components."""
        # Top Frame for Search and Actions
        top_frame = tk.Frame(self, bg="#2C2F33")
        top_frame.pack(fill="x", pady=10, padx=10)

        self.search_entry = ttk.Entry(top_frame, width=30, font=("Segoe UI", 11))
        self.search_entry.pack(side="left", padx=5)
        search_button = ttk.Button(top_frame, text="Search", command=self.search_package)
        search_button.pack(side="left", padx=5)

        refresh_button = ttk.Button(top_frame, text="Refresh", command=self.refresh_packages)
        refresh_button.pack(side="left", padx=5)

        details_button = ttk.Button(top_frame, text="View Details", command=self.view_package_details)
        details_button.pack(side="left", padx=5)

        uninstall_button = ttk.Button(
            top_frame, text="Uninstall Selected", command=self.uninstall_selected
        )
        uninstall_button.pack(side="left", padx=5)

        more_button = ttk.Button(top_frame, text="More", command=self.open_dependency_search)
        more_button.pack(side="left", padx=5)

        # Treeview Frame
        frame = tk.Frame(self, bg="#2C2F33")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Name", "Version", "Status")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("Name", text="Package Name")
        self.tree.heading("Version", text="Version")
        self.tree.heading("Status", text="Status")

        self.tree.column("Name", width=250)
        self.tree.column("Version", width=100)
        self.tree.column("Status", width=150)

        # Alternating Row Colors
        self.tree.tag_configure("oddrow", background="#3A3F44")
        self.tree.tag_configure("evenrow", background="#2E3338")

        # Treeview Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Progress Bar and Status
        self.progress_bar = ttk.Progressbar(self, mode="determinate", length=400)
        self.progress_bar.pack(pady=10)
        self.status_label = tk.Label(
            self, text="Status: Ready", bg="#2C2F33", fg="#EAEAEA", font=("Segoe UI", 10), anchor="w"
        )
        self.status_label.pack(fill="x", padx=10)

    def fetch_packages(self):
        """Fetch installed packages in a background thread."""
        def worker():
            self.packages_data = self.get_installed_packages()
            self.update_treeview()

        threading.Thread(target=worker, daemon=True).start()

    def get_installed_packages(self):
        """Retrieve all installed Python packages."""
        try:
            self.status_label.config(text="Fetching installed packages...")
            result = subprocess.run(["pip", "list", "--format=json"], capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError:
            messagebox.showerror("Error", "Failed to fetch installed packages.")
            return []

    def update_treeview(self):
        """Update the Treeview with the fetched packages."""
        self.tree.delete(*self.tree.get_children())
        for i, pkg in enumerate(self.packages_data):
            name, version = pkg["name"], pkg["version"]
            status = "OK" if self.check_package_import(name) else "Not Functional"
            tag = "oddrow" if i % 2 else "evenrow"
            self.tree.insert("", "end", values=(name, version, status), tags=(tag,))
        self.status_label.config(text="Loaded all installed packages.")

    def check_package_import(self, package_name):
        """Check if a package can be imported successfully."""
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False

    def uninstall_selected(self):
        """Uninstall the selected package."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a package to uninstall.")
            return
        package_name = self.tree.item(selected)["values"][0]
        response = messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall {package_name}?")
        if response:
            try:
                subprocess.run(["pip", "uninstall", "-y", package_name], text=True, check=True)
                messagebox.showinfo("Success", f"{package_name} has been uninstalled.")
                self.refresh_packages()
            except subprocess.CalledProcessError:
                messagebox.showerror("Error", f"Failed to uninstall {package_name}.")

    def view_package_details(self):
        """View detailed information about the selected package."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a package to view details.")
            return
        package_name = self.tree.item(selected)["values"][0]
        details = self.get_package_description(package_name)
        detail_window = tk.Toplevel(self)
        detail_window.title(f"Details for {package_name}")
        detail_window.geometry("600x400")
        text_widget = tk.Text(detail_window, wrap="word", font=("Segoe UI", 12), bg="#1E1E1E", fg="white")
        text_widget.insert("1.0", details)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

    def get_package_description(self, package_name):
        """Retrieve detailed information about the package."""
        try:
            result = subprocess.run(["pip", "show", package_name], capture_output=True, text=True, check=True)
            return result.stdout or "No additional details available."
        except subprocess.CalledProcessError:
            return "No additional details available."

    def open_dependency_search(self):
        """Search the web for the selected dependency."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a package to search for.")
            return
        package_name = self.tree.item(selected)["values"][0]
        query = f"What is {package_name} for?"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)

    def refresh_packages(self):
        """Refresh the package list."""
        self.fetch_packages()

    def search_package(self):
        """Search for a specific package."""
        query = self.search_entry.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        for i, pkg in enumerate(self.packages_data):
            if query in pkg["name"].lower():
                name, version = pkg["name"], pkg["version"]
                status = "OK" if self.check_package_import(name) else "Not Functional"
                tag = "oddrow" if i % 2 else "evenrow"
                self.tree.insert("", "end", values=(name, version, status), tags=(tag,))


if __name__ == "__main__":
    app = DependencyManagerApp()
    app.mainloop()

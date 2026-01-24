import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import create_map_poster as cmp


POSTERS_DIR = Path(cmp.POSTERS_DIR)


class MapPosterGUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title("City Map Poster Generator")
        master.geometry("520x540")
        master.resizable(False, False)

        self.city_var = tk.StringVar()
        self.country_var = tk.StringVar()
        self.country_label_var = tk.StringVar()
        self.name_label_var = tk.StringVar()
        self.distance_var = tk.StringVar(value="29000")
        self.width_var = tk.StringVar(value="12")
        self.height_var = tk.StringVar(value="16")
        self.format_var = tk.StringVar(value="png")
        self.theme_var = tk.StringVar()
        self.all_themes_var = tk.BooleanVar(value=False)

        self.available_themes: list[str] = []

        self._build_ui()
        self._refresh_themes()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        header = tk.Label(self.master, text="City Map Poster Generator", font=("Segoe UI", 14, "bold"))
        header.pack(pady=(12, 2))

        form = tk.Frame(self.master)
        form.pack(fill="x", padx=12)

        # Row 1: city / country
        row1 = tk.Frame(form)
        row1.pack(fill="x")
        tk.Label(row1, text="City:").grid(row=0, column=0, sticky="w", **pad)
        tk.Entry(row1, textvariable=self.city_var, width=22).grid(row=0, column=1, **pad)
        tk.Label(row1, text="Country:").grid(row=0, column=2, sticky="w", **pad)
        tk.Entry(row1, textvariable=self.country_var, width=22).grid(row=0, column=3, **pad)

        # Row 2: labels
        row2 = tk.Frame(form)
        row2.pack(fill="x")
        tk.Label(row2, text="Display city (optional):").grid(row=0, column=0, sticky="w", **pad)
        tk.Entry(row2, textvariable=self.name_label_var, width=22).grid(row=0, column=1, **pad)
        tk.Label(row2, text="Display country (optional):").grid(row=0, column=2, sticky="w", **pad)
        tk.Entry(row2, textvariable=self.country_label_var, width=22).grid(row=0, column=3, **pad)

        # Row 3: theme / all themes
        row3 = tk.Frame(form)
        row3.pack(fill="x")
        tk.Label(row3, text="Theme:").grid(row=0, column=0, sticky="w", **pad)
        self.theme_combo = ttk.Combobox(row3, textvariable=self.theme_var, state="readonly", width=19)
        self.theme_combo.grid(row=0, column=1, **pad)
        ttk.Button(row3, text="Refresh", command=self._refresh_themes).grid(row=0, column=2, **pad)
        tk.Checkbutton(row3, text="Generate all themes", variable=self.all_themes_var).grid(row=0, column=3, sticky="w", **pad)

        # Row 4: distance / format
        row4 = tk.Frame(form)
        row4.pack(fill="x")
        tk.Label(row4, text="Distance (m):").grid(row=0, column=0, sticky="w", **pad)
        tk.Entry(row4, textvariable=self.distance_var, width=22).grid(row=0, column=1, **pad)
        tk.Label(row4, text="Format:").grid(row=0, column=2, sticky="w", **pad)
        ttk.Combobox(row4, textvariable=self.format_var, values=["png", "svg", "pdf"], state="readonly", width=19).grid(row=0, column=3, **pad)

        # Row 5: size
        row5 = tk.Frame(form)
        row5.pack(fill="x")
        tk.Label(row5, text="Width (in):").grid(row=0, column=0, sticky="w", **pad)
        tk.Entry(row5, textvariable=self.width_var, width=22).grid(row=0, column=1, **pad)
        tk.Label(row5, text="Height (in):").grid(row=0, column=2, sticky="w", **pad)
        tk.Entry(row5, textvariable=self.height_var, width=22).grid(row=0, column=3, **pad)

        # Buttons
        actions = tk.Frame(self.master)
        actions.pack(fill="x", pady=12)
        self.generate_btn = ttk.Button(actions, text="Generate poster", command=self._start_generation)
        self.generate_btn.pack(side="left", padx=12)
        ttk.Button(actions, text="Open posters folder", command=self._open_posters_folder).pack(side="left")

        # Status
        self.status_text = tk.StringVar(value="Ready")
        status_frame = tk.Frame(self.master)
        status_frame.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(status_frame, textvariable=self.status_text, anchor="w", justify="left", bg="#f5f5f5", relief="groove", bd=1, padx=8, pady=8, wraplength=480).pack(fill="both", expand=True)

    def _refresh_themes(self) -> None:
        try:
            themes = cmp.get_available_themes()
        except Exception as exc:
            messagebox.showerror("Error", f"Could not read themes: {exc}")
            return

        if not themes:
            messagebox.showwarning("No themes", "No theme JSON files found in the themes folder.")
            return

        self.available_themes = themes
        self.theme_combo["values"] = themes
        if self.theme_var.get() not in themes:
            self.theme_var.set(themes[0])

    def _set_status(self, text: str) -> None:
        self.master.after(0, self.status_text.set, text)

    def _show_info(self, title: str, msg: str) -> None:
        self.master.after(0, lambda: messagebox.showinfo(title, msg))

    def _show_error(self, title: str, msg: str) -> None:
        self.master.after(0, lambda: messagebox.showerror(title, msg))

    def _start_generation(self) -> None:
        city = self.city_var.get().strip()
        country = self.country_var.get().strip()
        if not city or not country:
            messagebox.showwarning("Missing data", "City and country are required.")
            return

        try:
            distance = int(float(self.distance_var.get()))
            width = float(self.width_var.get())
            height = float(self.height_var.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Distance, width, and height must be numbers.")
            return

        fmt = self.format_var.get()
        if fmt not in {"png", "svg", "pdf"}:
            messagebox.showerror("Invalid format", "Format must be png, svg, or pdf.")
            return

        themes = self.available_themes if self.all_themes_var.get() else [self.theme_var.get()]
        if not themes:
            messagebox.showwarning("No theme selected", "Select at least one theme.")
            return

        self.generate_btn.config(state="disabled")
        self._set_status("Starting generation...")

        thread = threading.Thread(
            target=self._run_generation,
            args=(city, country, distance, width, height, fmt, themes, self.country_label_var.get().strip() or None, self.name_label_var.get().strip() or None),
            daemon=True,
        )
        thread.start()

    def _run_generation(
        self,
        city: str,
        country: str,
        distance: int,
        width: float,
        height: float,
        fmt: str,
        themes: list[str],
        country_label: str | None,
        name_label: str | None,
    ) -> None:
        try:
            self._set_status("Geocoding...")
            coords = cmp.get_coordinates(city, country)

            for idx, theme_name in enumerate(themes, start=1):
                self._set_status(f"Generating {idx}/{len(themes)}: {theme_name}")
                cmp.THEME = cmp.load_theme(theme_name)
                output_file = cmp.generate_output_filename(name_label or city, theme_name, fmt)
                cmp.create_poster(
                    name_label or city,
                    country,
                    coords,
                    distance,
                    output_file,
                    fmt,
                    width,
                    height,
                    country_label=country_label,
                    name_label=name_label,
                )

            msg = f"Finished! Files saved to {POSTERS_DIR.resolve()}"
            self._set_status(msg)
            self._show_info("Success", msg)
        except Exception as exc:
            self._set_status(f"Error: {exc}")
            self._show_error("Error", str(exc))
        finally:
            self.master.after(0, lambda: self.generate_btn.config(state="normal"))

    def _open_posters_folder(self) -> None:
        POSTERS_DIR.mkdir(exist_ok=True)
        path = POSTERS_DIR.resolve()
        try:
            if os.name == "nt":
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f"open \"{path}\"")
            else:
                os.system(f"xdg-open \"{path}\"")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open folder: {exc}")


def main() -> None:
    root = tk.Tk()
    MapPosterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

"""Continent Clicker — a Python/Tkinter country-shape quiz.

Run with:  python map_game.py
An internet connection is required the first time a map is selected, because
the public Natural Earth country-boundary data is downloaded on demand.
"""

import json
import math
import random
import threading
import tkinter as tk
from tkinter import messagebox
from urllib.request import urlopen

DATA_URL = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"

# ISO-3 country codes grouped by the five selectable continents.
CONTINENTS = {
    "Africa": "DZA AGO BEN BWA BFA BDI CMR CAF TCD COM COG COD CIV DJI EGY GNQ ERI SWZ ETH GAB GMB GHA GIN GNB KEN LSO LBR LBY MDG MWI MLI MRT MUS MAR MOZ NAM NER NGA RWA STP SEN SYC SLE SOM ZAF SSD SDN TZA TGO TUN UGA ZMB ZWE".split(),
    "Asia": "AFG ARM AZE BHR BGD BTN BRN KHM CHN CYP GEO IND IDN IRN IRQ ISR JPN JOR KAZ KWT KGZ LAO LBN MYS MDV MNG MMR NPL PRK OMN PAK PHL QAT SAU SGP KOR LKA SYR TWN TJK THA TLS TUR TKM ARE UZB VNM YEM".split(),
    "Europe": "ALB AND AUT BLR BEL BIH BGR HRV CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ITA LVA LIE LTU LUX MLT MDA MCO MNE NLD MKD NOR POL PRT ROU RUS SMR SRB SVK SVN ESP SWE CHE UKR GBR VAT".split(),
    "North America": "ATG BHS BRB BLZ CAN CRI CUB DMA DOM SLV GRD GTM HTI HND JAM MEX NIC PAN KNA LCA VCT TTO USA".split(),
    "South America": "ARG BOL BRA CHL COL ECU GUY PRY PER SUR URY VEN".split(),
}


class MapGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Continent Clicker")
        self.minsize(850, 620)
        self.configure(padx=18, pady=16, bg="#f6f8fb")
        self.features = None
        self.selected = None
        self.visible = []
        self.answer = None
        self.answered = False
        self.score = self.attempts = self.streak = 0
        self.item_codes = {}

        tk.Label(self, text="Continent Clicker", font=("Segoe UI", 24, "bold"), bg="#f6f8fb", fg="#14213d").pack(anchor="w")
        tk.Label(self, text="Choose a continent, then click the country named in the prompt.", font=("Segoe UI", 11), bg="#f6f8fb", fg="#52627a").pack(anchor="w", pady=(2, 14))

        choices = tk.Frame(self, bg="#f6f8fb")
        choices.pack(fill="x", pady=(0, 12))
        self.buttons = {}
        for continent in CONTINENTS:
            button = tk.Button(choices, text=continent, command=lambda c=continent: self.choose(c), relief="flat", padx=12, pady=8, bg="white", fg="#14213d", font=("Segoe UI", 10, "bold"))
            button.pack(side="left", padx=(0, 8))
            self.buttons[continent] = button

        body = tk.Frame(self, bg="#f6f8fb")
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(body, bg="#dceef8", highlightthickness=1, highlightbackground="#c8d8e8")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _: self.draw_map())
        panel = tk.Frame(body, width=235, bg="white", padx=18, pady=18, highlightthickness=1, highlightbackground="#d7e0ea")
        panel.pack(side="right", fill="y", padx=(15, 0))
        panel.pack_propagate(False)
        self.round_label = tk.Label(panel, text="READY TO PLAY", font=("Segoe UI", 9, "bold"), bg="white", fg="#5c6b80")
        self.round_label.pack(anchor="w")
        self.prompt = tk.Label(panel, text="Pick a continent", wraplength=190, justify="left", font=("Segoe UI", 18, "bold"), bg="white", fg="#14213d")
        self.prompt.pack(anchor="w", pady=(8, 12))
        tk.Label(panel, text="Click one country shape. Each round has one answer.", wraplength=190, justify="left", font=("Segoe UI", 10), bg="white", fg="#52627a").pack(anchor="w")
        self.stats = tk.Label(panel, text="Score  0 / 0\nStreak  0", justify="left", font=("Segoe UI", 12, "bold"), bg="#eef4f9", fg="#14213d", padx=12, pady=12)
        self.stats.pack(fill="x", pady=20)
        self.next_button = tk.Button(panel, text="Next country", command=self.new_round, state="disabled", relief="flat", bg="#1769aa", fg="white", font=("Segoe UI", 10, "bold"), padx=10, pady=9)
        self.next_button.pack(fill="x")
        self.feedback = tk.Label(panel, text="", wraplength=190, justify="left", font=("Segoe UI", 10, "bold"), bg="white")
        self.feedback.pack(anchor="w", pady=(15, 0))
        self.status = tk.Label(self.canvas, text="Choose a continent to begin", font=("Segoe UI", 12, "bold"), bg="#dceef8", fg="#52627a")
        self.status.place(relx=.5, rely=.5, anchor="center")

    def choose(self, continent):
        self.selected = continent
        for name, button in self.buttons.items():
            button.configure(bg="#14213d" if name == continent else "white", fg="white" if name == continent else "#14213d")
        self.score = self.attempts = self.streak = 0
        if self.features is None:
            self.status.configure(text="Loading country shapes…")
            threading.Thread(target=self.download_data, daemon=True).start()
        else:
            self.prepare_continent()

    def download_data(self):
        try:
            with urlopen(DATA_URL, timeout=30) as response:
                data = json.load(response)
            self.features = data["features"]
            self.after(0, self.prepare_continent)
        except Exception as error:
            self.after(0, lambda: self.status.configure(text=f"Could not load the map: {error}"))

    def code(self, feature):
        props = feature.get("properties", {})
        return str(props.get("ISO_A3") or props.get("iso_a3") or props.get("ADM0_A3") or "").upper()

    def name(self, feature):
        props = feature.get("properties", {})
        return props.get("ADMIN") or props.get("name") or self.code(feature)

    def prepare_continent(self):
        if not self.selected or self.features is None:
            return
        allowed = set(CONTINENTS[self.selected])
        self.visible = [f for f in self.features if self.code(f) in allowed]
        if not self.visible:
            self.status.configure(text="No shapes were found for that continent.")
            return
        self.status.place_forget()
        self.draw_map()
        self.new_round()

    def new_round(self):
        if not self.visible:
            return
        self.answer = random.choice(self.visible)
        self.answered = False
        self.prompt.configure(text=self.name(self.answer))
        self.round_label.configure(text=f"{self.selected.upper()} · FIND THIS COUNTRY")
        self.feedback.configure(text="", fg="#14213d")
        self.next_button.configure(state="disabled")
        self.update_stats()
        self.draw_map()

    def update_stats(self):
        self.stats.configure(text=f"Score  {self.score} / {self.attempts}\nStreak  {self.streak}")

    def polygons(self, geometry):
        kind, coords = geometry.get("type"), geometry.get("coordinates", [])
        if kind == "Polygon": return [coords]
        if kind == "MultiPolygon": return coords
        return []

    def draw_map(self):
        if not self.visible or self.canvas.winfo_width() < 20:
            return
        self.canvas.delete("country")
        self.item_codes.clear()
        all_points = [p for f in self.visible for poly in self.polygons(f["geometry"]) for ring in poly for p in ring]
        if not all_points:
            return
        min_lon, max_lon = min(p[0] for p in all_points), max(p[0] for p in all_points)
        min_lat, max_lat = min(p[1] for p in all_points), max(p[1] for p in all_points)
        width, height, pad = self.canvas.winfo_width(), self.canvas.winfo_height(), 26
        def project(point):
            lon, lat = point[0], max(-85, min(85, point[1]))
            x = (lon - min_lon) / max(max_lon - min_lon, .1)
            merc = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
            low = math.log(math.tan(math.pi / 4 + math.radians(min_lat) / 2))
            high = math.log(math.tan(math.pi / 4 + math.radians(max_lat) / 2))
            y = 1 - (merc - low) / max(high - low, .1)
            scale = min((width - 2 * pad) / 1, (height - 2 * pad) / 1)
            return pad + x * (width - 2 * pad), pad + y * (height - 2 * pad)
        for feature in self.visible:
            code = self.code(feature)
            fill = "#d5dbe5"
            if self.answered and code == self.code(self.answer): fill = "#14804a"
            for poly in self.polygons(feature["geometry"]):
                if not poly: continue
                points = [n for lonlat in poly[0] for n in project(lonlat)]
                item = self.canvas.create_polygon(points, fill=fill, outline="white", width=1, tags=("country", code))
                self.item_codes[item] = code
                self.canvas.tag_bind(item, "<Button-1>", lambda _, c=code: self.guess(c))
                self.canvas.tag_bind(item, "<Enter>", lambda _, i=item: self.canvas.itemconfigure(i, fill="#9fc7e6") if not self.answered else None)
                self.canvas.tag_bind(item, "<Leave>", lambda _, i=item, c=code: self.canvas.itemconfigure(i, fill="#d5dbe5") if not self.answered else None)

    def guess(self, code):
        if self.answered or not self.answer:
            return
        self.answered = True
        self.attempts += 1
        correct = code == self.code(self.answer)
        if correct:
            self.score += 1; self.streak += 1
            self.feedback.configure(text=f"Correct — that’s {self.name(self.answer)}!", fg="#14804a")
        else:
            self.streak = 0
            chosen = next((self.name(f) for f in self.visible if self.code(f) == code), "that country")
            self.feedback.configure(text=f"Not quite — you clicked {chosen}. The answer is highlighted.", fg="#bd2f37")
        self.next_button.configure(state="normal")
        self.update_stats()
        self.draw_map()


if __name__ == "__main__":
    MapGame().mainloop()

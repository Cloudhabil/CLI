import json
from pathlib import Path
import tkinter as tk
from typing import List


class PixelAvatarEditor(tk.Tk):
    """Simple pixel editor with configurable grid and basic palette."""

    def __init__(self, user_id: str, size: int = 32, pixel_size: int = 16) -> None:
        super().__init__()
        self.title(f"Pixel Avatar - {user_id}")
        self.user_id = user_id
        self.size = size
        self.pixel_size = pixel_size
        self.palette = [
            "#000000",
            "#ffffff",
            "#ff0000",
            "#00ff00",
            "#0000ff",
            "#ffff00",
            "#00ffff",
            "#ff00ff",
        ]
        self.selected = 0
        self.pixels = self._load_pixels()
        self.rects = [[0] * size for _ in range(size)]

        self.canvas = tk.Canvas(
            self, width=size * pixel_size, height=size * pixel_size, bg="white"
        )
        self.canvas.grid(row=0, column=0, columnspan=len(self.palette))
        for y in range(size):
            for x in range(size):
                x0 = x * pixel_size
                y0 = y * pixel_size
                rect_id = self.canvas.create_rectangle(
                    x0,
                    y0,
                    x0 + pixel_size,
                    y0 + pixel_size,
                    outline="gray",
                    fill=self.palette[self.pixels[y][x]],
                )
                self.canvas.tag_bind(
                    rect_id, "<Button-1>", lambda e, x=x, y=y: self._paint(x, y)
                )
                self.rects[y][x] = rect_id

        palette_frame = tk.Frame(self)
        palette_frame.grid(row=1, column=0, columnspan=len(self.palette))
        for idx, color in enumerate(self.palette):
            tk.Button(
                palette_frame,
                bg=color,
                width=2,
                command=lambda i=idx: self._set_color(i),
            ).grid(row=0, column=idx)

        tk.Button(self, text="Save", command=self._save).grid(
            row=2, column=0, columnspan=len(self.palette)
        )

    def _load_pixels(self) -> List[List[int]]:
        path = Path("profile/avatars") / f"{self.user_id}.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get(
                        "pixels", [[0 for _ in range(self.size)] for _ in range(self.size)]
                    )
            except Exception:
                pass
        return [[0 for _ in range(self.size)] for _ in range(self.size)]

    def _set_color(self, idx: int) -> None:
        self.selected = idx

    def _paint(self, x: int, y: int) -> None:
        self.pixels[y][x] = self.selected
        self.canvas.itemconfig(self.rects[y][x], fill=self.palette[self.selected])

    def _save(self) -> None:
        base = Path("profile/avatars")
        base.mkdir(parents=True, exist_ok=True)
        path = base / f"{self.user_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"palette": self.palette, "pixels": self.pixels}, f)


def edit_avatar(user_id: str, size: int = 32) -> None:
    editor = PixelAvatarEditor(user_id, size)
    editor.mainloop()

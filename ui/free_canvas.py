import tkinter as tk
from typing import Any, Dict, List


class FreeCanvas(tk.Frame):
    """Canvas widget with basic zoom, layer and drag support."""

    def __init__(self, master: tk.Misc | None = None) -> None:
        super().__init__(master)
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.layers: Dict[str, List[int]] = {}
        self.scale = 1.0
        self._drag_data = {"x": 0, "y": 0}

        # Bind interactions
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<MouseWheel>", self._zoom)
        self.canvas.bind("<Button-4>", self._zoom)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._zoom)  # Linux scroll down

    # --- Layer handling -------------------------------------------------
    def add_layer(self, name: str) -> None:
        if name not in self.layers:
            self.layers[name] = []

    def add_to_layer(self, name: str, item_id: int) -> None:
        self.add_layer(name)
        self.layers[name].append(item_id)
        self.canvas.addtag_withtag(name, item_id)

    def create_rectangle(self, layer: str, *coords: float, **kwargs: Any) -> int:
        item_id = self.canvas.create_rectangle(*coords, **kwargs)
        self.add_to_layer(layer, item_id)
        return item_id

    # --- Drag & Zoom ----------------------------------------------------
    def _start_drag(self, event: tk.Event) -> None:  # pragma: no cover - GUI
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _drag(self, event: tk.Event) -> None:  # pragma: no cover - GUI
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self.canvas.move("all", dx, dy)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _zoom(self, event: tk.Event) -> None:  # pragma: no cover - GUI
        if event.num == 5 or event.delta < 0:
            factor = 0.9
        else:
            factor = 1.1
        self.scale *= factor
        self.canvas.scale("all", event.x, event.y, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # --- Layout ---------------------------------------------------------
    def get_layout(self) -> Dict[str, Any]:
        layout: Dict[str, Any] = {"scale": self.scale, "layers": {}}
        for name, items in self.layers.items():
            layout["layers"][name] = [self.canvas.coords(i) for i in items]
        return layout

    def load_layout(self, layout: Dict[str, Any]) -> None:
        self.canvas.delete("all")
        self.layers.clear()
        self.scale = layout.get("scale", 1.0)
        for name, items in layout.get("layers", {}).items():
            for coords in items:
                item_id = self.canvas.create_rectangle(*coords, tags=name)
                self.add_to_layer(name, item_id)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

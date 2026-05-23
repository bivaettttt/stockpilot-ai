from __future__ import annotations

import math
import struct
import zlib
from typing import Iterable


Color = tuple[int, int, int]


def _hex_to_rgb(value: str) -> Color:
    stripped = value.lstrip("#")
    return tuple(int(stripped[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]


WHITE = _hex_to_rgb("#FFFFFF")
SLATE = _hex_to_rgb("#CBD5E1")
GRID = _hex_to_rgb("#E2E8F0")
TEXT = _hex_to_rgb("#0F172A")


class Canvas:
    def __init__(self, width: int, height: int, background: Color = WHITE) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(background * (width * height))

    def _set_pixel(self, x: int, y: int, color: Color) -> None:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return
        offset = (y * self.width + x) * 3
        self.pixels[offset : offset + 3] = bytes(color)

    def rect(self, x: int, y: int, w: int, h: int, color: Color) -> None:
        x2 = min(self.width, x + w)
        y2 = min(self.height, y + h)
        for row in range(max(0, y), max(0, y2)):
            start = (row * self.width + max(0, x)) * 3
            end = (row * self.width + x2) * 3
            if start < end:
                self.pixels[start:end] = bytes(color) * max(0, x2 - max(0, x))

    def line(self, x1: int, y1: int, x2: int, y2: int, color: Color, thickness: int = 1) -> None:
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        while True:
            for tx in range(-(thickness // 2), thickness // 2 + 1):
                for ty in range(-(thickness // 2), thickness // 2 + 1):
                    self._set_pixel(x1 + tx, y1 + ty, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    def circle(self, cx: int, cy: int, radius: int, color: Color) -> None:
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x * x + y * y <= radius * radius:
                    self._set_pixel(cx + x, cy + y, color)

    def png_bytes(self) -> bytes:
        rows = []
        row_bytes = self.width * 3
        for y in range(self.height):
            start = y * row_bytes
            rows.append(b"\x00" + bytes(self.pixels[start : start + row_bytes]))
        raw = b"".join(rows)
        return _pack_png(self.width, self.height, raw)


def _pack_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return struct.pack("!I", len(data)) + chunk_type + data + struct.pack("!I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)


def _pack_png(width: int, height: int, raw_data: bytes) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw_data, level=9)
    return signature + _pack_chunk(b"IHDR", ihdr) + _pack_chunk(b"IDAT", idat) + _pack_chunk(b"IEND", b"")


def render_bar_chart_png(
    values: Iterable[float],
    *,
    width: int = 520,
    height: int = 220,
    color: str = "#2563EB",
    horizontal: bool = False,
) -> bytes:
    points = [max(0.0, float(value)) for value in values]
    canvas = Canvas(width, height)
    canvas.rect(0, 0, width, height, WHITE)
    canvas.rect(0, 0, width, height, WHITE)
    chart_color = _hex_to_rgb(color)
    left = 32
    top = 18
    right = width - 18
    bottom = height - 28
    plot_w = right - left
    plot_h = bottom - top
    for step in range(5):
        y = top + int(plot_h * step / 4)
        canvas.line(left, y, right, y, GRID)
    canvas.line(left, bottom, right, bottom, SLATE, 2)
    if not points:
        return canvas.png_bytes()
    max_value = max(points) or 1.0
    if horizontal:
        band = plot_h / max(len(points), 1)
        for idx, value in enumerate(points):
            bar_y = int(top + idx * band + 6)
            bar_h = max(10, int(band - 10))
            bar_w = max(6, int((value / max_value) * (plot_w - 24)))
            canvas.rect(left, bar_y, bar_w, bar_h, chart_color)
    else:
        band = plot_w / max(len(points), 1)
        for idx, value in enumerate(points):
            bar_x = int(left + idx * band + 8)
            bar_w = max(12, int(band - 16))
            bar_h = max(6, int((value / max_value) * (plot_h - 12)))
            canvas.rect(bar_x, bottom - bar_h, bar_w, bar_h, chart_color)
    return canvas.png_bytes()


def render_line_chart_png(
    values: Iterable[float],
    *,
    width: int = 520,
    height: int = 220,
    color: str = "#7C3AED",
) -> bytes:
    points = [float(value) for value in values]
    canvas = Canvas(width, height)
    chart_color = _hex_to_rgb(color)
    left = 32
    top = 18
    right = width - 18
    bottom = height - 28
    plot_w = right - left
    plot_h = bottom - top
    for step in range(5):
        y = top + int(plot_h * step / 4)
        canvas.line(left, y, right, y, GRID)
    canvas.line(left, bottom, right, bottom, SLATE, 2)
    if len(points) < 2:
        return canvas.png_bytes()
    min_value = min(points)
    max_value = max(points)
    spread = max(max_value - min_value, 1.0)
    coords: list[tuple[int, int]] = []
    for idx, value in enumerate(points):
        x = int(left + idx * (plot_w / max(len(points) - 1, 1)))
        y = int(bottom - ((value - min_value) / spread) * (plot_h - 8))
        coords.append((x, y))
    baseline = bottom
    for idx in range(len(coords) - 1):
        x1, y1 = coords[idx]
        x2, y2 = coords[idx + 1]
        canvas.line(x1, y1, x2, y2, chart_color, 3)
        steps = max(abs(x2 - x1), 1)
        for step in range(steps + 1):
            ratio = step / steps
            px = int(x1 + (x2 - x1) * ratio)
            py = int(y1 + (y2 - y1) * ratio)
            canvas.line(px, py, px, baseline, _blend(chart_color, WHITE, 0.82))
    for x, y in coords:
        canvas.circle(x, y, 4, chart_color)
    return canvas.png_bytes()


def render_heatmap_png(
    matrix: list[list[float]],
    *,
    width: int = 520,
    height: int = 220,
    base_color: str = "#F59E0B",
) -> bytes:
    canvas = Canvas(width, height)
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    if not rows or not cols:
        return canvas.png_bytes()
    left = 28
    top = 20
    gap = 6
    cell_w = max(18, int((width - left * 2 - gap * (cols - 1)) / cols))
    cell_h = max(18, int((height - top * 2 - gap * (rows - 1)) / rows))
    max_value = max(max(row) for row in matrix) or 1
    base = _hex_to_rgb(base_color)
    for r, row in enumerate(matrix):
        for c, value in enumerate(row):
            strength = min(1.0, max(0.0, value / max_value))
            color = _blend(WHITE, base, 0.2 + strength * 0.8)
            x = left + c * (cell_w + gap)
            y = top + r * (cell_h + gap)
            canvas.rect(x, y, cell_w, cell_h, color)
    return canvas.png_bytes()


def _blend(color_a: Color, color_b: Color, ratio: float) -> Color:
    return tuple(int(color_a[idx] * ratio + color_b[idx] * (1 - ratio)) for idx in range(3))

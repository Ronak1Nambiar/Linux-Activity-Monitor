"""Scrolling area sparkline chart drawn with QPainter."""

from __future__ import annotations

from collections import deque

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class MiniChart(QWidget):
    """A lightweight scrolling area chart.

    Parameters
    ----------
    max_value:
        Fixed upper bound for scaling.  Ignored when *auto_scale* is True.
    color:
        Hex string for the line/fill colour.
    history_size:
        How many data points to retain (one per refresh tick).
    auto_scale:
        When True the y-axis scales to the max value in the current window.
    """

    def __init__(
        self,
        max_value: float = 100,
        color: str = "#4f8cff",
        history_size: int = 60,
        auto_scale: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.max_value = max_value
        self.base_color = QColor(color)
        self.auto_scale = auto_scale
        self._history: deque[float] = deque([0.0] * history_size, maxlen=history_size)
        self.setMinimumHeight(50)
        self.setMinimumWidth(80)

    def set_color(self, color: str) -> None:
        self.base_color = QColor(color)
        self.update()

    def add_value(self, value: float) -> None:
        self._history.append(float(value))
        self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        values = list(self._history)
        n = len(values)

        if n < 2:
            return

        # Determine vertical scale
        if self.auto_scale:
            top = max(values) if max(values) > 0 else 1.0
        else:
            top = self.max_value if self.max_value > 0 else 1.0

        pad_top = h * 0.05
        pad_bottom = h * 0.05
        chart_h = h - pad_top - pad_bottom
        step_x = w / (n - 1)

        def _y(v: float) -> float:
            return pad_top + chart_h * (1.0 - min(v, top) / top)

        points = [(_x * step_x, _y(v)) for _x, v in enumerate(values)]

        # Filled area
        path = QPainterPath()
        path.moveTo(0.0, float(h))
        path.lineTo(points[0][0], points[0][1])
        n_pts = len(points)
        for i in range(1, n_pts):
            x0, y0 = points[i - 1]
            x1, y1 = points[i]
            cp1x = x0 + (x1 - x0) / 3.0
            cp2x = x0 + 2.0 * (x1 - x0) / 3.0
            path.cubicTo(cp1x, y0, cp2x, y1, x1, y1)
        path.lineTo(float(w), float(h))
        path.closeSubpath()

        gradient = QLinearGradient(0, 0, 0, h)
        fill = QColor(self.base_color)
        fill.setAlpha(100)
        gradient.setColorAt(0.0, fill)
        transparent = QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 15)
        gradient.setColorAt(1.0, transparent)
        painter.fillPath(path, gradient)

        # Smooth line using cubic bezier curves
        line = QPainterPath()
        line.moveTo(points[0][0], points[0][1])
        n_pts = len(points)
        for i in range(1, n_pts):
            x0, y0 = points[i - 1]
            x1, y1 = points[i]
            # Control points at 1/3 and 2/3 of the x distance
            cp1x = x0 + (x1 - x0) / 3.0
            cp2x = x0 + 2.0 * (x1 - x0) / 3.0
            line.cubicTo(cp1x, y0, cp2x, y1, x1, y1)
        pen = QPen(self.base_color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(line)

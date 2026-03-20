"""Circular arc gauge drawn with QPainter."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class CircularGauge(QWidget):
    """Renders an arc-style percentage gauge.

    The arc spans 270 degrees (starting at 225 degrees, going clockwise).
    The centre shows the percentage value as text.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value: float = 0.0
        self.setMinimumSize(110, 110)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(100.0, float(value)))
        self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin = 10
        size = min(w, h) - margin * 2
        x = (w - size) / 2
        y = (h - size) / 2
        rect = QRectF(x, y, size, size)
        arc_width = max(8, size // 12)

        # Background arc
        bg_pen = QPen(QColor("#252840"), arc_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, int(225 * 16), int(-270 * 16))

        # Colour arc
        color = self._arc_color()
        fg_pen = QPen(QColor(color), arc_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(fg_pen)
        span = int(-270 * 16 * self._value / 100)
        painter.drawArc(rect, int(225 * 16), span)

        # Centre text
        painter.setPen(QColor("#e8eaf6"))
        font_size = max(11, int(size * 0.20))
        font = QFont("Inter, Sans Serif", font_size, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._value:.0f}%")

    def _arc_color(self) -> str:
        if self._value < 60:
            return "#4ade80"
        if self._value < 80:
            return "#fbbf24"
        return "#f87171"

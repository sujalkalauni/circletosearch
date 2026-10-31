from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import (
    Qt,
    QPoint,
    QRect,
    QRectF,
    pyqtSignal,
    QPropertyAnimation,
    QEasingCurve,
)
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QPainterPath,
    QLinearGradient,
)


class FloatingNavBar(QWidget):
    """Subtle Android-style navigation handle at the bottom edge of the screen."""

    triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered = False

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setCursor(Qt.PointingHandCursor)

        self.bar_width = 130
        self.bar_height = 8
        self.reposition()

    def reposition(self):
        screen = QApplication.primaryScreen().geometry()
        self.setFixedSize(self.bar_width + 20, self.bar_height + 12)
        x = (screen.width() - self.width()) // 2
        # Position at the very bottom edge above taskbar
        y = screen.height() - self.height() - 2
        self.move(x, y)

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.triggered.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(10, 4, self.bar_width, self.bar_height)

        if self.hovered:
            # Glowing Google rainbow gradient on hover
            grad = QLinearGradient(rect.topLeft(), rect.topRight())
            grad.setColorAt(0.0, QColor("#4285F4"))
            grad.setColorAt(0.33, QColor("#EA4335"))
            grad.setColorAt(0.66, QColor("#FBBC05"))
            grad.setColorAt(1.0, QColor("#34A853"))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
        else:
            # Subtle frosted white pill
            painter.setBrush(QBrush(QColor(255, 255, 255, 110)))
            painter.setPen(Qt.NoPen)

        painter.drawRoundedRect(
            rect, self.bar_height / 2.0, self.bar_height / 2.0
        )

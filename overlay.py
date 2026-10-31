import io
import math
import random
from PIL import Image

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import (
    Qt,
    QPoint,
    QRect,
    QRectF,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    pyqtSignal,
    QBuffer,
    QIODevice,
)
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QPixmap,
    QPainterPath,
    QFont,
    QCursor,
    QLinearGradient,
    QRadialGradient,
)

import sound
import ocr_engine
import search_engine
from hud import CircleToSearchToast, CircleToSearchActionSheet


class Particle:

    def __init__(self, x: float, y: float, color: QColor):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.5, 2.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.radius = random.uniform(2.0, 4.5)
        self.alpha = 240.0
        self.decay = random.uniform(10.0, 18.0)

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.alpha -= self.decay
        self.radius = max(0.5, self.radius * 0.95)
        return self.alpha > 0


class CircleToSearchOverlay(QWidget):
    """Full-screen translucent overlay capturing the desktop and drawing glowing lasso."""

    closed = pyqtSignal()

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.is_drawing = False
        self.points = []
        self.particles = []
        self.active_rect = None
        self.selection_done = False
        self.ripple_radius = 0
        self.ripple_center = QPoint()
        self.ripple_max = 280
        self.current_mouse_pos = QPoint()

        # Window properties
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.BypassWindowManagerHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        # Multi-monitor virtual desktop coverage
        desktop = QApplication.desktop()
        self.screen_geo = desktop.geometry()
        self.setGeometry(self.screen_geo)

        # Capture frozen desktop snapshot
        screen = QApplication.primaryScreen()
        self.snapshot = screen.grabWindow(0)

        # Particle & animation timer (60 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.on_anim_frame)
        self.anim_timer.start(16)

        # Start ripple animation from cursor
        self.ripple_center = QCursor.pos()
        self.ripple_radius = 5

        # Play sound cue
        sound.play_activate_sound(self.config.get("sound_effects", True))

    def on_anim_frame(self):
        need_repaint = False

        # Update ripple
        if self.ripple_radius < self.ripple_max:
            self.ripple_radius += 12
            need_repaint = True

        # Update particles
        alive_particles = []
        for p in self.particles:
            if p.update():
                alive_particles.append(p)
                need_repaint = True
        self.particles = alive_particles

        if self.is_drawing or need_repaint:
            self.update()

    def get_rainbow_color(self, t: float) -> QColor:
        """Return Google-styled glowing rainbow color for parameter t in [0, 1]."""
        # Blue -> Red -> Yellow -> Green -> Cyan
        colors = [
            QColor(66, 133, 244),  # #4285F4 (Google Blue)
            QColor(234, 67, 53),  # #EA4335 (Google Red)
            QColor(251, 188, 5),  # #FBBC05 (Google Yellow)
            QColor(52, 168, 83),  # #34A853 (Google Green)
            QColor(0, 229, 255),  # Electric Cyan
        ]
        pos = t * (len(colors) - 1)
        idx = int(pos)
        idx = min(idx, len(colors) - 2)
        frac = pos - idx
        c1, c2 = colors[idx], colors[idx + 1]
        r = int(c1.red() + frac * (c2.red() - c1.red()))
        g = int(c1.green() + frac * (c2.green() - c1.green()))
        b = int(c1.blue() + frac * (c2.blue() - c1.blue()))
        return QColor(r, g, b)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_drawing = True
            self.points = [event.pos()]
            self.spawn_sparkles(event.pos(), 6)
            self.update()
        elif event.button() == Qt.RightButton:
            self.close_and_dismiss()

    def mouseMoveEvent(self, event):
        self.current_mouse_pos = event.pos()
        if self.is_drawing:
            last_pt = self.points[-1]
            dist = math.hypot(
                event.pos().x() - last_pt.x(), event.pos().y() - last_pt.y()
            )
            if dist > 3.0:
                self.points.append(event.pos())
                self.spawn_sparkles(event.pos(), 3)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.is_drawing = False
            if len(self.points) < 4:
                # If too few points, ignore or cancel
                return

            # Compute bounding box
            xs = [p.x() for p in self.points]
            ys = [p.y() for p in self.points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            width = max_x - min_x
            height = max_y - min_y

            # Check minimum size
            if width < 12 or height < 12:
                return

            # Add padding
            padding = 10
            sel_rect = QRect(
                max(0, min_x - padding),
                max(0, min_y - padding),
                min(self.width() - (min_x - padding), width + padding * 2),
                min(self.height() - (min_y - padding), height + padding * 2),
            )

            self.active_rect = sel_rect
            self.selection_done = True
            sound.play_select_sound(self.config.get("sound_effects", True))
            self.update()

            # Execute selection after short delay for satisfying visual snap
            QTimer.singleShot(180, self.finish_selection)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_and_dismiss()
        else:
            super().keyPressEvent(event)

    def spawn_sparkles(self, pos: QPoint, count: int = 4):
        t = (
            len(self.points) / 50.0
            if self.points
            else random.random() % 1.0
        )
        base_color = self.get_rainbow_color(t % 1.0)
        for _ in range(count):
            self.particles.append(
                Particle(float(pos.x()), float(pos.y()), base_color)
            )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 1. Draw base captured desktop
        painter.drawPixmap(0, 0, self.snapshot)

        # 2. Draw frosted dark veil
        veil_color = QColor(10, 14, 22, 115)
        if self.selection_done and self.active_rect:
            # Highlight selected region: dim everything except active_rect
            path = QPainterPath()
            path.addRect(QRectF(self.rect()))
            selected_path = QPainterPath()
            selected_path.addRoundedRect(QRectF(self.active_rect), 16, 16)
            dim_path = path.subtracted(selected_path)
            painter.fillPath(dim_path, veil_color)

            # Draw glowing Google colored border around selected region
            pen_glow = QPen(QColor(66, 133, 244, 220), 4)
            painter.setPen(pen_glow)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.active_rect, 16, 16)
        else:
            painter.fillRect(self.rect(), veil_color)

        # 3. Draw initial expanding ripple
        if self.ripple_radius < self.ripple_max:
            progress = self.ripple_radius / float(self.ripple_max)
            alpha = int((1.0 - progress) * 160)
            ripple_grad = QRadialGradient(
                QPoint(self.ripple_center.x(), self.ripple_center.y()),
                float(self.ripple_radius),
            )
            ripple_grad.setColorAt(0.0, QColor(66, 133, 244, 0))
            ripple_grad.setColorAt(0.7, QColor(0, 229, 255, int(alpha * 0.4)))
            ripple_grad.setColorAt(1.0, QColor(66, 133, 244, alpha))
            painter.setPen(QPen(QColor(66, 133, 244, alpha), 3))
            painter.setBrush(QBrush(ripple_grad))
            painter.drawEllipse(self.ripple_center, self.ripple_radius, self.ripple_radius)

        # 4. Draw glowing Google rainbow lasso stroke
        if len(self.points) > 1:
            total_pts = len(self.points)
            for i in range(total_pts - 1):
                p1, p2 = self.points[i], self.points[i + 1]
                t = i / float(total_pts)
                col = self.get_rainbow_color(t)

                # Outer bloom halo
                col_outer = QColor(col.red(), col.green(), col.blue(), 35)
                painter.setPen(
                    QPen(col_outer, 16, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                )
                painter.drawLine(p1, p2)

                # Mid glowing halo
                col_mid = QColor(col.red(), col.green(), col.blue(), 130)
                painter.setPen(
                    QPen(col_mid, 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                )
                painter.drawLine(p1, p2)

                # Inner intense core
                col_core = QColor(255, 255, 255, 230)
                painter.setPen(
                    QPen(col_core, 3.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                )
                painter.drawLine(p1, p2)

        # 5. Draw drifting particles
        for p in self.particles:
            painter.setPen(Qt.NoPen)
            painter.setBrush(
                QBrush(
                    QColor(
                        p.color.red(),
                        p.color.green(),
                        p.color.blue(),
                        int(p.alpha),
                    )
                )
            )
            painter.drawEllipse(QPoint(int(p.x), int(p.y)), int(p.radius), int(p.radius))

        # 6. Bottom Search Bar Pill (Google Style)
        if not self.selection_done:
            self.paint_bottom_search_pill(painter)

    def paint_bottom_search_pill(self, painter: QPainter):
        bar_w = 460
        bar_h = 54
        bar_x = (self.width() - bar_w) // 2
        bar_y = self.height() - bar_h - 48

        pill_rect = QRect(bar_x, bar_y, bar_w, bar_h)

        # Glassmorphism dark pill
        painter.setPen(QPen(QColor(255, 255, 255, 38), 1))
        painter.setBrush(QBrush(QColor(26, 28, 33, 230)))
        painter.drawRoundedRect(pill_rect, 27, 27)

        # Google "G" / Lens colored icon on left
        icon_cx = bar_x + 30
        icon_cy = bar_y + 27
        icon_r = 13
        icon_rect = QRect(
            icon_cx - icon_r, icon_cy - icon_r, icon_r * 2, icon_r * 2
        )

        colors = [
            (QColor("#4285F4"), -40 * 16, 90 * 16),
            (QColor("#34A853"), 50 * 16, 90 * 16),
            (QColor("#FBBC05"), 140 * 16, 90 * 16),
            (QColor("#EA4335"), 230 * 16, 90 * 16),
        ]
        for c, st, sp in colors:
            painter.setPen(QPen(c, 3))
            painter.drawArc(icon_rect, st, sp)

        # Central text hint
        painter.setPen(QColor("#E2E8F0"))
        font = QFont("Segoe UI", 11)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(
            QRect(bar_x + 56, bar_y, bar_w - 150, bar_h),
            Qt.AlignVCenter | Qt.AlignLeft,
            "Circle, scribble, or tap to search",
        )

        # Hotkey badge on right
        badge_w = 72
        badge_h = 24
        badge_x = bar_x + bar_w - badge_w - 16
        badge_y = bar_y + (bar_h - badge_h) // 2
        badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)
        painter.setPen(QPen(QColor(255, 255, 255, 25), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
        painter.drawRoundedRect(badge_rect, 6, 6)

        font_badge = QFont("Segoe UI", 9)
        painter.setFont(font_badge)
        painter.setPen(QColor("#9AA0A6"))
        painter.drawText(badge_rect, Qt.AlignCenter, "Esc to exit")

    def finish_selection(self):
        """Extract cropped region and trigger Google Lens & OCR."""
        if not self.active_rect:
            self.close_and_dismiss()
            return

        cropped_pixmap = self.snapshot.copy(self.active_rect)

        # Convert QPixmap to PIL Image
        buf = QBuffer()
        buf.open(QIODevice.ReadWrite)
        cropped_pixmap.save(buf, "PNG")
        pil_image = Image.open(io.BytesIO(buf.data()))

        self.anim_timer.stop()
        self.close()
        self.closed.emit()

        instant_lens = self.config.get("instant_lens", True)
        auto_copy_ocr = self.config.get("auto_copy_ocr", False)

        if instant_lens:
            # 1. Show sleek HUD Toast Pill
            toast = CircleToSearchToast(
                cropped_pixmap, initial_status="Opening Google Lens..."
            )
            toast.show_centered()
            self._toast_ref = toast

            # 2. Upload to Google Lens and open browser immediately!
            search_engine.open_google_lens_async(pil_image)

            # 3. Simultaneously run fast offline OCR in background
            def on_ocr_done(text: str):
                if text:
                    toast.update_with_ocr_text(text)
                    if auto_copy_ocr:
                        QApplication.clipboard().setText(text)

            ocr_engine.extract_text_async(pil_image, on_ocr_done)
        else:
            # Show full Action Sheet first
            def on_ocr_sheet(text: str):
                sheet = CircleToSearchActionSheet(
                    cropped_pixmap, pil_image, detected_text=text
                )
                self._sheet_ref = sheet

            ocr_engine.extract_text_async(pil_image, on_ocr_sheet)

    def close_and_dismiss(self):
        self.anim_timer.stop()
        self.close()
        self.closed.emit()

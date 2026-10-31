import io
import os
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QTextEdit,
    QApplication,
    QFileDialog,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
)
from PyQt5.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QColor,
    QFont,
    QIcon,
    QPixmap,
    QPainter,
    QPainterPath,
    QPen,
)
import search_engine


class ModernPillButton(QPushButton):

    def __init__(self, text: str, primary: bool = False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(36)
        self.update_style()

    def update_style(self):
        if self.primary:
            self.setStyleSheet(
                """
                QPushButton {
                    background-color: #4285F4;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: bold;
                    border-radius: 18px;
                    padding: 0 18px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #5393FF;
                }
                QPushButton:pressed {
                    background-color: #3367D6;
                }
            """
            )
        else:
            self.setStyleSheet(
                """
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.10);
                    color: #E2E8F0;
                    font-size: 13px;
                    font-weight: 500;
                    border-radius: 18px;
                    padding: 0 14px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.20);
                    color: #FFFFFF;
                    border-color: rgba(255, 255, 255, 0.30);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.08);
                }
            """
            )


class CircleToSearchToast(QWidget):
    """Floating Android-style HUD Pill that appears after circling."""

    dismissed = pyqtSignal()

    def __init__(
        self,
        cropped_pixmap: QPixmap,
        initial_status: str = "Opening Google Lens...",
        parent=None,
    ):
        super().__init__(parent)
        self.cropped_pixmap = cropped_pixmap
        self.detected_text = ""
        self.lens_url = None

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self.setup_ui(initial_status)
        self.setup_shadow()
        self.setup_animation()

        # Auto-dismiss timer after 6 seconds if not hovered
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.fade_out_and_close)
        self.dismiss_timer.start(6000)

    def setup_ui(self, initial_status: str):
        self.container = QWidget(self)
        self.container.setStyleSheet(
            """
            QWidget#Container {
                background-color: rgba(26, 28, 33, 0.94);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 22px;
            }
        """
        )
        self.container.setObjectName("Container")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.addWidget(self.container)

        self.pill_layout = QHBoxLayout(self.container)
        self.pill_layout.setContentsMargins(16, 8, 16, 8)
        self.pill_layout.setSpacing(12)

        # Google 4-color glowing indicator / Lens Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        self.render_lens_icon()
        self.pill_layout.addWidget(self.icon_label)

        # Status text / Text preview
        self.text_label = QLabel(initial_status)
        self.text_label.setStyleSheet(
            """
            color: #F1F3F4;
            font-size: 13px;
            font-weight: 500;
        """
        )
        self.pill_layout.addWidget(self.text_label)

        # Action Buttons container
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(8)
        self.pill_layout.addLayout(self.actions_layout)

        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                color: #9AA0A6;
                font-size: 14px;
                border-radius: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
                color: #FFFFFF;
            }
        """
        )
        self.close_btn.clicked.connect(self.fade_out_and_close)
        self.pill_layout.addWidget(self.close_btn)

    def render_lens_icon(self):
        pix = QPixmap(28, 28)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = pix.rect().adjusted(2, 2, -2, -2)
        pen_width = 3.5

        colors = [
            (QColor("#4285F4"), -40 * 16, 90 * 16),
            (QColor("#34A853"), 50 * 16, 90 * 16),
            (QColor("#FBBC05"), 140 * 16, 90 * 16),
            (QColor("#EA4335"), 230 * 16, 90 * 16),
        ]
        for color, start, span in colors:
            painter.setPen(QPen(color, pen_width))
            painter.drawArc(rect, start, span)

        painter.setBrush(QColor("#4285F4"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(rect.center(), 3, 3)

        painter.end()
        self.icon_label.setPixmap(pix)

    def update_with_ocr_text(self, text: str):
        self.detected_text = text.strip()
        if not self.detected_text:
            return

        # Show truncated snippet
        snippet = (
            self.detected_text[:38] + "..."
            if len(self.detected_text) > 38
            else self.detected_text
        )
        self.text_label.setText(f'📝 "{snippet}"')

        # Add Copy Text button
        copy_btn = ModernPillButton("📋 Copy Text")
        copy_btn.clicked.connect(lambda: self.on_copy_text(copy_btn))
        self.actions_layout.addWidget(copy_btn)

        # Add Translate button
        trans_btn = ModernPillButton("🔤 Translate")
        trans_btn.clicked.connect(
            lambda: search_engine.translate_google_text(self.detected_text)
        )
        self.actions_layout.addWidget(trans_btn)

        self.adjustSize()
        self.recenter_on_screen()
        self.dismiss_timer.start(6500)

    def on_copy_text(self, btn: ModernPillButton):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.detected_text)
        btn.setText("✓ Copied!")
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: #34A853;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                border-radius: 17px;
                padding: 0 14px;
                border: none;
            }
        """
        )

    def setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 6)
        self.container.setGraphicsEffect(shadow)

    def setup_animation(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(240)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

    def show_centered(self):
        self.adjustSize()
        self.recenter_on_screen()
        self.show()

    def recenter_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 50
        self.move(x, y)

    def enterEvent(self, event):
        self.dismiss_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.dismiss_timer.start(4500)
        super().leaveEvent(event)

    def fade_out_and_close(self):
        self.anim_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_out.setDuration(220)
        self.anim_out.setStartValue(self.opacity_effect.opacity())
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.InCubic)
        self.anim_out.finished.connect(self.close)
        self.anim_out.finished.connect(self.dismissed.emit)
        self.anim_out.start()


class CircleToSearchActionSheet(QWidget):
    """Full Android Material-style Action Sheet with Image preview, Google Lens, and OCR text."""

    def __init__(
        self, cropped_pixmap: QPixmap, pil_image, detected_text: str = ""
    ):
        super().__init__()
        self.cropped_pixmap = cropped_pixmap
        self.pil_image = pil_image
        self.detected_text = detected_text

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setup_ui()
        self.setup_shadow()
        self.show_centered()

    def setup_ui(self):
        self.container = QWidget(self)
        self.container.setFixedWidth(460)
        self.container.setStyleSheet(
            """
            QWidget#SheetContainer {
                background-color: #1E2024;
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 24px;
            }
        """
        )
        self.container.setObjectName("SheetContainer")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header with drag bar / title
        header_layout = QHBoxLayout()
        title_label = QLabel("Circle to Search")
        title_label.setStyleSheet(
            "color: #FFFFFF; font-size: 16px; font-weight: bold;"
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #9AA0A6;
                font-size: 14px;
                border-radius: 14px;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
                color: #FFFFFF;
            }
        """
        )
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)

        # Preview Thumbnail
        preview_label = QLabel()
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setFixedHeight(140)
        preview_label.setStyleSheet(
            """
            background-color: #131416;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        """
        )
        scaled_pix = self.cropped_pixmap.scaled(
            420, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        preview_label.setPixmap(scaled_pix)
        layout.addWidget(preview_label)

        # Primary Action: Search with Google Lens
        self.lens_btn = ModernPillButton(
            "🔍 Search with Google Lens", primary=True
        )
        self.lens_btn.setFixedHeight(40)
        self.lens_btn.clicked.connect(self.on_open_lens)
        layout.addWidget(self.lens_btn)

        # OCR Section (if text is found)
        if self.detected_text:
            text_header = QLabel("Extracted Text:")
            text_header.setStyleSheet(
                "color: #9AA0A6; font-size: 12px; font-weight: bold;"
            )
            layout.addWidget(text_header)

            self.text_edit = QTextEdit()
            self.text_edit.setPlainText(self.detected_text)
            self.text_edit.setFixedHeight(70)
            self.text_edit.setStyleSheet(
                """
                QTextEdit {
                    background-color: #131416;
                    color: #E2E8F0;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    padding: 8px;
                    font-size: 12px;
                }
            """
            )
            layout.addWidget(self.text_edit)

            # OCR Actions row
            ocr_row = QHBoxLayout()
            self.copy_btn = ModernPillButton("📋 Copy Text")
            self.copy_btn.clicked.connect(self.on_copy)
            ocr_row.addWidget(self.copy_btn)

            search_btn = ModernPillButton("🌐 Search Text")
            search_btn.clicked.connect(
                lambda: search_engine.search_google_text(self.detected_text)
            )
            ocr_row.addWidget(search_btn)

            trans_btn = ModernPillButton("🔤 Translate")
            trans_btn.clicked.connect(
                lambda: search_engine.translate_google_text(self.detected_text)
            )
            ocr_row.addWidget(trans_btn)
            layout.addLayout(ocr_row)

        # Secondary Actions row
        sec_row = QHBoxLayout()
        copy_img_btn = ModernPillButton("🖼️ Copy Image")
        copy_img_btn.clicked.connect(self.on_copy_image)
        sec_row.addWidget(copy_img_btn)

        save_btn = ModernPillButton("💾 Save Image")
        save_btn.clicked.connect(self.on_save_image)
        sec_row.addWidget(save_btn)
        layout.addLayout(sec_row)

    def on_open_lens(self):
        self.lens_btn.setText("Opening Google Lens...")
        search_engine.open_google_lens_async(self.pil_image)
        QTimer.singleShot(1500, self.close)

    def on_copy(self):
        txt = (
            self.text_edit.toPlainText()
            if hasattr(self, "text_edit")
            else self.detected_text
        )
        QApplication.clipboard().setText(txt)
        self.copy_btn.setText("✓ Copied!")

    def on_copy_image(self):
        QApplication.clipboard().setPixmap(self.cropped_pixmap)

    def on_save_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Cropped Image", "circle_search.png", "PNG (*.png)"
        )
        if path:
            self.cropped_pixmap.save(path, "PNG")

    def setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

    def show_centered(self):
        self.adjustSize()
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        self.show()

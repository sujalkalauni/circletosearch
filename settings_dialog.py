import os
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QApplication,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap

import config


class ModernSettingsDialog(QDialog):
    """Sleek dark-mode settings dialog for Circle to Search."""

    config_changed = pyqtSignal(dict)
    test_triggered = pyqtSignal()

    def __init__(self, current_config: dict, parent=None):
        super().__init__(parent)
        self.config = dict(current_config)

        self.setWindowTitle("Circle to Search - Settings")
        self.setFixedSize(520, 580)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets", "app_icon.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        self.setStyleSheet(
            """
            QDialog {
                background-color: #17181C;
                color: #E2E8F0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #E2E8F0;
            }
            QGroupBox {
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                margin-top: 18px;
                padding-top: 14px;
                font-size: 13px;
                font-weight: bold;
                color: #4285F4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }
            QCheckBox {
                color: #CBD5E1;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.25);
                background-color: #202227;
            }
            QCheckBox::indicator:checked {
                background-color: #4285F4;
                border-color: #4285F4;
            }
            QComboBox {
                background-color: #202227;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #202227;
                color: #FFFFFF;
                selection-background-color: #4285F4;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
        """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header banner
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        icon_label = QLabel()
        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets", "app_icon.png"
        )
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(
                44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            icon_label.setPixmap(pix)
        header_layout.addWidget(icon_label)

        title_vbox = QVBoxLayout()
        title_lbl = QLabel("Circle to Search")
        title_lbl.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #FFFFFF;"
        )
        sub_lbl = QLabel("Android-style screen search for Windows 10/11")
        sub_lbl.setStyleSheet("font-size: 12px; color: #9AA0A6;")
        title_vbox.addWidget(title_lbl)
        title_vbox.addWidget(sub_lbl)
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # 1. Activation & Hotkey Group
        hotkey_group = QGroupBox("Activation & Trigger")
        hotkey_layout = QVBoxLayout(hotkey_group)
        hotkey_layout.setSpacing(10)

        combo_row = QHBoxLayout()
        combo_row.addWidget(QLabel("Global Keyboard Shortcut:"))
        self.hotkey_combo = QComboBox()
        self.hotkey_combo.addItems(
            [
                "Alt + C (Recommended)",
                "Ctrl + Alt + S",
                "Ctrl + Space",
                "Alt + Space",
                "Ctrl + Shift + S",
            ]
        )
        combo_row.addWidget(self.hotkey_combo)
        hotkey_layout.addLayout(combo_row)

        self.handle_cb = QCheckBox(
            "Show floating Android gesture bar at bottom of screen"
        )
        hotkey_layout.addWidget(self.handle_cb)

        main_layout.addWidget(hotkey_group)

        # 2. Search Behavior Group
        search_group = QGroupBox("Search & Recognition Behavior")
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(10)

        self.instant_cb = QCheckBox(
            "Instant Google Lens (Immediately search and open browser on circle)"
        )
        search_layout.addWidget(self.instant_cb)

        self.auto_copy_cb = QCheckBox(
            "Auto-copy offline OCR text to clipboard when detected"
        )
        search_layout.addWidget(self.auto_copy_cb)

        self.sounds_cb = QCheckBox(
            "Enable futuristic activation and selection sound effects"
        )
        search_layout.addWidget(self.sounds_cb)

        main_layout.addWidget(search_group)

        # 3. System Integration Group
        sys_group = QGroupBox("System & Startup")
        sys_layout = QVBoxLayout(sys_group)
        sys_layout.setSpacing(10)

        self.startup_cb = QCheckBox(
            "Start Circle to Search automatically with Windows"
        )
        sys_layout.addWidget(self.startup_cb)

        main_layout.addWidget(sys_group)

        main_layout.addStretch()

        # Footer Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.test_btn = QPushButton("🔍 Try Circle to Search Now")
        self.test_btn.setFixedHeight(38)
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self.test_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #E2E8F0;
                font-size: 13px;
                font-weight: 500;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.16);
            }
        """
        )
        self.test_btn.clicked.connect(self.on_test_clicked)
        btn_layout.addWidget(self.test_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(38)
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                color: #9AA0A6;
                font-size: 13px;
                border: none;
                padding: 0 16px;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """
        )
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save & Apply")
        save_btn.setFixedHeight(38)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4285F4;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #5393FF;
            }
        """
        )
        save_btn.clicked.connect(self.on_save)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)

    def load_values(self):
        # Hotkey mapping
        key = self.config.get("hotkey", "alt+c").lower()
        if "alt+c" in key:
            self.hotkey_combo.setCurrentIndex(0)
        elif "ctrl+alt+s" in key:
            self.hotkey_combo.setCurrentIndex(1)
        elif "ctrl+space" in key:
            self.hotkey_combo.setCurrentIndex(2)
        elif "alt+space" in key:
            self.hotkey_combo.setCurrentIndex(3)
        elif "ctrl+shift+s" in key:
            self.hotkey_combo.setCurrentIndex(4)

        self.handle_cb.setChecked(self.config.get("floating_handle", True))
        self.instant_cb.setChecked(self.config.get("instant_lens", True))
        self.auto_copy_cb.setChecked(self.config.get("auto_copy_ocr", False))
        self.sounds_cb.setChecked(self.config.get("sound_effects", True))
        self.startup_cb.setChecked(
            self.config.get("start_with_windows", False)
        )

    def on_test_clicked(self):
        self.hide()
        self.test_triggered.emit()

    def on_save(self):
        idx = self.hotkey_combo.currentIndex()
        hotkeys = [
            "alt+c",
            "ctrl+alt+s",
            "ctrl+space",
            "alt+space",
            "ctrl+shift+s",
        ]
        chosen_hotkey = hotkeys[idx] if idx < len(hotkeys) else "alt+c"

        self.config["hotkey"] = chosen_hotkey
        self.config["floating_handle"] = self.handle_cb.isChecked()
        self.config["instant_lens"] = self.instant_cb.isChecked()
        self.config["auto_copy_ocr"] = self.auto_copy_cb.isChecked()
        self.config["sound_effects"] = self.sounds_cb.isChecked()
        self.config["start_with_windows"] = self.startup_cb.isChecked()

        config.save_config(self.config)
        self.config_changed.emit(self.config)
        self.accept()

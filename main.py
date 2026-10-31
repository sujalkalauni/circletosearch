import os
import sys
import ctypes

# DPI awareness for crisp rendering on Windows 10/11
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# When running under pythonw.exe, sys.stdout and sys.stderr are None
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")


import keyboard
from PyQt5.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon

import config
from overlay import CircleToSearchOverlay
from floating_bar import FloatingNavBar
from settings_dialog import ModernSettingsDialog


class HotkeySignalEmitter(QObject):
    hotkey_pressed = pyqtSignal()


class CircleToSearchApp(QObject):

    def __init__(self, q_app: QApplication):
        super().__init__()
        self.app = q_app
        self.config = config.load_config()
        self.overlay = None
        self.settings_dialog = None
        self.floating_bar = None

        # Cross-thread signal for global hotkey
        self.signal_emitter = HotkeySignalEmitter()
        self.signal_emitter.hotkey_pressed.connect(self.trigger_search)

        self.assets_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets"
        )
        self.icon_path = os.path.join(self.assets_dir, "tray_icon.png")

        self.setup_tray()
        self.setup_floating_bar()
        self.register_global_hotkey()

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        if os.path.exists(self.icon_path):
            self.tray.setIcon(QIcon(self.icon_path))
        else:
            self.tray.setIcon(
                self.app.style().standardIcon(
                    self.app.style().SP_ComputerIcon
                )
            )

        hotkey_name = self.config.get("hotkey", "alt+c").upper()
        self.tray.setToolTip(f"Circle to Search for Windows ({hotkey_name})")

        # Context Menu
        menu = QMenu()
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #1E2024;
                color: #E2E8F0;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 7px 24px;
                border-radius: 4px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #4285F4;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.1);
                margin: 4px 8px;
            }
        """
        )

        trigger_action = QAction(
            f"🔍 Circle to Search ({hotkey_name})", self
        )
        trigger_action.triggered.connect(self.trigger_search)
        menu.addAction(trigger_action)

        menu.addSeparator()

        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)

        menu.addSeparator()

        exit_action = QAction("🚪 Exit", self)
        exit_action.triggered.connect(self.quit_app)
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
        ):
            self.trigger_search()

    def setup_floating_bar(self):
        if self.config.get("floating_handle", True):
            if not self.floating_bar:
                self.floating_bar = FloatingNavBar()
                self.floating_bar.triggered.connect(self.trigger_search)
            self.floating_bar.show()
        else:
            if self.floating_bar:
                self.floating_bar.hide()

    def register_global_hotkey(self):
        try:
            keyboard.clear_all_hotkeys()
            hotkey = self.config.get("hotkey", "alt+c")

            def _on_press():
                self.signal_emitter.hotkey_pressed.emit()

            keyboard.add_hotkey(hotkey, _on_press)
            print(f"Registered global hotkey: {hotkey}")
        except Exception as e:
            print(f"Error registering hotkey: {e}")

    def trigger_search(self):
        """Freeze screen and show Circle to Search overlay."""
        if self.overlay and self.overlay.isVisible():
            return  # Already open

        # Hide floating bar during screenshot
        if self.floating_bar:
            self.floating_bar.hide()

        # Slight delay to ensure clean frame capture
        QTimer.singleShot(40, self._show_overlay_window)

    def _show_overlay_window(self):
        self.overlay = CircleToSearchOverlay(self.config)
        self.overlay.closed.connect(self._on_overlay_closed)
        self.overlay.show()

    def _on_overlay_closed(self):
        self.overlay = None
        # Restore floating bar if enabled
        if self.config.get("floating_handle", True) and self.floating_bar:
            self.floating_bar.show()

    def open_settings(self):
        if not self.settings_dialog:
            self.settings_dialog = ModernSettingsDialog(self.config)
            self.settings_dialog.config_changed.connect(self.on_config_updated)
            self.settings_dialog.test_triggered.connect(self.trigger_search)
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def on_config_updated(self, new_config: dict):
        self.config = new_config
        hotkey_name = self.config.get("hotkey", "alt+c").upper()
        self.tray.setToolTip(f"Circle to Search for Windows ({hotkey_name})")
        self.setup_floating_bar()
        self.register_global_hotkey()

    def show_about(self):
        msg = QMessageBox()
        msg.setWindowTitle("About Circle to Search")
        msg.setText("<h3>Circle to Search for Windows</h3>")
        msg.setInformativeText(
            "An Android-inspired screen search tool for Windows 10/11.<br><br>"
            "• <b>Circle, scribble, or tap</b> any part of your screen.<br>"
            "• <b>Google Lens</b> visual search integration.<br>"
            "• <b>Windows Native Offline OCR</b> for instant text extraction & translation.<br>"
            "• Glowing Google rainbow lasso with particle trail animations.<br><br>"
            f"Current Hotkey: <b>{self.config.get('hotkey', 'alt+c').upper()}</b>"
        )
        if os.path.exists(self.icon_path):
            msg.setWindowIcon(QIcon(self.icon_path))
        msg.exec_()

    def quit_app(self):
        try:
            keyboard.clear_all_hotkeys()
        except Exception:
            pass
        self.tray.hide()
        self.app.quit()


def check_single_instance() -> bool:
    """Ensure only one instance runs at a time using Windows Mutex."""
    mutex_name = "CircleToSearch_Windows_Mutex"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183
    if last_error == ERROR_ALREADY_EXISTS:
        return False
    # Store handle so it is not garbage collected
    check_single_instance._mutex = mutex
    return True


def main():
    if not check_single_instance():
        print("Circle to Search is already running.")
        sys.exit(0)

    # Enable High DPI pixmaps
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "app_icon.png"
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    circle_app = CircleToSearchApp(app)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

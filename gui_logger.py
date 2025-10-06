"""
GUI Logger - Bridge between Python's logging system and PyQt GUI (PyQt5 or PySide6)
"""

import logging

# --- Compatibility Layer: supports PyQt5 and PySide6 seamlessly ---
try:
    from PyQt5.QtCore import QObject, pyqtSignal
    from PyQt5.QtWidgets import QTextEdit
    from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat
except ImportError:
    from PySide6.QtCore import QObject, Signal as pyqtSignal
    from PySide6.QtWidgets import QTextEdit
    from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat


class QTextEditLogger(logging.Handler, QObject):
    """Custom logging handler that emits log messages safely to a PyQt GUI."""

    log_signal = pyqtSignal(str, str)  # (message, level_name)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

        # Optional color reference (not directly used here)
        self.colors = {
            'DEBUG': '#95a5a6',     # Gray
            'INFO': '#27ae60',      # Green
            'WARNING': '#f39c12',   # Orange
            'ERROR': '#e74c3c',     # Red
            'CRITICAL': '#c0392b'   # Dark Red
        }

    def emit(self, record):
        """Safely emit a log record to the GUI via signal."""
        try:
            formatted_message = self.format(record)
            self.log_signal.emit(formatted_message, record.levelname)
        except Exception as e:
            print(f"[QTextEditLogger] Logging handler error: {e}")
            self.handleError(record)


class LogViewer(QTextEdit):
    """Enhanced QTextEdit for displaying color-coded logs efficiently."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

        self.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                border: 1px solid #34495e;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        # Performance and memory management settings
        self.max_lines = 1000
        self.cleanup_threshold = 100

        # Color mapping per log level
        self.colors = {
            'DEBUG': QColor('#95a5a6'),
            'INFO': QColor('#27ae60'),
            'WARNING': QColor('#f39c12'),
            'ERROR': QColor('#e74c3c'),
            'CRITICAL': QColor('#c0392b')
        }

    def append_log(self, message: str, level: str):
        """Append a log message to the viewer with color-coding."""
        try:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)

            color = self.colors.get(level, QColor('#ecf0f1'))  # Default white
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            cursor.setCharFormat(fmt)

            cursor.insertText(f"{message}\n")

            # Auto-scroll and manage memory
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            self._limit_line_count()

        except Exception as e:
            print(f"[LogViewer] Failed to append log: {e}")

    def _limit_line_count(self):
        """Trim old log lines when exceeding max_lines."""
        document = self.document()
        if document.blockCount() > self.max_lines:
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.Start)
            for _ in range(self.cleanup_threshold):
                if cursor.atEnd():
                    break
                cursor.select(QTextCursor.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # Remove newline

    def clear_logs(self):
        """Clear all log entries."""
        self.clear()
        self.append_log("Log viewer cleared successfully", "INFO")


def setup_gui_logging(log_viewer: LogViewer) -> QTextEditLogger:
    """
    Configure Python's logging to output to a LogViewer instance.

    Args:
        log_viewer (LogViewer): The target widget for displaying logs.

    Returns:
        QTextEditLogger: Configured logging handler.
    """
    gui_handler = QTextEditLogger()
    gui_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)-8s - %(message)s',
        datefmt='%H:%M:%S'
    )
    gui_handler.setFormatter(formatter)

    gui_handler.log_signal.connect(log_viewer.append_log)

    root_logger = logging.getLogger()
    root_logger.addHandler(gui_handler)

    return gui_handler


def remove_gui_logging(handler: QTextEditLogger):
    """Remove the GUI logging handler cleanly."""
    try:
        logging.getLogger().removeHandler(handler)
    except Exception as e:
        print(f"[remove_gui_logging] Error removing handler: {e}")


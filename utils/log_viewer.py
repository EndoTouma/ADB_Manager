import logging
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QHBoxLayout, QLineEdit, QPushButton


class LogViewerDialog(QDialog):
    def __init__(self, log_text, parent=None):
        super().__init__(parent)
        self.prev_button = None
        self.next_button = None
        self.filter_button = None
        self.clear_filter_button = None
        self.search_button = None
        self.search_input = None
        self.log_viewer = None
        self.highlighter = None
        self.setWindowTitle("Log Viewer")
        self.setMinimumSize(800, 600)

        self.log_text = log_text
        self.filtered_log_text = log_text
        self.highlight_text = ""
        self.highlight_positions = []
        self.current_highlight_index = -1

        self.init_ui()
        self.update_button_states()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.log_viewer = QTextEdit(self)
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setPlainText(self.log_text)
        self.highlighter = LogHighlighter(self.log_viewer.document())
        layout.addWidget(self.log_viewer)

        search_layout = QHBoxLayout()

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.update_button_states)
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_text)
        search_layout.addWidget(self.search_button)

        self.filter_button = QPushButton("Filter")
        self.filter_button.clicked.connect(self.filter_text)
        search_layout.addWidget(self.filter_button)

        self.clear_filter_button = QPushButton("Clear Filter")
        self.clear_filter_button.clicked.connect(self.clear_filter)
        search_layout.addWidget(self.clear_filter_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.find_next)
        search_layout.addWidget(self.next_button)

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.find_prev)
        search_layout.addWidget(self.prev_button)

        layout.addLayout(search_layout)

    def update_button_states(self):
        has_text = bool(self.search_input.text().strip())
        self.search_button.setEnabled(has_text)
        self.filter_button.setEnabled(has_text)
        self.clear_filter_button.setEnabled(has_text)
        self.next_button.setEnabled(False)
        self.prev_button.setEnabled(False)

    def search_text(self):
        self.highlight_text = self.search_input.text().strip()
        if not self.highlight_text:
            logging.debug('Search input is empty.')
            return

        self.log_viewer.moveCursor(QTextCursor.MoveOperation.Start)
        self.highlight_positions = []
        self.current_highlight_index = -1
        self.find_all()
        if self.highlight_positions:
            self.current_highlight_index = 0
            self.move_cursor_to_highlight()
            self.next_button.setEnabled(True)
            self.prev_button.setEnabled(True)
            logging.debug(f'Found positions: {self.highlight_positions}')
        else:
            logging.debug('No matches found.')

    def filter_text(self):
        search_text = self.search_input.text().strip()
        if search_text:
            self.filtered_log_text = '\n'.join(
                line for line in self.log_text.split('\n') if search_text in line)
            self.log_viewer.setPlainText(self.filtered_log_text)
        else:
            self.log_viewer.setPlainText(self.log_text)

    def clear_filter(self):
        self.log_viewer.setPlainText(self.log_text)
        self.search_input.clear()
        self.update_button_states()

    def find_all(self):
        self.highlight_positions = []
        document = self.log_viewer.document()
        cursor = QTextCursor(document)

        while True:
            cursor = document.find(self.highlight_text, cursor)
            if cursor.isNull():
                break
            self.highlight_positions.append(cursor.position())

        self.highlight_search_results()

    def find_next(self):
        if not self.highlight_positions:
            logging.debug('No highlight positions available for "Next".')
            return
        self.current_highlight_index = (self.current_highlight_index + 1) % len(self.highlight_positions)
        self.move_cursor_to_highlight()

    def find_prev(self):
        if not self.highlight_positions:
            logging.debug('No highlight positions available for "Previous".')
            return
        self.current_highlight_index = (self.current_highlight_index - 1) % len(self.highlight_positions)
        self.move_cursor_to_highlight()

    def move_cursor_to_highlight(self):
        if not self.highlight_positions:
            logging.debug('No highlight positions to move to.')
            return

        cursor = self.log_viewer.textCursor()
        position = self.highlight_positions[self.current_highlight_index]
        cursor.setPosition(position - len(self.highlight_text), QTextCursor.MoveMode.MoveAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(self.highlight_text))
        self.log_viewer.setTextCursor(cursor)
        self.log_viewer.ensureCursorVisible()

    def highlight_search_results(self):
        extra_selections = []
        cursor = QTextCursor(self.log_viewer.document())
        format = QTextCharFormat()
        format.setBackground(QColor(Qt.GlobalColor.yellow))

        for pos in self.highlight_positions:
            cursor.setPosition(pos - len(self.highlight_text), QTextCursor.MoveMode.MoveAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(self.highlight_text))

            extra_selection = QTextEdit.ExtraSelection()
            extra_selection.cursor = cursor
            extra_selection.format = format
            extra_selections.append(extra_selection)

        self.log_viewer.setExtraSelections(extra_selections)


class LogHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        timestamp_format = QTextCharFormat()
        self.highlighting_rules.append(
            (QRegularExpression("\\b\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\.\\d{3}\\b"), timestamp_format))

        log_level_format = QTextCharFormat()
        log_levels = ["D", "I", "W", "E", "F", "V"]
        for level in log_levels:
            self.highlighting_rules.append((QRegularExpression("\\b" + level + "\\b(?=\\s)"), log_level_format))

        message_format = QTextCharFormat()
        self.highlighting_rules.append((QRegularExpression(":.*"), message_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            match_iterator = expression.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


def run_log_viewer(log_text):
    viewer = LogViewerDialog(log_text)
    viewer.exec()

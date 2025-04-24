import sys
import random
import itertools
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QGridLayout, QLabel, QMessageBox, QLineEdit, QHBoxLayout
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QTimer


class StartWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tęczowe Trójki — Start")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Podaj wartość n (liczba cyfr na planszy = 3n):")
        self.layout.addWidget(self.label)

        self.input = QLineEdit()
        self.input.setPlaceholderText("np. 2")
        self.layout.addWidget(self.input)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_game)
        self.layout.addWidget(self.start_button)

    def start_game(self):
        try:
            n = int(self.input.text())
            if n < 1:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Proszę podać poprawną liczbę całkowitą większą od zera.")
            return

        self.hide()
        self.game_window = RainbowTripletsGame(n)
        self.game_window.show()


class RainbowTripletsGame(QWidget):
    def __init__(self, n=2):
        super().__init__()
        self.n = n
        self.size = 3 * n
        self.board = [None] * (self.size + 1)
        self.current_turn = 1
        self.buttons = []

        self.setWindowTitle("Tęczowe Trójki")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Tęczowe Trójki — Twój ruch")
        self.layout.addWidget(self.label)

        self.grid = QGridLayout()
        self.layout.addLayout(self.grid)

        for i in range(1, self.size + 1):
            btn = QPushButton(str(i))
            btn.setFixedSize(50, 50)
            btn.clicked.connect(lambda _, i=i: self.player_move(i))
            self.buttons.append(btn)
            self.grid.addWidget(btn, (i - 1) // 10, (i - 1) % 10)

    def color(self, turn):
        return ['N', 'Z', 'C'][turn % 3]

    def color_to_qcolor(self, color):
        return {
            'Z': QColor('#2ecc71'),
            'C': QColor('#e74c3c'),
            'N': QColor('#3498db')
        }[color]

    def is_valid(self, i):
        return self.board[i] is None

    def set_move(self, i):
        color_code = self.color(self.current_turn)
        self.board[i] = color_code
        button = self.buttons[i - 1]
        button.setStyleSheet(f"background-color: {self.color_to_qcolor(color_code).name()}")
        button.setEnabled(False)
        self.current_turn += 1

    def player_move(self, i):
        if not self.is_valid(i):
            return

        self.set_move(i)

        if self.check_rainbow_triplet():
            self.end_game("Przegrana", "Utworzyłeś tęczowy ciąg – przegrywasz!")
            return

        self.label.setText("Tęczowe Trójki — Ruch komputera")
        QTimer.singleShot(1500, self.computer_move)

    def computer_move(self):
        available = [i for i in range(1, self.size + 1) if self.board[i] is None]
        if not available:
            self.end_game("Remis", "Brak dostępnych ruchów.")
            return

        choice = random.choice(available)
        self.set_move(choice)

        if self.check_rainbow_triplet():
            self.end_game("Wygrana", "Komputer utworzył tęczowy ciąg – wygrywasz!")
            return

        self.label.setText("Tęczowe Trójki — Twój ruch")

    def end_game(self, title, message):
        QMessageBox.information(self, title, message)
        for btn in self.buttons:
            btn.setEnabled(False)

    def check_rainbow_triplet(self):
        colored = [i for i in range(1, self.size + 1) if self.board[i] is not None]
        for a, c in itertools.combinations(colored, 2):
            b = (a + c) // 2
            if (a + c) % 2 == 0 and self.board[b] is not None:
                colors = {self.board[a], self.board[b], self.board[c]}
                if len(colors) == 3:
                    return True
        return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    start = StartWindow()
    start.show()
    sys.exit(app.exec_())

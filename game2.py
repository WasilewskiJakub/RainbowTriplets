import sys
import random
import itertools
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QMessageBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QTimer


class StartWindow(QWidget):
    def __init__(self, size=9):
        super().__init__()
        self.size = size
        self.setWindowTitle("Tęczowe Trójki")
        self.current_turn = 0  # liczba wykonanych ruchów
        # mapa pozycji -> kolor (None lub 0,1,2)
        self.board = {i: None for i in range(1, size + 1)}

        # UI
        self.layout = QVBoxLayout()
        self.label = QLabel("Tęczowe Trójki — Twój ruch")
        self.layout.addWidget(self.label)

        row = QHBoxLayout()
        self.buttons = []
        for i in range(1, size + 1):
            btn = QPushButton(str(i))
            btn.setFixedSize(40, 40)
            btn.clicked.connect(lambda _, x=i: self.player_move(x))
            self.buttons.append(btn)
            row.addWidget(btn)
        self.layout.addLayout(row)

        self.setLayout(self.layout)

    def color(self, turn_index):
        # Zwraca kod koloru 0,1,2 na podstawie tury
        return turn_index % 3

    def color_to_qcolor(self, code):
        return {0: QColor('red'), 1: QColor('green'), 2: QColor('blue')}[code]

    def is_valid(self, pos):
        return self.board.get(pos) is None

    def set_move(self, pos):
        code = self.color(self.current_turn)
        self.board[pos] = code
        btn = self.buttons[pos - 1]
        btn.setStyleSheet(f"background-color: {self.color_to_qcolor(code).name()}")
        btn.setEnabled(False)
        self.current_turn += 1

    def player_move(self, pos):
        if not self.is_valid(pos):
            return
        self.set_move(pos)
        if self.check_rainbow_triplet():
            self.end_game("Przegrana", "Utworzyłeś tęczowy ciąg – przegrywasz!")
            return
        self.label.setText("Tęczowe Trójki — Ruch komputera")
        QTimer.singleShot(500, self.computer_move)

    def computer_move(self):
        available = [i for i in self.board if self.board[i] is None]
        if not available:
            self.end_game("Remis", "Brak dostępnych ruchów.")
            return
        # 1. filtrowanie natychmiastowych przegranych
        safe_moves = []
        for m in available:
            self.board[m] = self.color(self.current_turn)
            if not self.check_rainbow_triplet():
                safe_moves.append(m)
            self.board[m] = None
        candidates = safe_moves or available
        # 2. minimalizacja opcji gracza
        best, min_opts = [], None
        for m in candidates:
            self.board[m] = self.color(self.current_turn)
            # ile bezpiecznych ruchów gracz ma
            pa = [j for j in self.board if self.board[j] is None]
            safe_cnt = 0
            for j in pa:
                self.board[j] = self.color(self.current_turn + 1)
                if not self.check_rainbow_triplet():
                    safe_cnt += 1
                self.board[j] = None
            self.board[m] = None
            if min_opts is None or safe_cnt < min_opts:
                min_opts = safe_cnt
                best = [m]
            elif safe_cnt == min_opts:
                best.append(m)
        choice = random.choice(best)
        self.set_move(choice)
        if self.check_rainbow_triplet():
            self.end_game("Wygrana", "Komputer utworzył tęczowy ciąg – wygrywasz!")
            return
        self.label.setText("Tęczowe Trójki — Twój ruch")

    def check_rainbow_triplet(self):
        filled = [i for i, c in self.board.items() if c is not None]
        for a, c in itertools.combinations(filled, 2):
            if (a + c) % 2 == 0:
                b = (a + c) // 2
                if self.board.get(b) is not None:
                    colors = {self.board[a], self.board[b], self.board[c]}
                    if len(colors) == 3:
                        return True
        return False

    def end_game(self, title, msg):
        QMessageBox.information(self, title, msg)
        for btn in self.buttons:
            btn.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = StartWindow(size=9)
    win.show()
    sys.exit(app.exec_())
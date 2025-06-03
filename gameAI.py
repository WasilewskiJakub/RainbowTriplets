import sys
import random
import itertools
import math
from copy import deepcopy
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QMessageBox, QLineEdit, QComboBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QTimer


class StartWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tęczowe Trójki — Start")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label_n = QLabel("Podaj wartość n (liczba pozycji = 3n):")
        self.layout.addWidget(self.label_n)

        self.input_n = QLineEdit()
        self.input_n.setPlaceholderText("np. 3")
        self.layout.addWidget(self.input_n)

        self.label_ai = QLabel("Wybierz tryb gry z komputerem:")
        self.layout.addWidget(self.label_ai)

        self.ai_selector = QComboBox()
        self.ai_selector.addItems(["Losowy", "Heurystyczny", "MCTS"])
        self.layout.addWidget(self.ai_selector)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_game)
        self.layout.addWidget(self.start_button)

    def start_game(self):
        try:
            n = int(self.input_n.text())
            if n < 1:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Wprowadź poprawną liczbę całkowitą większą od zera.")
            return

        ai_mode = self.ai_selector.currentText().lower()
        self.hide()
        self.game_window = RainbowTripletsGame(size=3 * n, ai_mode=ai_mode)
        self.game_window.show()


class MCTSNode:
    def __init__(self, board, turn, parent=None, move=None):
        self.board = deepcopy(board)
        self.turn = turn
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.wins = 0

    def is_fully_expanded(self):
        return len(self.get_untried_moves()) == 0

    def get_untried_moves(self):
        return [i for i in self.board if self.board[i] is None and i not in [c.move for c in self.children]]

    def ucb1(self, c=1.41):
        if self.visits == 0:
            return float('inf')
        return self.wins / self.visits + c * math.sqrt(math.log(self.parent.visits) / self.visits)

    def best_child(self):
        return max(self.children, key=lambda child: child.ucb1())

    def expand(self):
        move = random.choice(self.get_untried_moves())
        new_board = deepcopy(self.board)
        new_board[move] = self.turn % 3
        child = MCTSNode(new_board, self.turn + 1, parent=self, move=move)
        self.children.append(child)
        return child

    def simulate(self):
        board = deepcopy(self.board)
        turn = self.turn
        while True:
            available = [i for i in board if board[i] is None]
            if not available:
                return 0.5  # remis
            move = random.choice(available)
            board[move] = turn % 3
            if RainbowTripletsGame.find_triplet_static(board):
                return 0 if turn % 2 == 0 else 1
            turn += 1

    def backpropagate(self, result):
        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(1 - result)  # bo przeciwnik wygrywa


class RainbowTripletsGame(QWidget):
    def __init__(self, size=9, ai_mode="losowy"):
        super().__init__()
        self.size = size
        self.ai_mode = ai_mode
        self.setWindowTitle("Tęczowe Trójki")
        self.current_turn = 0
        self.board = {i: None for i in range(1, size + 1)}
        self.button_styles = {}

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
        return turn_index % 3

    def color_to_qcolor(self, code):
        return {0: QColor('red'), 1: QColor('green'), 2: QColor('blue')}[code]

    def is_valid(self, pos):
        return self.board.get(pos) is None

    def set_move(self, pos):
        code = self.color(self.current_turn)
        self.board[pos] = code
        color_hex = self.color_to_qcolor(code).name()
        style = f"background-color: {color_hex};"
        self.button_styles[pos] = style
        btn = self.buttons[pos - 1]
        btn.setStyleSheet(style)
        btn.setEnabled(False)
        self.current_turn += 1

    def player_move(self, pos):
        if not self.is_valid(pos):
            return
        self.set_move(pos)
        triplet = self.find_rainbow_triplet()
        if triplet:
            self.end_game("Przegrana", "Utworzyłeś tęczowy ciąg – przegrywasz!", triplet)
            return
        self.label.setText("Tęczowe Trójki — Ruch komputera")
        QTimer.singleShot(500, self.computer_move)

    def computer_move(self):
        available = [i for i in self.board if self.board[i] is None]
        if not available:
            self.end_game("Remis", "Brak dostępnych ruchów.")
            return

        if self.ai_mode == "losowy":
            choice = random.choice(available)
        elif self.ai_mode == "heurystyczny":
            safe_moves = []
            for m in available:
                self.board[m] = self.color(self.current_turn)
                if not self.find_rainbow_triplet():
                    safe_moves.append(m)
                self.board[m] = None

            candidates = safe_moves or available
            best, min_opts = [], None
            for m in candidates:
                self.board[m] = self.color(self.current_turn)
                future_safe = 0
                for j in self.board:
                    if self.board[j] is None:
                        self.board[j] = self.color(self.current_turn + 1)
                        if not self.find_rainbow_triplet():
                            future_safe += 1
                        self.board[j] = None
                self.board[m] = None
                if min_opts is None or future_safe < min_opts:
                    min_opts = future_safe
                    best = [m]
                elif future_safe == min_opts:
                    best.append(m)
            choice = random.choice(best)
        else:  # MCTS
            root = MCTSNode(self.board, self.current_turn)
            for _ in range(100):  # liczba symulacji
                node = root
                while node.is_fully_expanded() and node.children:
                    node = node.best_child()
                if node.get_untried_moves():
                    node = node.expand()
                result = node.simulate()
                node.backpropagate(result)
            choice = max(root.children, key=lambda c: c.visits).move

        self.set_move(choice)
        triplet = self.find_rainbow_triplet()
        if triplet:
            self.end_game("Wygrana", "Komputer utworzył tęczowy ciąg – wygrywasz!", triplet)
            return
        self.label.setText("Tęczowe Trójki — Twój ruch")

    def find_rainbow_triplet(self):
        return RainbowTripletsGame.find_triplet_static(self.board)

    @staticmethod
    def find_triplet_static(board):
        filled = [i for i, c in board.items() if c is not None]
        for a, c in itertools.combinations(filled, 2):
            if (a + c) % 2 == 0:
                b = (a + c) // 2
                if board.get(b) is not None:
                    colors = {board[a], board[b], board[c]}
                    if len(colors) == 3:
                        return (a, b, c)
        return None

    def end_game(self, title, msg, triplet=None):
        if triplet:
            for i in triplet:
                base_style = self.button_styles.get(i, "")
                self.buttons[i - 1].setStyleSheet(base_style + "border: 3px solid black;")
        QMessageBox.information(self, title, msg)
        for btn in self.buttons:
            btn.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    start = StartWindow()
    start.show()
    sys.exit(app.exec_())

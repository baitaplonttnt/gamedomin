import random
from typing import Optional, Set

from utils import Board, Coord, get_neighbors


class Minesweeper:
    """
    Môi trường game Minesweeper.

    AI chỉ được nhìn bảng thông qua get_percept().
    AI không được nhìn trực tiếp self.mines.
    """

    def __init__(
        self,
        rows: int,
        cols: int,
        mine_count: int,
        seed: Optional[int] = None,
        first_click_safe: bool = True,
    ):
        if rows <= 0 or cols <= 0:
            raise ValueError("Số hàng và số cột phải lớn hơn 0.")

        if mine_count <= 0:
            raise ValueError("Số mìn phải lớn hơn 0.")

        if mine_count >= rows * cols:
            raise ValueError("Số mìn phải nhỏ hơn tổng số ô.")

        self.rows = rows
        self.cols = cols
        self.mine_count = mine_count
        self.first_click_safe = first_click_safe

        self.random = random.Random(seed)

        self.mines: Set[Coord] = set()
        self.opened = [[False for _ in range(cols)] for _ in range(rows)]

        self.game_over = False
        self.won = False
        self.move_count = 0

        self._place_mines()

    def _place_mines(self) -> None:
        """
        Sinh mìn ngẫu nhiên trên bảng.
        """
        all_cells = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
        ]

        self.mines = set(self.random.sample(all_cells, self.mine_count))

    def in_bounds(self, row: int, col: int) -> bool:
        """
        Kiểm tra tọa độ có nằm trong bảng không.
        """
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_mine(self, row: int, col: int) -> bool:
        """
        Kiểm tra ô có phải mìn không.
        """
        return (row, col) in self.mines

    def count_adjacent_mines(self, row: int, col: int) -> int:
        """
        Đếm số mìn xung quanh ô (row, col).
        """
        count = 0

        for nr, nc in get_neighbors(self.rows, self.cols, row, col):
            if (nr, nc) in self.mines:
                count += 1

        return count

    def get_percept(self) -> Board:
        """
        Sensor cho AI.

        Return:
            -1 nếu ô chưa mở
            0..8 nếu ô đã mở
        """
        board = []

        for r in range(self.rows):
            row_data = []

            for c in range(self.cols):
                if self.opened[r][c]:
                    row_data.append(self.count_adjacent_mines(r, c))
                else:
                    row_data.append(-1)

            board.append(row_data)

        return board

    def _relocate_mine(self, safe_cell: Coord) -> None:
        """
        Đảm bảo click đầu tiên không chết.

        Nếu ô đầu tiên có mìn, di chuyển mìn đó sang ô khác.
        """
        if safe_cell not in self.mines:
            return

        self.mines.remove(safe_cell)

        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) != safe_cell and (r, c) not in self.mines
        ]

        new_mine = self.random.choice(candidates)
        self.mines.add(new_mine)

    def _reveal_from(self, row: int, col: int) -> None:
        """
        Mở ô.

        Nếu ô đó là số 0, tự động mở lan các ô xung quanh.
        """
        stack = [(row, col)]

        while stack:
            cr, cc = stack.pop()

            if not self.in_bounds(cr, cc):
                continue

            if self.opened[cr][cc]:
                continue

            if (cr, cc) in self.mines:
                continue

            self.opened[cr][cc] = True

            if self.count_adjacent_mines(cr, cc) == 0:
                for nr, nc in get_neighbors(self.rows, self.cols, cr, cc):
                    if not self.opened[nr][nc] and (nr, nc) not in self.mines:
                        stack.append((nr, nc))

    def _check_win(self) -> None:
        """
        Kiểm tra điều kiện thắng:
            Mở hết tất cả ô không phải mìn.
        """
        opened_count = 0

        for r in range(self.rows):
            for c in range(self.cols):
                if self.opened[r][c]:
                    opened_count += 1

        safe_cells = self.rows * self.cols - self.mine_count

        if opened_count == safe_cells:
            self.won = True
            self.game_over = True

    def make_move(self, row: int, col: int) -> str:
        """
        Actuator cho AI.

        AI gọi hàm này để click vào ô.

        Return:
            "invalid"
            "already_opened"
            "mine"
            "safe"
            "won"
            "game_over"
        """
        if self.game_over:
            return "game_over"

        if not self.in_bounds(row, col):
            return "invalid"

        if self.opened[row][col]:
            return "already_opened"

        if self.move_count == 0 and self.first_click_safe:
            self._relocate_mine((row, col))

        self.move_count += 1

        if (row, col) in self.mines:
            self.game_over = True
            self.won = False
            return "mine"

        self._reveal_from(row, col)
        self._check_win()

        if self.won:
            return "won"

        return "safe"

    def render(self, show_mines: bool = False) -> None:
        """
        Hiển thị bảng ra terminal.
        """
        print()
        print("    " + " ".join(f"{c:2d}" for c in range(self.cols)))
        print("   " + "---" * self.cols)

        for r in range(self.rows):
            row_display = []

            for c in range(self.cols):
                if show_mines and (r, c) in self.mines:
                    row_display.append(" *")
                elif self.opened[r][c]:
                    row_display.append(f"{self.count_adjacent_mines(r, c):2d}")
                else:
                    row_display.append(" ?")

            print(f"{r:2d}| " + " ".join(row_display))

        print()
import sys
import time
from typing import Optional, Tuple

from environment import Minesweeper
from logic_ai import ResolutionLogicAI
from probability_ai import ProbabilisticAI
from utils import Board, Coord, get_frontier_cells


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def choose_ai_move(
    board: Board,
    logic_ai: ResolutionLogicAI,
    probability_ai: ProbabilisticAI,
) -> Tuple[Optional[Coord], str]:
    """
    Chọn nước đi cho AI.

    Ưu tiên:
        1. Nếu frontier nhỏ thì dùng Logic AI.
        2. Nếu frontier lớn hoặc Logic AI không tìm được, dùng Probability AI.
    """

    frontier = get_frontier_cells(board)

    # Giới hạn Logic AI để tránh PL-Resolution chạy quá lâu.
    if len(frontier) <= 6:
        move = logic_ai.find_safe_move(board)

        if move is not None:
            return move, "Logic AI"

    move = probability_ai.find_best_move(board)

    if move is not None:
        return move, "Probability AI"

    return None, "No Move"


def play_game(
    rows: int = 5,
    cols: int = 5,
    mine_count: int = 5,
    seed: Optional[int] = None,
    delay: float = 0.2,
) -> None:
    """
    Hàm chạy game chính.
    """
    game = Minesweeper(
        rows=rows,
        cols=cols,
        mine_count=mine_count,
        seed=seed,
        first_click_safe=True,
    )

    logic_ai = ResolutionLogicAI()

    probability_ai = ProbabilisticAI(
        mine_probability=mine_count / (rows * cols),
        seed=seed,
    )

    print("===== MINESWEEPER AI START =====")
    print(f"Board: {rows}x{cols}")
    print(f"Mines: {mine_count}")
    print()

    game.render(show_mines=False)

    step = 0

    while not game.game_over:
        step += 1

        board = game.get_percept()

        move, ai_name = choose_ai_move(
            board=board,
            logic_ai=logic_ai,
            probability_ai=probability_ai,
        )

        if move is None:
            print("AI không tìm được nước đi nào.")
            break

        row, col = move

        print(f"Step {step}: {ai_name} chọn ô ({row}, {col})")

        result = game.make_move(row, col)

        print(f"Kết quả: {result}")

        if result == "mine":
            print("AI đã click trúng mìn.")
            game.render(show_mines=True)
            break

        if result == "won":
            print("AI đã thắng game.")
            game.render(show_mines=True)
            break

        game.render(show_mines=False)

        time.sleep(delay)

    print("===== GAME FINISHED =====")

    if game.won:
        print("Kết quả cuối cùng: AI THẮNG")
    else:
        print("Kết quả cuối cùng: AI THUA hoặc không thể đi tiếp")


if __name__ == "__main__":
    play_game(
        rows=5,
        cols=5,
        mine_count=5,
        seed=100,
        delay=0.2,
    )
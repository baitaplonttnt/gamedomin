from typing import List, Set, Tuple


Coord = Tuple[int, int]
Board = List[List[int]]


def get_neighbors(rows: int, cols: int, row: int, col: int) -> List[Coord]:
    """
    Trả về danh sách các ô lân cận hợp lệ của ô (row, col).
    Một ô có tối đa 8 ô lân cận.
    """
    neighbors = []

    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue

            nr = row + dr
            nc = col + dc

            if 0 <= nr < rows and 0 <= nc < cols:
                neighbors.append((nr, nc))

    return neighbors


def get_unknown_cells(board: Board) -> Set[Coord]:
    """
    Trả về tập các ô chưa mở.
    Quy ước:
        -1 là ô chưa mở
    """
    rows = len(board)
    cols = len(board[0])

    unknowns = set()

    for r in range(rows):
        for c in range(cols):
            if board[r][c] == -1:
                unknowns.add((r, c))

    return unknowns


def get_frontier_cells(board: Board) -> Set[Coord]:
    """
    Frontier là các ô chưa mở nằm cạnh ít nhất một ô số đã mở.

    Đây là vùng mà Logic AI và Probability AI có thông tin để suy luận.
    """
    rows = len(board)
    cols = len(board[0])

    frontier = set()

    for r in range(rows):
        for c in range(cols):
            if board[r][c] >= 0:
                for nr, nc in get_neighbors(rows, cols, r, c):
                    if board[nr][nc] == -1:
                        frontier.add((nr, nc))

    return frontier


def extract_number_constraints(board: Board) -> List[Tuple[List[Coord], int]]:
    """
    Từ board hiện tại, trích xuất các ràng buộc dạng:

        exactly k mines among [cell1, cell2, ...]

    Ví dụ:
        Ô số 2 có 3 ô chưa mở xung quanh A, B, C

    Suy ra:
        Trong A, B, C có đúng 2 ô là mìn.

    Vì phiên bản này chưa dùng flag, ta chỉ xét các ô -1 xung quanh ô số.
    """
    rows = len(board)
    cols = len(board[0])

    constraints = []

    for r in range(rows):
        for c in range(cols):
            number = board[r][c]

            if number < 0:
                continue

            unknown_neighbors = []

            for nr, nc in get_neighbors(rows, cols, r, c):
                if board[nr][nc] == -1:
                    unknown_neighbors.append((nr, nc))

            if unknown_neighbors:
                constraints.append((unknown_neighbors, number))

    return constraints


def coord_to_var(cell: Coord) -> str:
    """
    Chuyển tọa độ ô thành tên biến logic/xác suất.

    Ví dụ:
        (2, 3) -> P_2_3
    """
    row, col = cell
    return f"P_{row}_{col}"
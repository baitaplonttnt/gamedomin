import random
from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Optional, Set, Tuple

from utils import (
    Board,
    Coord,
    coord_to_var,
    extract_number_constraints,
    get_frontier_cells,
    get_unknown_cells,
)


@dataclass
class Factor:
    """
    Factor dùng trong Variable Elimination.

    variables:
        Tuple tên biến.

    table:
        Dict ánh xạ assignment sang trọng số/xác suất.

    Trong đó:
        0 = an toàn
        1 = có mìn
    """

    variables: Tuple[str, ...]
    table: Dict[Tuple[int, ...], float]

    def contains(self, variable: str) -> bool:
        return variable in self.variables

    def normalize(self) -> "Factor":
        """
        Chuẩn hóa factor sao cho tổng xác suất bằng 1.
        """
        total = sum(self.table.values())

        if total == 0:
            return self

        normalized_table = {
            assignment: value / total
            for assignment, value in self.table.items()
        }

        return Factor(self.variables, normalized_table)


def make_constraint_factor(cells: List[Coord], mine_count: int) -> Factor:
    """
    Tạo factor từ ràng buộc Minesweeper:

        exactly mine_count mines among cells

    Ví dụ:
        cells = A, B, C
        mine_count = 1

    Factor bằng 1 nếu A + B + C = 1, ngược lại bằng 0.
    """
    variables = tuple(coord_to_var(cell) for cell in cells)
    table: Dict[Tuple[int, ...], float] = {}

    for assignment in product([0, 1], repeat=len(variables)):
        table[assignment] = 1.0 if sum(assignment) == mine_count else 0.0

    return Factor(variables, table)


def make_prior_factor(variable: str, mine_probability: float) -> Factor:
    """
    Tạo prior factor cho một biến.

    P(variable = 1) = mine_probability
    P(variable = 0) = 1 - mine_probability
    """
    p = max(0.0, min(1.0, mine_probability))

    return Factor(
        variables=(variable,),
        table={
            (0,): 1.0 - p,
            (1,): p,
        },
    )


def build_factors_from_board(
    board: Board,
    mine_probability: float = 0.2,
) -> List[Factor]:
    """
    Xây dựng danh sách factor từ board.

    Gồm:
        1. Constraint factor từ các ô số
        2. Prior factor cho các ô frontier
    """
    factors: List[Factor] = []

    constraints = extract_number_constraints(board)
    frontier = get_frontier_cells(board)

    for cells, mine_count in constraints:
        factors.append(make_constraint_factor(cells, mine_count))

    for cell in frontier:
        variable = coord_to_var(cell)
        factors.append(make_prior_factor(variable, mine_probability))

    return factors


def pointwise_product(f1: Factor, f2: Factor) -> Factor:
    """
    Nhân hai factor.

    Ví dụ:
        f1(A, B)
        f2(B, C)

    Kết quả:
        f3(A, B, C) = f1(A, B) * f2(B, C)
    """
    new_variables = tuple(dict.fromkeys(f1.variables + f2.variables))
    new_table: Dict[Tuple[int, ...], float] = {}

    f1_indices = [new_variables.index(var) for var in f1.variables]
    f2_indices = [new_variables.index(var) for var in f2.variables]

    for assignment in product([0, 1], repeat=len(new_variables)):
        f1_assignment = tuple(assignment[i] for i in f1_indices)
        f2_assignment = tuple(assignment[i] for i in f2_indices)

        value = f1.table[f1_assignment] * f2.table[f2_assignment]
        new_table[assignment] = value

    return Factor(new_variables, new_table)


def multiply_all(factors: List[Factor]) -> Factor:
    """
    Nhân toàn bộ danh sách factor.
    """
    if not factors:
        return Factor(variables=(), table={(): 1.0})

    result = factors[0]

    for factor in factors[1:]:
        result = pointwise_product(result, factor)

    return result


def sum_out(variable: str, factor: Factor) -> Factor:
    """
    Loại bỏ một biến khỏi factor bằng phép cộng dồn.

    Ví dụ:
        g(A, C) = Σ_B f(A, B, C)
    """
    if variable not in factor.variables:
        return factor

    var_index = factor.variables.index(variable)

    new_variables = tuple(
        var for var in factor.variables
        if var != variable
    )

    new_table: Dict[Tuple[int, ...], float] = {}

    for assignment, value in factor.table.items():
        new_assignment = tuple(
            assignment[i]
            for i in range(len(assignment))
            if i != var_index
        )

        new_table[new_assignment] = new_table.get(new_assignment, 0.0) + value

    return Factor(new_variables, new_table)


def get_all_variables(factors: List[Factor]) -> Set[str]:
    """
    Lấy toàn bộ biến xuất hiện trong danh sách factor.
    """
    variables: Set[str] = set()

    for factor in factors:
        variables.update(factor.variables)

    return variables


def get_relevant_factors(
    factors: List[Factor],
    query_variable: str,
) -> List[Factor]:
    """
    Lấy các factor thuộc cùng connected component với query_variable.

    Giúp Variable Elimination nhỏ hơn.
    """
    relevant_factors: List[Factor] = []

    visited_variables: Set[str] = set()
    visited_factor_ids: Set[int] = set()

    queue = [query_variable]
    visited_variables.add(query_variable)

    while queue:
        current_variable = queue.pop(0)

        for i, factor in enumerate(factors):
            if i in visited_factor_ids:
                continue

            if current_variable in factor.variables:
                visited_factor_ids.add(i)
                relevant_factors.append(factor)

                for var in factor.variables:
                    if var not in visited_variables:
                        visited_variables.add(var)
                        queue.append(var)

    return relevant_factors


def variable_elimination(
    factors: List[Factor],
    query_variable: str,
    default_probability: float = 0.5,
) -> Factor:
    """
    Tính phân phối xác suất của query_variable bằng Variable Elimination.

    Kết quả:
        variables = ("P_2_3",)

        table = {
            (0,): xác suất an toàn,
            (1,): xác suất có mìn
        }
    """
    if not factors:
        return Factor(
            variables=(query_variable,),
            table={
                (0,): 1.0 - default_probability,
                (1,): default_probability,
            },
        )

    relevant_factors = get_relevant_factors(factors, query_variable)

    if not relevant_factors:
        return Factor(
            variables=(query_variable,),
            table={
                (0,): 1.0 - default_probability,
                (1,): default_probability,
            },
        )

    working_factors = list(relevant_factors)

    all_variables = get_all_variables(working_factors)

    hidden_variables = [
        var for var in all_variables
        if var != query_variable
    ]

    # Heuristic đơn giản: loại biến có ít factor liên quan trước
    hidden_variables.sort(
        key=lambda var: sum(1 for factor in working_factors if var in factor.variables)
    )

    for variable in hidden_variables:
        containing = [
            factor for factor in working_factors
            if variable in factor.variables
        ]

        not_containing = [
            factor for factor in working_factors
            if variable not in factor.variables
        ]

        if not containing:
            working_factors = not_containing
            continue

        product_factor = multiply_all(containing)
        summed_factor = sum_out(variable, product_factor)

        working_factors = not_containing + [summed_factor]

    result = multiply_all(working_factors)

    if query_variable not in result.variables:
        return Factor(
            variables=(query_variable,),
            table={
                (0,): 1.0 - default_probability,
                (1,): default_probability,
            },
        )

    # Sau khi loại bỏ hidden variables, thường chỉ còn query_variable.
    # Nếu vì lý do nào đó còn biến khác, loại bỏ tiếp.
    extra_variables = [
        var for var in result.variables
        if var != query_variable
    ]

    for variable in extra_variables:
        result = sum_out(variable, result)

    result = result.normalize()

    # Đảm bảo thứ tự variable là query_variable
    if result.variables == (query_variable,):
        return result

    # Trường hợp hiếm: nếu biến không đúng format, trả về mặc định
    return Factor(
        variables=(query_variable,),
        table={
            (0,): 1.0 - default_probability,
            (1,): default_probability,
        },
    )


def get_mine_probability(distribution: Factor) -> float:
    """
    Lấy xác suất query variable là mìn từ factor kết quả.

    Cần giá trị:
        P(variable = 1)
    """
    if not distribution.table:
        return 0.5

    return distribution.table.get((1,), 0.5)


class ProbabilisticAI:
    """
    AI xác suất.

    Khi Logic AI không tìm được ô chắc chắn an toàn,
    AI này chọn ô có xác suất chứa mìn thấp nhất.
    """

    def __init__(
        self,
        mine_probability: float = 0.2,
        seed: Optional[int] = None,
    ):
        self.mine_probability = mine_probability
        self.random = random.Random(seed)

    def find_best_move(self, board: Board) -> Optional[Coord]:
        """
        Trả về ô có xác suất chứa mìn thấp nhất.

        Nếu không có frontier, chọn ngẫu nhiên một ô chưa mở.
        """
        unknown_cells = get_unknown_cells(board)

        if not unknown_cells:
            return None

        frontier = get_frontier_cells(board)

        # Nếu chưa có thông tin gì, chọn random.
        if not frontier:
            return self.random.choice(list(unknown_cells))

        factors = build_factors_from_board(
            board=board,
            mine_probability=self.mine_probability,
        )

        best_cell: Optional[Coord] = None
        best_probability = float("inf")

        for cell in sorted(frontier):
            variable = coord_to_var(cell)

            distribution = variable_elimination(
                factors=factors,
                query_variable=variable,
                default_probability=self.mine_probability,
            )

            mine_prob = get_mine_probability(distribution)

            if mine_prob < best_probability:
                best_probability = mine_prob
                best_cell = cell

        if best_cell is not None:
            return best_cell

        return self.random.choice(list(unknown_cells))
from dataclasses import dataclass
from itertools import combinations
from typing import FrozenSet, List, Optional, Set

from utils import (
    Board,
    Coord,
    coord_to_var,
    extract_number_constraints,
    get_frontier_cells,
)


@dataclass(frozen=True)
class Literal:
    """
    Literal logic.

    Ví dụ:
        P_2_3  : ô (2, 3) có mìn
        ¬P_2_3 : ô (2, 3) không có mìn
    """

    name: str
    is_positive: bool = True

    def negate(self) -> "Literal":
        return Literal(self.name, not self.is_positive)

    def __str__(self) -> str:
        return self.name if self.is_positive else f"¬{self.name}"


Clause = FrozenSet[Literal]


def is_tautology(clause: Clause) -> bool:
    """
    Một clause là tautology nếu chứa cả P và ¬P.
    """
    for lit in clause:
        if lit.negate() in clause:
            return True

    return False


def exactly_k_to_cnf(variables: List[str], k: int) -> Set[Clause]:
    """
    Chuyển ràng buộc:

        exactly k biến True

    sang CNF.

    At most k:
        Không có k + 1 biến nào cùng True.

    At least k:
        Không có n - k + 1 biến nào cùng False.
    """
    clauses: Set[Clause] = set()
    n = len(variables)

    if k < 0 or k > n:
        # Ràng buộc vô lý, tạo empty clause để biểu diễn mâu thuẫn.
        return {frozenset()}

    # At most k:
    # Không được có k + 1 biến cùng True.
    for subset in combinations(variables, k + 1):
        clause = frozenset(Literal(var, False) for var in subset)
        clauses.add(clause)

    # At least k:
    # Không được có n - k + 1 biến cùng False.
    for subset in combinations(variables, n - k + 1):
        clause = frozenset(Literal(var, True) for var in subset)
        clauses.add(clause)

    return clauses


def build_kb_from_board(board: Board) -> Set[Clause]:
    """
    Xây dựng Knowledge Base dạng CNF từ board hiện tại.
    """
    constraints = extract_number_constraints(board)

    kb: Set[Clause] = set()

    for cells, mine_count in constraints:
        variables = [coord_to_var(cell) for cell in cells]
        clauses = exactly_k_to_cnf(variables, mine_count)
        kb.update(clauses)

    return kb


def resolve(ci: Clause, cj: Clause) -> Set[Clause]:
    """
    Sinh resolvent giữa hai clause ci và cj.

    Nếu:
        ci chứa P
        cj chứa ¬P

    Thì resolvent:
        ci bỏ P, cj bỏ ¬P, rồi hợp lại.
    """
    resolvents: Set[Clause] = set()

    for lit in ci:
        opposite = lit.negate()

        if opposite in cj:
            new_clause = set(ci)
            new_clause.remove(lit)

            new_clause.update(cj)
            new_clause.remove(opposite)

            new_clause_frozen = frozenset(new_clause)

            if not is_tautology(new_clause_frozen):
                resolvents.add(new_clause_frozen)

    return resolvents


def pl_resolution(kb: Set[Clause], alpha: Clause) -> bool:
    """
    Kiểm tra KB ⊨ alpha bằng PL-Resolution.

    Theo phản chứng:

        KB ⊨ alpha

    nếu:

        KB ∧ ¬alpha

    dẫn đến mâu thuẫn, tức sinh ra empty clause.
    """
    clauses = set(kb)

    # alpha thường là clause chỉ có 1 literal.
    # Ví dụ alpha = {¬P_1_2}
    # Khi phản chứng, thêm ¬alpha = {P_1_2}
    negated_alpha = frozenset(lit.negate() for lit in alpha)
    clauses.add(negated_alpha)

    new: Set[Clause] = set()

    while True:
        clause_list = list(clauses)
        n = len(clause_list)

        for i in range(n):
            for j in range(i + 1, n):
                ci = clause_list[i]
                cj = clause_list[j]

                resolvents = resolve(ci, cj)

                # Empty clause nghĩa là mâu thuẫn.
                if frozenset() in resolvents:
                    return True

                new.update(resolvents)

        if new.issubset(clauses):
            return False

        clauses.update(new)


class ResolutionLogicAI:
    """
    AI logic dùng Propositional Logic + PL-Resolution.

    Mục tiêu chính:
        Tìm ô chắc chắn an toàn 100%.
    """

    def find_safe_move(self, board: Board) -> Optional[Coord]:
        """
        Trả về một ô chắc chắn an toàn nếu chứng minh được.

        Nếu không tìm được:
            return None
        """
        kb = build_kb_from_board(board)
        frontier = get_frontier_cells(board)

        for cell in sorted(frontier):
            var = coord_to_var(cell)

            # Muốn chứng minh cell an toàn:
            # KB ⊨ ¬P_cell
            alpha = frozenset({Literal(var, False)})

            if pl_resolution(kb, alpha):
                return cell

        return None

    def find_certain_mines(self, board: Board) -> Set[Coord]:
        """
        Tùy chọn nâng cao:
        Tìm các ô chắc chắn là mìn.

        Kiểm tra:
            KB ⊨ P_cell
        """
        kb = build_kb_from_board(board)
        frontier = get_frontier_cells(board)

        certain_mines: Set[Coord] = set()

        for cell in sorted(frontier):
            var = coord_to_var(cell)

            alpha = frozenset({Literal(var, True)})

            if pl_resolution(kb, alpha):
                certain_mines.add(cell)

        return certain_mines
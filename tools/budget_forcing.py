from __future__ import annotations
from dataclasses import dataclass
from typing import List

PHI = 1.618033988749895


def fib_steps(n0: int = 512, n1: int = 832, limit: int = 100000) -> List[int]:
    a, b = n0, n1
    steps = [a, b]
    while True:
        c = a + b
        if c > limit:
            break
        steps.append(c)
        a, b = b, c
    return steps


@dataclass
class BudgetController:
    first: int = 512
    second: int = 832
    limit: int = 100000
    continue_token: str = "Wait"

    def budgets(self) -> List[int]:
        return fib_steps(self.first, self.second, self.limit)

    def force_continue_str(self) -> str:
        return self.continue_token

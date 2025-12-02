from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any, Optional
# from .cost import CostExpr
import sympy as sp

@dataclass
class RecurrenceBranch:
    # Example: `if n > 1: return f(n/2) + n`
    # TODO: how to deal with pattern matching branches?
    condition: Optional[Any]     
    local_cost: sp.Expr
    # {argname: expr}
    recursive_calls: List[Dict[str, sp.Expr]] = field(default_factory=list)

@dataclass
class ProgramRecurrence:
    # z3 variables
    variables: List[str]
    # (cond, cost)
    base_cases: List[Tuple[Any, sp.Expr]] = field(default_factory=list)
    # Recursive Steps
    # Contains all possible recursive paths (if/else)
    branches: List[RecurrenceBranch] = field(default_factory=list)

    def __repr__(self):
        res = [f"Variables: {self.variables}"]
        res.append("\n  Base Cases:")
        for cond, cost in self.base_cases:
            res.append(f"    If {cond} => Cost: {cost}")
        res.append("\n  Branches:")
        for i, b in enumerate(self.branches):
            res.append(f"    Branch {i+1} (If {b.condition}):")
            res.append(f"      Local Cost: {b.local_cost}")
            res.append(f"      Calls: {b.recursive_calls}")
        return "\n".join(res)
    
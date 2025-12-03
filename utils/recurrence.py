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
    # Use None for unknown value
    variables_values: Dict[str, Optional[sp.Expr]] = field(default_factory=dict)

@dataclass
class ProgramRecurrence:
    # (function_name, branches)
    functions: Tuple[str, List[RecurrenceBranch]] = field(default_factory=lambda: ("", []))
    # function_name -> complexity_claim
    complexity_claims: Dict[str, sp.Expr] = field(default_factory=dict)
    # function_name -> input_size (e.g., "n", "r - l")
    input_sizes: Dict[str, sp.Expr] = field(default_factory=dict)

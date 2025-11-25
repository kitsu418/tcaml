from dataclasses import dataclass
from enum import Enum
from typing import Set

class CostOp(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"

@dataclass(frozen=True)
class CostExpr:
    def __repr__(self): return str(self)

@dataclass(frozen=True)
class CInt(CostExpr):
    value: int
    def __str__(self): return str(self.value)

@dataclass(frozen=True)
class CVar(CostExpr):
    name: str
    def __str__(self): return self.name

@dataclass(frozen=True)
class CBinary(CostExpr):
    op: CostOp
    left: CostExpr
    right: CostExpr
    def __str__(self): return f"({self.left} {self.op.value} {self.right})"

@dataclass(frozen=True)
class CLog(CostExpr):
    body: CostExpr
    def __str__(self): return f"log({self.body})"

@dataclass(frozen=True)
class CPoly(CostExpr):
    base: CostExpr
    degree: int
    def __str__(self): return f"({self.base}^{self.degree})"

@dataclass(frozen=True)
class CExp(CostExpr):
    base: int
    exponent: CostExpr
    def __str__(self): return f"({self.base}^{self.exponent})"

@dataclass(frozen=True)
class CBigO(CostExpr):
    body: CostExpr
    def __str__(self): return f"O({self.body})"

# Result Structure

@dataclass
class DecomposedCost:
    fixed: CostExpr
    basis: Set[CostExpr]

    def __str__(self):
        sorted_basis = sorted([str(b) for b in self.basis], key=len, reverse=True)
        basis_str = ", ".join(sorted_basis) if self.basis else "{}"
        return f"[Fixed: {self.fixed} | Basis: {{{basis_str}}}]"

# Factory Constructors (Algebraic Simplification)

def val(x: int) -> CInt:
    return CInt(x)

def one() -> CInt:
    return CInt(1)

def make_add(a: CostExpr, b: CostExpr) -> CostExpr:
    if isinstance(a, CInt) and a.value == 0: return b
    if isinstance(b, CInt) and b.value == 0: return a
    if isinstance(a, CInt) and isinstance(b, CInt): return val(a.value + b.value)
    return CBinary(CostOp.ADD, a, b)

def make_sub(a: CostExpr, b: CostExpr) -> CostExpr:
    if isinstance(b, CInt) and b.value == 0: return a
    if isinstance(a, CInt) and isinstance(b, CInt): return val(a.value - b.value)
    return CBinary(CostOp.SUB, a, b)

def make_mul(a: CostExpr, b: CostExpr) -> CostExpr:
    if isinstance(a, CInt):
        if a.value == 0: return val(0)
        if a.value == 1: return b
    if isinstance(b, CInt):
        if b.value == 0: return val(0)
        if b.value == 1: return a
    if isinstance(a, CInt) and isinstance(b, CInt): return val(a.value * b.value)

    def get_base_deg(e: CostExpr):
        if isinstance(e, CVar): return e, 1
        if isinstance(e, CPoly): return e.base, e.degree
        return None, 0
    
    base_a, deg_a = get_base_deg(a)
    base_b, deg_b = get_base_deg(b)

    if base_a and base_b and base_a == base_b:
        return make_poly(base_a, deg_a + deg_b)
    return CBinary(CostOp.MUL, a, b)

def make_poly(base: CostExpr, degree: int) -> CostExpr:
    if degree == 0: return one()
    if degree == 1: return base
    if isinstance(base, CInt): return val(base.value ** degree)
    return CPoly(base, degree)

def make_log(body: CostExpr) -> CostExpr:
    if isinstance(body, CInt) and body.value == 1: return val(0)
    
    if isinstance(body, CPoly):
        return make_mul(val(body.degree), make_log(body.base))
        
    return CLog(body)

def expand_basis(expr: CostExpr) -> Set[CostExpr]:
    if isinstance(expr, CInt): return {one()}
    if isinstance(expr, CVar): return {expr, one()}
    if isinstance(expr, CLog): return {expr, one()}

    if isinstance(expr, CPoly):
        return {make_poly(expr.base, i) for i in range(expr.degree + 1)}

    if isinstance(expr, CExp): return {expr, one()}

    if isinstance(expr, CBinary):
        if expr.op == CostOp.MUL:
            return {make_mul(l, r) for l in expand_basis(expr.left) for r in expand_basis(expr.right)}
            
        elif expr.op in (CostOp.ADD, CostOp.SUB):
            return expand_basis(expr.left).union(expand_basis(expr.right))

    return {expr, one()}

def decompose(expr: CostExpr) -> DecomposedCost:
    if isinstance(expr, CBigO):
        return DecomposedCost(fixed=val(0), basis=expand_basis(expr.body))

    if isinstance(expr, CBinary):
        left = decompose(expr.left)
        right = decompose(expr.right)

        if expr.op in (CostOp.ADD, CostOp.SUB):
            op = expr.op
            new_fixed = make_add(left.fixed, right.fixed) if op == CostOp.ADD else make_sub(left.fixed, right.fixed)
            return DecomposedCost(new_fixed, left.basis.union(right.basis))

        if expr.op == CostOp.MUL:
            # (F1 + B1) * (F2 + B2)
            # Fixed = F1 * F2
            new_fixed = make_mul(left.fixed, right.fixed)
            new_basis = set()
            
            # F * B
            if not (isinstance(left.fixed, CInt) and left.fixed.value == 0):
                for b in right.basis: new_basis.add(make_mul(left.fixed, b))
            
            if not (isinstance(right.fixed, CInt) and right.fixed.value == 0):
                for b in left.basis: new_basis.add(make_mul(b, right.fixed))
            
            # B * B
            for b1 in left.basis:
                for b2 in right.basis:
                    new_basis.add(make_mul(b1, b2))
            
            return DecomposedCost(new_fixed, new_basis)

    return DecomposedCost(fixed=expr, basis=set())

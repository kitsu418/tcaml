import sympy as sp

counter = 0


def create_fresh(name: str) -> sp.Expr:
    global counter
    var = sp.symbols(f"{name}{counter}")
    counter += 1
    return var

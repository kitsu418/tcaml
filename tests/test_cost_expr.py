import pytest
from verification.cost import (
    CVar, CInt, CBinary, CPoly, CLog, CExp, CBigO, CostOp,
    make_add, make_mul, make_poly, make_log, val, one,
    decompose, DecomposedCost
)

n = CVar("n")

@pytest.mark.parametrize(
    "expr, expected",
    [
        # Case 1: Binary Search
        (
            CBigO(make_log(n)),
            DecomposedCost(
                fixed=val(0),
                basis={make_log(n), one()}
            )
        ),

        # Case 2: Merge Sort
        (
            CBigO(make_mul(n, make_log(n))),
            DecomposedCost(
                fixed=val(0),
                basis={
                    make_mul(n, make_log(n)),
                    n,
                    make_log(n),
                    one()
                }
            )
        ),

        # Case 3: Naive Fibonacci
        (
            CBigO(CExp(2, n)),
            DecomposedCost(
                fixed=val(0),
                basis={CExp(2, n), one()}
            )
        ),

        # Case 4: Linear Scan with Setup
        (
            make_add(val(100), CBigO(n)),
            DecomposedCost(
                fixed=val(100),
                basis={n, one()}
            )
        ),

        # Case 5: Nested Loop with Inner Unknown
        # Outer loop runs n times
        # Inner operation is O(n)
        (
            make_mul(n, CBigO(n)),
            DecomposedCost(
                fixed=val(0),
                basis={
                    make_poly(n, 2),
                    n
                }
            )
        ),

        # Case 6: Log Power
        (
            CBigO(make_log(make_poly(n, 3))),
            DecomposedCost(
                fixed=val(0),
                basis={make_log(n), one()}
            )
        ),
        
        # Case 7: Bubble Sort
        (
            CBigO(make_poly(n, 2)),
            DecomposedCost(
                fixed=val(0),
                basis={
                    make_poly(n, 2),
                    n,
                    one()
                }
            )
        ),
    ],
)

def test_decompose_costs(expr, expected):
    result = decompose(expr)
    
    assert result.fixed == expected.fixed and result.basis == expected.basis \
        , f"Decomposition failed for expr: {expr}. Expected: {expected}, Got: {result}"
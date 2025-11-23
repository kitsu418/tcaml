import pytest
from language.lang import *
from language.lang_parser import parse


@pytest.mark.parametrize(
    "program,start,expected",
    [
        ("1", "expr", EInt(1)),
        ("1 + 2", "expr", EBinOp(EBinOpKinds("+"), EInt(1), EInt(2))),
        (
            "1 * 2 + 3",
            "expr",
            EBinOp(
                EBinOpKinds("+"), EBinOp(EBinOpKinds("*"), EInt(1), EInt(2)), EInt(3)
            ),
        ),
        ("int", "delta", DeltaInt()),
        (
            "(v: int) -> int @ 1",
            "type",
            TFunc("v", TBase(DeltaInt()), TBase(DeltaInt()), TSExact(SPInt(1))),
        ),
        (
            "{v: int | v >= 2}",
            "type",
            TRefinement(
                "v", DeltaInt(), SPBinOp(SPBinOpKinds(">="), SPVar("v"), SPInt(2))
            ),
        ),
        (
            "match xs with [] -> 0 | _ -> 1",
            "expr",
            EMatch(
                EVar("xs"),
                [
                    Clause(PNil(), EInt(0)),
                    Clause(PAny(), EInt(1)),
                ],
            ),
        ),
        (
            "1 :: (2 + 3) :: []",
            "expr",
            ECons(EInt(1), ECons(EBinOp(EBinOpKinds("+"), EInt(2), EInt(3)), ENil())),
        ),
        (
            "let rec f : (x: int) -> int @ O(1) = fun (x: int) -> x + 1 in f 1",
            "expr",
            ELet(
                True,
                "f",
                TFunc("x", TBase(DeltaInt()), TBase(DeltaInt()), TSBigO(SPInt(1))),
                EFunc(
                    "x", TBase(DeltaInt()), EBinOp(EBinOpKinds("+"), EVar("x"), EInt(1))
                ),
                EFuncCall(EVar("f"), EInt(1)),
            ),
        ),
    ],
)
def test_parse_exprs(program: str, start: str, expected: Expr) -> None:
    assert parse(program, start) == expected

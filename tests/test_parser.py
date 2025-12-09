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
            "(v: int) -> int @ 1 measure 1",
            "type",
            TFunc("v", TBase(DeltaInt()), TBase(DeltaInt()), TSExact(SPInt(1), SPInt(1))),
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
            "let rec f : (x: int) -> int @ O(1) measure 1 = fun (x: int) -> x + 1 in f 1",
            "expr",
            ELet(
                True,
                "f",
                TFunc("x", TBase(DeltaInt()), TBase(DeltaInt()), TSBigO(SPInt(1), SPInt(1))),
                EFunc(
                    "x", TBase(DeltaInt()), EBinOp(EBinOpKinds("+"), EVar("x"), EInt(1))
                ),
                EFuncCall(EVar("f"), EInt(1)),
            ),
        ),
        (
            "forall a b . exists x y . a = x",
            "espec",
            SPForAll(
                "a",
                SPForAll(
                    "b",
                    SPExists(
                        "x",
                        SPExists(
                            "y", SPBinOp(SPBinOpKinds("="), SPVar("a"), SPVar("x"))
                        ),
                    ),
                ),
            ),
        ),
        (
            "{ v: (int * int) list | len v = 5 }",
            "type",
            TRefinement(
                "v",
                DeltaList(DeltaTuple([DeltaInt(), DeltaInt()])),
                SPBinOp(
                    SPBinOpKinds("="), SPMeasureCall(SPVar("len"), SPVar("v")), SPInt(5)
                ),
            ),
        ),
        (
            "int * int list",
            "delta",
            DeltaTuple([DeltaInt(), DeltaList(DeltaInt())]),
        ),
        (
            "int * int * int",
            "delta",
            DeltaTuple([DeltaInt(), DeltaInt(), DeltaInt()]),
        ),
        (
            "int list array",
            "delta",
            DeltaArray(DeltaList(DeltaInt())),
        ),
        (
            r"""
measure num_rows (mat: int array array) : int =
  len mat;

measure num_cols (mat: int array array) : int =
  if num_rows mat > 0 then len (select mat 0) else 0
            """,
            "prog",
            [
                (
                    "num_rows",
                    EMeasureDef(
                        "mat",
                        TBaseFunc(DeltaArray(DeltaArray(DeltaInt())), DeltaInt()),
                        SPMeasureCall(SPVar("len"), SPVar("mat")),
                    ),
                ),
                (
                    "num_cols",
                    EMeasureDef(
                        "mat",
                        TBaseFunc(DeltaArray(DeltaArray(DeltaInt())), DeltaInt()),
                        SPIte(
                            SPBinOp(
                                SPBinOpKinds(">"),
                                SPMeasureCall(SPVar("num_rows"), SPVar("mat")),
                                SPInt(0),
                            ),
                            SPMeasureCall(
                                SPVar("len"),
                                SPMeasureCall(
                                    SPMeasureCall(SPVar("select"), SPVar("mat")),
                                    SPInt(0),
                                ),
                            ),
                            SPInt(0),
                        ),
                    ),
                ),
            ],
        ),
    ],
)
def test_parse_exprs(program: str, start: str, expected: Expr) -> None:
    assert parse(program, start) == expected


@pytest.mark.parametrize(
    "sugar,unsugared",
    [
        (
            "let f (x : int) : int @ O(n) measure n = x + 1",
            "let f : (x : int) -> int @ O(n) measure n = fun (x : int) -> x + 1",
        ),
        (
            "let f (x : int) (y : int) : int @ O(n) measure n = x + y",
            "let f : (x : int) -> ((y : int) -> int @ O(n) measure n) @ O(1) measure 1 = fun (x : int) -> fun (y : int) -> x + y",
        ),
    ],
)
def test_sugar(sugar: str, unsugared: str) -> None:
    assert parse(sugar) == parse(unsugared)

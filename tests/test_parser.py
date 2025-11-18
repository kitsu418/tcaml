import pytest
from language.lang import *
from language.lang_parser import parse


@pytest.mark.parametrize(
    "program,start,expected",
    [
        ("1", "expr", EInt(1)),
        ("1 + 2", "expr", EBinOp(EBinOpKinds("+"), EInt(1), EInt(2))),
        # TODO: implement order precedence
        # ("1 * 2 + 3", EBinOp(EBinOpKinds("*"), EInt(1), (EBinOp(EBinOpKinds('+'), EInt(2), EInt(3))))),
        # ("(v: int) -> int @ 1", TFunc("v", TBase(DeltaInt()), TBase(DeltaInt()), TSExact(SPInt(1)))),
        ("int", "delta", DeltaInt()),
    ],
)
def test_parse_exprs(program: str, start: str, expected: Expr) -> None:
    assert parse(program, start) == expected

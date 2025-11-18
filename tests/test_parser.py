import pytest
from language.lang import *
from language.lang_parser import parse


@pytest.mark.parametrize(
    "program,expected",
    [
        ("1", EInt(1)),
        ("1 + 2", EBinOp(EBinOpKinds("+"), EInt(1), EInt(2))),
    ],
)
def test_parse_exprs(program: str, expected: Expr) -> None:
    assert parse(program) == expected

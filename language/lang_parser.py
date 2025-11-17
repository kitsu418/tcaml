from lark import Lark, Token, Transformer, Tree
from language.lang import *
from pathlib import Path


class TCamlParserException(Exception):
    pass


class TCamlTransformer(Transformer):
    def __init__(self):
        super(Transformer).__init__()

    def number(self, tree) -> Expr:
        return EInt(int(tree[0].value))

    def bool(self, tree) -> Expr:
        return EBool(tree[0].value == "true")

    def ident(self, tree) -> Expr:
        return EVar(tree[0].value)

    def measure(self, tree) -> Expr:
        left, _, right = tree
        return EMeasure(left, right)

    def prog(self, tree) -> list[Expr]:
        match tuple(map(lambda x: x.value, tree)):
            case (defn,):
                return [defn]
            case (defn, ";", prog):
                return [defn] + prog
        raise TCamlParserException(f"no match on prog expression {tree}")

    def _def(self, tree) -> Expr:
        print(tree)
        return EInt(0)

    def delta(self, tree) -> DeltaType:
        match tuple(map(lambda x: x.value, tree)):
            case ("()",):
                return DeltaUnit()
            case ("int",):
                return DeltaInt()
            case ("bool",):
                return DeltaBool()
            case (left, "*", right):
                return DeltaProd(left, right)
            case (typ, "list"):
                return DeltaList(typ)
            case (typ, "array"):
                return DeltaArray(typ)
        raise TCamlParserException(f"no match on delta expression {tree}")


def construct_lark_parser() -> Lark:
    with open(Path(__file__).parent.absolute() / "lang_parser.lark", "r") as f:
        return Lark(f, start="expr")


def parse_lark_repr(tree: Tree) -> Expr:
    transformer = TCamlTransformer()
    result_tree = transformer.transform(tree)
    return result_tree


def parse(text: str) -> Expr:
    parser = construct_lark_parser()
    return parse_lark_repr(parser.parse(text))

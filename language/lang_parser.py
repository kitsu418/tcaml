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
        return EVar(tree[0])

    def measure(self, tree) -> Expr:
        left, _, right = tree
        return EMeasure(left, right)

    def prog(self, tree) -> list[Expr]:
        match tree:
            case (defn,):
                return [defn]
            case (defn, ";", prog):
                return [defn] + prog
        raise TCamlParserException(f"no match on prog expression {tree}")

    def _def(self, tree) -> tuple[str, Expr]:
        return tree[0]

    def funcdef(self, tree) -> tuple[str, Expr]:
        if tree[1].value == "rec":
            _, _, ident, _, typ, _, body = tree
        else:
            _, ident, _, typ, _, body = tree
        return ident, EFuncDef(typ, body)

    def measuredef(self, tree) -> tuple[str, Expr]:
        _, ident, _, inp, _, ret, _, body = tree
        return ident, EMeasureDef(inp, ret, body)

    def delta(self, tree) -> DeltaType:
        match tree:
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

    def _type(self, tree) -> Type:
        match tree:
            case (dtype,):
                return TBase(dtype)
            case ("{", ident, "L", dtype, "|", espec, "}"):
                return TRefinement(ident, dtype, espec)
            case ("(", ident, ":", typ, ")", "->", ret, "@", cspec):
                return TFunc(ident, typ, ret, cspec)
            case (inp, "->", ret):
                return TBaseFunc(inp, ret)
        raise TCamlParserException(f"no match on type expression {tree}")

    def cspec(self, tree) -> TimeSpec:
        match tree:
            case (espec,):
                return TSExact(espec)
            case ("O(", espec, ")"):
                return TSBigO(espec)
        raise TCamlParserException(f"no match on time expression {tree}")

    def espec(self, tree) -> Spec:
        match tree:
            # these are by default turned into expressions, so extract them out
            case EVar(ident):
                return SPVar(ident)
            case EInt(value):
                return SPInt(value)
            case EBool(value):
                return SPBool(value)

            case ("not", body):
                return SPNot(body)
            case (left, op, right) if isinstance(op, SPBinOpKinds):
                return SPBinOp(op, left, right)
            case ("forall", idents, ".", spec):
                cur = spec
                for ident in reversed(idents):
                    cur = SPForAll(ident, cur)
                return cur
            case ("exists", idents, ".", spec):
                cur = spec
                for ident in reversed(idents):
                    cur = SPExists(ident, cur)
                return cur
            case (measure, inp):
                return SPMeasureCall(measure, inp)
            case ("if", cond, "then", then, "else", els):
                return SPIte(cond, then, els)
            case ("(", body, ")"):
                return body
        raise TCamlParserException(f"no match on espec expression {tree}")

    def opspec(self, tree) -> SPBinOpKinds:
        return SPBinOpKinds(tree[0])

    def expr(self, tree) -> Expr:
        match tree:
            # these are by default turned into expressions, so extract them out
            case EVar(_):
                return tree
            case EInt(_):
                return tree
            case EBool(_):
                return tree

            case ("not", body):
                return ENot(body)
            case (left, op, right) if isinstance(op, EBinOpKinds):
                return EBinOp(op, left, right)
            case ("if", cond, "then", then, "else", els):
                return EIte(cond, then, els)
            case ("let", ident, ":", typ, "=", value, "in", body) | (
                "let",
                "rec",
                ident,
                ":",
                typ,
                "=",
                value,
                "in",
                body,
            ):
                return ELet(ident, typ, value, body)
            case ("fun", "(", ident, ":", typ, ")", "->", ret):
                return EFunc(ident, typ, ret)
            case (func, inp):
                return EFuncCall(func, inp)
            case ("[]",):
                return ENil()
            case (head, "::", tail):
                return ECons(head, tail)
            case ("match", value, "with", clauses):
                return EMatch(value, clauses)
            case ("(", body, ")"):
                return body
        raise TCamlParserException(f"no match on expr expression {tree}")

    def clauses(self, tree) -> list[Clause]:
        match tree:
            case (path, "->", expr):
                return [Clause(path, expr)]
            case (path, "->", expr, "|", rest):
                return [Clause(path, expr)] + rest
        raise TCamlParserException(f"no match on clauses expression {tree}")

    def pat(self, tree) -> Pattern:
        match tree:
            # these are by default turned into expressions, so extract them out
            case EVar(ident):
                return PVar(ident)
            case ("_",):
                return PAny()
            case EInt(value):
                return PInt(value)
            case EBool(value):
                return PInt(value)

            case ("[]",):
                return PNil()
            case (head, "::", tail):
                return PCons(head, tail)
            case ("(", pat, ")"):
                return pat
            case ("(", left, ",", right, ")"):
                return PPair(left, right)

        raise TCamlParserException(f"no match on clauses expression {tree}")

    def op(self, tree) -> EBinOpKinds:
        print(f'tree is {tree}')
        return EBinOpKinds(tree[0])


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

from lark import Lark, Transformer, Token, Tree
from language.lang import *
from pathlib import Path
from typing import Any


class TCamlParserException(Exception):
    pass


def get_values(tree) -> tuple:
    return tuple(map(lambda x: x.value if isinstance(x, Token) else x, tree))


def is_cname(ident: Any) -> bool:
    if isinstance(ident, str):
        if not ident or ident == "_":
            return False
        if ident[0] != "_" and not ident[0].isalpha():
            return False
        for c in ident[1:]:
            if c != "_" and not c.isalnum():
                return False
        return True
    return False


def is_ebinop(op: Any) -> bool:
    if isinstance(op, str):
        try:
            _ = EBinOpKinds(op)
            return True
        except:
            return False
    return False


def is_spbinop(op: Any) -> bool:
    if isinstance(op, str):
        try:
            _ = SPBinOpKinds(op)
            return True
        except:
            return False
    return False


class TCamlTransformer(Transformer):
    def __init__(self):
        super(Transformer).__init__()

    def number(self, tree) -> int:
        return int(tree[0].value)

    def bool(self, tree) -> bool:
        return tree[0].value == "true"

    def ident(self, tree) -> str:
        return tree[0]

    def idents(self, tree) -> list[str]:
        return [x.value for x in tree]

    def prog(self, tree) -> list[tuple[str, Expr]]:
        print(get_values(tree))
        match get_values(tree):
            case (defn,):
                return [defn]
            case (defn, ";", prog):
                return [defn] + prog
        raise TCamlParserException(f"no match on prog expression {tree}")

    def defn(self, tree) -> tuple[str, Expr]:
        return tree[0]

    def funcdef(self, tree) -> tuple[str, Expr]:
        if tree[1].value == "rec":
            rec = True
            _, _, ident, _, typ, _, body = tree
        else:
            rec = False
            _, ident, _, typ, _, body = tree
        return ident, EFuncDef(rec, typ, body)

    def measuredef(self, tree) -> tuple[str, Expr]:
        _, ident, _, inp, _, typ, _, _, ret, _, body = get_values(tree)
        return ident, EMeasureDef(inp, TBaseFunc(typ, ret), body)

    def delta_parser(self, tree) -> DeltaType:
        match get_values(tree):
            case ("()",):
                return DeltaUnit()
            case ("int",):
                return DeltaInt()
            case ("bool",):
                return DeltaBool()
            case ("(", typ, ")"):
                return typ
            case (typ, "list"):
                return DeltaList(typ)
            case (typ, "array"):
                return DeltaArray(typ)
        raise TCamlParserException(f"no match on delta expression {tree}")

    delta_init = delta_parser
    delta0 = delta_parser

    # handles pairs
    def delta1(self, tree) -> DeltaType:
        vals = get_values(tree)
        print(vals)
        if len(vals) == 1:
            return vals[0]
        else:
            every_other = list(get_values(tree)[::2])
            return DeltaTuple(every_other)

    def type(self, tree) -> Type:
        match get_values(tree):
            case (dtype,):
                return TBase(dtype)
            case ("{", ident, ":", dtype, "|", espec, "}"):
                return TRefinement(ident, dtype, espec)
            case ("(", ident, ":", typ, ")", "->", ret, "@", cspec):
                return TFunc(ident, typ, ret, cspec)
            case (inp, "->", ret):
                return TBaseFunc(inp, ret)
        raise TCamlParserException(f"no match on type expression {tree}")

    def cspec(self, tree) -> TimeSpec:
        match get_values(tree):
            case (espec,):
                return TSExact(espec)
            case ("O(", espec, ")"):
                return TSBigO(espec)
        raise TCamlParserException(f"no match on time expression {tree}")

    def espec_parser(self, tree) -> Spec:
        vals = get_values(tree)
        match vals:
            case (ident,) if is_cname(ident):
                return SPVar(ident)
            case (value,) if isinstance(value, int):
                return SPInt(value)
            case (value,) if isinstance(value, bool):
                return SPBool(value)
            case ("not", body):
                return SPNot(body)
            case (left, op, right) if is_spbinop(op):
                return SPBinOp(SPBinOpKinds(op), left, right)
            case ("forall", idents, ".", spec):
                cur = spec
                print("here", idents)
                for ident in reversed(idents):
                    cur = SPForAll(ident, cur)
                return cur
            case ("exists", idents, ".", spec):
                cur = spec
                print("here", idents)
                for ident in reversed(idents):
                    cur = SPExists(ident, cur)
                return cur
            case (measure, inp) if is_cname(measure):
                return SPMeasureCall(measure, inp)
            case ("if", cond, "then", then, "else", els):
                return SPIte(cond, then, els)
            case ("(", body, ")"):
                return body

        if vals and vals[0] == "forall":
            dot_idx = vals.index(".")
            if dot_idx != -1 and dot_idx + 1 < len(vals):
                idents = vals[1:dot_idx]
                # spec = vals[
        raise TCamlParserException(f"no match on espec expression {tree}")

    espec_init = espec_parser
    espec0 = espec_parser
    espec1 = espec_parser
    espec2 = espec_parser
    espec3 = espec_parser
    espec4 = espec_parser
    espec5 = espec_parser
    espec6 = espec_parser
    espec7 = espec_parser
    espec8 = espec_parser
    espec9 = espec_parser

    def expr_parser(self, tree) -> Expr:
        print(get_values(tree))
        match get_values(tree):
            case (ident,) if is_cname(ident):
                return EVar(ident)
            case (value,) if isinstance(value, int):
                return EInt(value)
            case (value,) if isinstance(value, bool):
                return EBool(value)
            case ("not", body):
                return ENot(body)
            case (left, op, right) if is_ebinop(op):
                return EBinOp(EBinOpKinds(op), left, right)
            case ("if", cond, "then", then, "else", els):
                return EIte(cond, then, els)
            case ("let", ident, ":", typ, "=", value, "in", body):
                return ELet(False, ident, typ, value, body)
            case (
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
                return ELet(True, ident, typ, value, body)
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
            case (val,):
                return val
        raise TCamlParserException(f"no match on expr expression {tree}")

    expr_init = expr_parser
    expr0 = expr_parser
    expr1 = expr_parser
    expr2 = expr_parser
    expr3 = expr_parser
    expr4 = expr_parser
    expr5 = expr_parser
    expr6 = expr_parser
    expr7 = expr_parser
    expr8 = expr_parser

    def clauses(self, tree) -> list[Clause]:
        match get_values(tree):
            case (path, "->", expr):
                return [Clause(path, expr)]
            case (path, "->", expr, "|", rest):
                return [Clause(path, expr)] + rest
        raise TCamlParserException(f"no match on clauses expression {tree}")

    def pat(self, tree) -> Pattern:
        match get_values(tree):
            case (ident,) if is_cname(ident):
                return PVar(ident)
            case ("_",):
                return PAny()
            case (value,) if isinstance(value, int):
                return PInt(value)
            case (value,) if isinstance(value, bool):
                return PBool(value)
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
        return EBinOpKinds(tree[0])


def construct_lark_parser(start: str) -> Lark:
    with open(Path(__file__).parent.absolute() / "lang_parser.lark", "r") as f:
        return Lark(f, start=start)


def parse_lark_repr(tree: Tree) -> Expr:
    print(tree)
    transformer = TCamlTransformer()
    result_tree = transformer.transform(tree)
    return result_tree


def parse(text: str, start: str | None = None) -> Expr:
    if start is None:
        start = "prog"
    parser = construct_lark_parser(start)
    return parse_lark_repr(parser.parse(text))

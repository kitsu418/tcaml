from dataclasses import dataclass
from enum import Enum


class Expr:
    pass


class DeltaType:
    pass


class BinOpKinds(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "mod"
    POW = "^"
    EQ = "=="
    NEQ = "<>"
    LE = "<"
    GE = ">"
    LEQ = "<="
    GEQ = ">="
    AND = "&&"
    OR = "||"


## Expressions


@dataclass(frozen=True, slots=True, eq=True)
class EDelta(Expr):
    pass


@dataclass(frozen=True, slots=True, eq=True)
class EInt(Expr):
    value: int


@dataclass(frozen=True, slots=True, eq=True)
class EBool(Expr):
    value: bool


@dataclass(frozen=True, slots=True, eq=True)
class EVar(Expr):
    ident: str


@dataclass(frozen=True, slots=True, eq=True)
class EMeasure(Expr):
    left: EDelta
    right: EDelta


## Delta Types


@dataclass(frozen=True, slots=True, eq=True)
class DeltaUnit(DeltaType):
    pass


@dataclass(frozen=True, slots=True, eq=True)
class DeltaInt(DeltaType):
    pass


@dataclass(frozen=True, slots=True, eq=True)
class DeltaBool(DeltaType):
    pass


@dataclass(frozen=True, slots=True, eq=True)
class DeltaProd(DeltaType):
    left: DeltaType
    right: DeltaType


@dataclass(frozen=True, slots=True, eq=True)
class DeltaList(DeltaType):
    typ: DeltaType


@dataclass(frozen=True, slots=True, eq=True)
class DeltaArray(DeltaType):
    typ: DeltaType

from dataclasses import dataclass
from enum import Enum


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


class Expr:
    pass


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


@dataclass(frozen=True, slots=True, eq=True)
class EFuncDef(Expr):
    typ: Type
    body: Expr


@dataclass(frozen=True, slots=True, eq=True)
class EMeasureDef(Expr):
    inp: DeltaType
    ret: DeltaType
    body: Expr


### Delta Types


class DeltaType:
    pass


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


### General types


class Type:
    pass


@dataclass(frozen=True, slots=True, eq=True)
class TBase(Type):
    base: DeltaType


@dataclass(frozen=True, slots=True, eq=True)
class TRefinement(Type):
    ident: str
    typ: DeltaType
    spec: Expr


@dataclass(frozen=True, slots=True, eq=True)
class TFunc(Type):
    ident: str
    typ: Type
    ret: Type
    time: Expr


@dataclass(frozen=True, slots=True, eq=True)
class TBaseFunc(Type):
    inp: Type
    ret: Type


# Time specs


class TimeSpec:
    pass


@dataclass(frozen=True, slots=True, eq=True)
class TSExact(TimeSpec):
    spec: Expr


@dataclass(frozen=True, slots=True, eq=True)
class TSBigO(TimeSpec):
    spec: Expr

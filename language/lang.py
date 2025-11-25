from dataclasses import dataclass
from enum import Enum


# Base Types


class Expr:
    pass


class DeltaType:
    pass


class Type:
    pass


class TimeSpec:
    pass


class Spec:
    pass


class Pattern:
    pass


## Expressions


class EBinOpKinds(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "mod"
    EQ = "="
    NEQ = "<>"
    LE = "<"
    GE = ">"
    LEQ = "<="
    GEQ = ">="
    AND = "&&"
    OR = "||"


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
class EFuncDef(Expr):
    rec: bool
    typ: Type
    body: Expr


@dataclass(frozen=True, slots=True, eq=True)
class EMeasureDef(Expr):
    inp: DeltaType
    ret: DeltaType
    body: Expr


@dataclass(frozen=True, slots=True, eq=True)
class ENot(Expr):
    body: Expr


@dataclass(frozen=True, slots=True, eq=True)
class EBinOp(Expr):
    op: EBinOpKinds
    left: Expr
    right: Expr


@dataclass(frozen=True, slots=True, eq=True)
class EIte(Expr):
    cond: Expr
    then: Expr
    els: Expr


@dataclass(frozen=True, slots=True, eq=True)
class ELet(Expr):
    rec: bool
    ident: str
    typ: Type
    value: Expr
    body: Expr


@dataclass(frozen=True, slots=True, eq=True)
class EFunc(Expr):
    ident: str
    typ: Type
    ret: Expr


@dataclass(frozen=True, slots=True, eq=True)
class EFuncCall(Expr):
    func: Expr
    inp: Expr


@dataclass(frozen=True, slots=True, eq=True)
class ENil(Expr):
    pass


@dataclass(frozen=True, slots=True, eq=True)
class ECons(Expr):
    head: Expr
    tail: Expr


@dataclass(frozen=True, slots=True, eq=True)
class EMatch(Expr):
    value: Expr
    clauses: list["Clause"]


### Delta Types


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


@dataclass(frozen=True, slots=True, eq=True)
class TBase(Type):
    base: DeltaType


@dataclass(frozen=True, slots=True, eq=True)
class TRefinement(Type):
    ident: str
    typ: DeltaType
    spec: Spec


@dataclass(frozen=True, slots=True, eq=True)
class TFunc(Type):
    ident: str
    typ: Type
    ret: Type
    time: TimeSpec


@dataclass(frozen=True, slots=True, eq=True)
class TBaseFunc(Type):
    inp: DeltaType
    ret: DeltaType


# Mathematical specifications


class SPBinOpKinds(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "mod"
    POW = "^"
    EQ = "="
    NEQ = "<>"
    LE = "<"
    GE = ">"
    LEQ = "<="
    GEQ = ">="
    AND = "&&"
    OR = "||"


@dataclass(frozen=True, slots=True, eq=True)
class SPVar(Spec):
    ident: str


@dataclass(frozen=True, slots=True, eq=True)
class SPInt(Spec):
    value: int


@dataclass(frozen=True, slots=True, eq=True)
class SPBool(Spec):
    value: bool


@dataclass(frozen=True, slots=True, eq=True)
class SPNot(Spec):
    body: Spec


@dataclass(frozen=True, slots=True, eq=True)
class SPBinOp(Spec):
    op: SPBinOpKinds
    left: Spec
    right: Spec


@dataclass(frozen=True, slots=True, eq=True)
class SPLog(Spec):
    body: Spec


@dataclass(frozen=True, slots=True, eq=True)
class SPForAll(Spec):
    ident: str
    body: Spec


@dataclass(frozen=True, slots=True, eq=True)
class SPExists(Spec):
    ident: str
    body: Spec


@dataclass(frozen=True, slots=True, eq=True)
class SPMeasureCall(Spec):
    measure: str
    inp: Spec


@dataclass(frozen=True, slots=True, eq=True)
class SPIte(Spec):
    cond: Spec
    then: Spec
    els: Spec


# Time specs


@dataclass(frozen=True, slots=True, eq=True)
class TSExact(TimeSpec):
    spec: Spec


@dataclass(frozen=True, slots=True, eq=True)
class TSBigO(TimeSpec):
    spec: Spec


# Clauses and Patterns


@dataclass(frozen=True, slots=True, eq=True)
class Clause:
    pat: "Pattern"
    expr: Expr


@dataclass(frozen=True, slots=True, eq=True)
class PVar(Pattern):
    ident: str


@dataclass(frozen=True, slots=True, eq=True)
class PAny(Pattern):
    pass


@dataclass(frozen=True, slots=True, eq=True)
class PInt(Pattern):
    value: int


@dataclass(frozen=True, slots=True, eq=True)
class PBool(Pattern):
    value: bool


@dataclass(frozen=True, slots=True, eq=True)
class PNil(Pattern):
    pass


@dataclass(frozen=True, slots=True, eq=True)
class PCons(Pattern):
    head: Pattern
    tail: Pattern


@dataclass(frozen=True, slots=True, eq=True)
class PPair(Pattern):
    left: Pattern
    right: Pattern

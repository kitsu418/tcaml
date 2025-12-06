import sympy as sp

from language.lang import *
from utils.recurrence import RecurrenceBranch, ProgramRecurrence
from utils.sympy_vars import create_fresh

VariableMap = dict[str, sp.Expr]


def program_generate_vcs(prog: Program) -> ProgramRecurrence:
    env: dict[str, Expr] = {}

    for name, val in prog:
        match val:
            case EMeasureDef(_):
                env[name] = val
            case EFuncDef(_):
                if val.rec:
                    env[name] = val
        env[name] = val

    return ProgramRecurrence()


# returns environment and constraints on those arguments
def arguments_to_env(body: Expr) -> tuple[VariableMap, sp.Expr]:
    def helper(
        body: Expr, env: VariableMap, constraint: sp.Expr
    ) -> tuple[VariableMap, sp.Expr]:
        match body:
            case EFunc(ident, typ, ret):
                match typ:
                    case TRefinement(inner_ident, dtyp, spec):
                        assert isinstance(dtyp, DeltaInt), "non-int unimplemented"
                        cur_var = create_fresh(ident)
                        local_env = env.copy()
                        local_env[inner_ident] = cur_var
                        local_constraint = spec_to_expr(spec, local_env)
                        constraint = constraint & local_constraint
                    case TBase(dtyp):
                        assert isinstance(dtyp, DeltaInt), "non-int unimplemented"
                        cur_var = create_fresh(ident)
                    case _:
                        assert False, "unimpl"

                env[ident] = cur_var
                return helper(ret, env, constraint)
            case _:
                return env, constraint

    return helper(body, {}, sp.sympify(True))


def timespec_to_sympy(spec: TimeSpec) -> sp.Expr:
    assert isinstance(spec, TSBigO), "concrete unimplemented"


def spec_to_expr(spec: Spec, env: dict[str, sp.Expr]) -> sp.Expr:
    match spec:
        case SPVar(ident):
            return env[ident]
        case SPInt(x) | SPBool(x):
            return sp.sympify(x)
        case SPNot(body):
            return ~spec_to_expr(body, env)
        case SPBinOp(op, left, right):
            left = spec_to_expr(left, env)
            right = spec_to_expr(right, env)
            match op:
                case SPBinOpKinds.ADD:
                    return left + right
                case SPBinOpKinds.SUB:
                    return left - right
                case SPBinOpKinds.MUL:
                    return left * right
                case SPBinOpKinds.DIV:
                    return left / right
                case SPBinOpKinds.MOD:
                    return left % right
                case SPBinOpKinds.POW:
                    return left**right
                case SPBinOpKinds.EQ:
                    return sp.Eq(left, right)
                case SPBinOpKinds.NEQ:
                    return ~sp.Eq(left, right)
                case SPBinOpKinds.LE:
                    return left < right
                case SPBinOpKinds.GE:
                    return left > right
                case SPBinOpKinds.LEQ:
                    return left <= right
                case SPBinOpKinds.GEQ:
                    return left >= right
                case SPBinOpKinds.AND:
                    return left & right
                case SPBinOpKinds.OR:
                    return left | right
        case SPLog(body):
            return sp.log(spec_to_expr(body, env), 2)
        case SPForAll(_) | SPExists(_):
            assert False, "unimpl"
        case SPMeasureCall(_):
            # TODO: impl len at least
            assert False, "unimpl"
        case SPIte(cond, then, els):
            cond = spec_to_expr(cond, env)
            then = spec_to_expr(then, env)
            els = spec_to_expr(els, env)
            return (cond >> then) & ((~cond) >> els)

def expr_to_symb(expr: Expr, env: dict[str, sp.Expr]) -> sp.Expr:
    match expr:
        case EBool(x):
            return sp.sympify(x)
        case EInt(x):
            return sp.sympify(x)
        case ENot(body):
            return ~expr_to_symb(body, env)
        case EBinOp(op, left, right):
            left = expr_to_symb(left, env)
            right = expr_to_symb(right, env)
            match op:
                case EBinOpKinds.ADD:
                    return left + right
                case EBinOpKinds.SUB:
                    return left - right
                case EBinOpKinds.MUL:
                    return left * right
                case EBinOpKinds.DIV:
                    return left / right
                case EBinOpKinds.MOD:
                    return left % right
                case EBinOpKinds.POW:
                    return left**right
                case EBinOpKinds.EQ:
                    return sp.Eq(left, right)
                case EBinOpKinds.NEQ:
                    return ~sp.Eq(left, right)
                case EBinOpKinds.LE:
                    return left < right
                case EBinOpKinds.GE:
                    return left > right
                case EBinOpKinds.LEQ:
                    return left <= right
                case EBinOpKinds.GEQ:
                    return left >= right
                case EBinOpKinds.AND:
                    return left & right
                case EBinOpKinds.OR:
                    return left | right
        case EVar(ident):
            return env[ident]
        case ELet(rec, ident, typ, value, body):
            value = expr_to_symb(value, env)
            new_env = env.copy()
            new_env[ident] = value
            return expr_to_symb(body, new_env)
        case _:
            return None

def function_generate_vcs(
    func: EFuncDef, env: dict[str, Expr]
) -> list[RecurrenceBranch]:
    pass

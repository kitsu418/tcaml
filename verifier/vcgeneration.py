import sympy as sp

from itertools import product
from language.lang import *
from utils.recurrence import RecurrenceBranch, ProgramRecurrence
from utils.sympy_vars import create_fresh
from typing import Newtype

VariableMap = NewType("VariableMap", dict[str, sp.Expr])
TimeSpecMap = NewType("TimeSpecMap", dict[str, sp.Expr])


def program_generate_vcs(prog: Program) -> ProgramRecurrence:
    env = VariableMap({})
    timespecs = TimeSpecMap({})
    constraints = sp.sympify(True)

    for name, val in prog:
        match val:
            case EMeasureDef(_):
                env[name] = val
            case EFuncDef(rec, typ, body):
                assert isinstance(typ, TFunc)

                arg_env, arg_constraint = arguments_to_env(body)
                timespec = timespec_to_sympy(typ.time, arg_env)

                if rec:
                    timespecs[name] = timespec

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


def timespec_to_sympy(spec: TimeSpec, env: VariableMap) -> sp.Expr:
    assert isinstance(spec, TSBigO), "concrete unimplemented"
    return spec_to_expr(spec.spec, env)


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


def cost_of_funccall(
    expr: EFuncCall, env: VariableMap, timespecs: TimeSpecMap
) -> sp.Expr:
    pass


def expr_cost_spec(
    expr: Expr, env: VariableMap, timespecs: TimeSpecMap
) -> list[sp.Expr]:
    match expr:
        case EInt(_) | EBool(_) | EVar(_) | ENil() | ECons(_):
            return [sp.sympify(1)]
        case EFuncDef(_) | EMeasureDef(_):
            assert False, "not allowed in function body"
        case ENot(body):
            return [x + 1 for x in expr_cost_spec(body, env, timespecs)]
        case EBinOp(_, left, right):
            left = expr_cost_spec(left, env, timespecs)
            right = expr_cost_spec(right, env, timespecs)
            return [x + y + 1 for x, y in product(left, right)]
        case EIte(cond, then, els):
            pass
        case ELet(rec, ident, typ, value, body):
            assert not rec, "recursive inner let not allowed"
            value = expr_cost_spec(value, env, timespecs)
            body = expr_cost_spec(body, env, timespecs)
            return [x + y for x, y in product(value, body)]
        case EFunc(_):
            assert False, "local functions not supported"
        case EFuncCall(func, expr):
            assert False, "unimpl"
        case EMatch(_):
            # TODO: match on len
            assert False, "unimpl"


def function_generate_vcs(
    func: EFuncDef, env: dict[str, Expr]
) -> list[RecurrenceBranch]:
    pass

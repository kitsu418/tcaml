import sympy as sp

from collections.abc import Callable
from itertools import product
from language.lang import *
from utils.recurrence import RecurrenceBranch, ProgramRecurrence
from utils.sympy_vars import create_fresh
from typing import NewType

FuncArgsMap = NewType("FuncArgsMap", dict[sp.Expr, sp.Expr | None])


@dataclass(frozen=True, slots=True, eq=True)
class FuncInfo:
    args: list[sp.Expr]
    timespec: sp.Expr
    size: sp.Expr


@dataclass(frozen=True, slots=True, eq=True)
class FuncCall:
    func_name: str
    args: FuncArgsMap


FuncDefs = NewType("FuncDefs", dict[str, FuncInfo])
VariableMap = NewType("VariableMap", dict[str, sp.Expr | None])


def program_generate_vcs(prog: Program) -> ProgramRecurrence:
    env = VariableMap({})
    funcs = FuncDefs({})
    constraints = sp.sympify(True)

    for name, val in prog:
        match val:
            case EMeasureDef(_):
                funcs[name] = val
            case EFuncDef(rec, typ, body):
                assert isinstance(typ, TFunc)

                arg_env, arg_constraint = arguments_to_env(body)
                timespec = timespec_to_sympy(typ.time, arg_env)

                if rec:
                    funcs[name] = (typ.time, body)

                local_costs = expr_cost_spec(body, env, funcs)

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


def spec_to_expr(spec: Spec, env: VariableMap) -> sp.Expr:
    match spec:
        case SPVar(ident):
            value = env[ident]
            assert value is not None
            return value
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


def bind_opt[T, U](val: T | None, func: Callable[[T], U | None]) -> U | None:
    if val is None:
        return None
    else:
        return func(val)


def merge_product[T](xss: list[list[T]], yss: list[list[T]]) -> list[list[T]]:
    return [xs + ys for xs in xss for ys in yss]


def cost_of_funccall(
    expr: EFuncCall, env: VariableMap, funcs: FuncDefs
) -> list[list[FuncCall]]:
    arg_values: list[sp.Expr | None] = []
    cur = expr
    costs: list[list[FuncCall]] = [[]]

    while True:
        match cur:
            case EFuncCall(func, arg):
                arg_value, arg_costs = expr_cost_spec(arg, env, funcs)
                arg_values.append(arg_value)
                costs = merge_product(costs, arg_costs)
                cur = func
            case EVar(fname):
                info = funcs[fname]
                args = info.args
                break
            case _:
                assert False, "unimpl"

    argmap = FuncArgsMap({arg: value for arg, value in zip(args, arg_values)})
    this_call = FuncCall(fname, argmap)
    return merge_product([[this_call]], costs)


def expr_cost_spec(
    expr: Expr, env: VariableMap, funcs: FuncDefs
) -> tuple[sp.Expr | None, list[list[FuncCall]]]:
    match expr:
        case EInt(x) | EBool(x):
            return sp.sympify(x), [sp.sympify(1)]
        case EVar(var):
            return env[var], [sp.sympify(1)]
        case ENil():
            return sp.sympify(1), [sp.sympify(1)]
        case ECons(body):
            body_value, body_costs = expr_cost_spec(body, env, funcs)
            value = bind_opt(body_value, lambda x: x + 1)
            costs = [x + 1 for x in body_costs]
            return value, costs
        case EFuncDef(_) | EMeasureDef(_):
            assert False, "not allowed in function body"
        case ENot(body):
            body_val, body_costs = expr_cost_spec(body, env, funcs)
            value = bind_opt(body_val, lambda x: ~x)
            costs = [x + 1 for x in body_costs]
            return value, costs
        case EBinOp(op, left, right):
            left_value, left_costs = expr_cost_spec(left, env, funcs)
            right_value, right_costs = expr_cost_spec(right, env, funcs)
            value = eval_binop(op, left_value, right_value)
            costs = [x + y + 1 for x, y in product(left_costs, right_costs)]
            return value, costs
        case EIte(cond, then, els):
            # TODO: implement computing the value of a conditional
            _, cond_costs = expr_cost_spec(cond, env, funcs)
            _, then_costs = expr_cost_spec(then, env, funcs)
            _, els_costs = expr_cost_spec(els, env, funcs)
            return None, [
                x + y + z for x, y, z in product(cond_costs, then_costs, els_costs)
            ]
        case ELet(rec, ident, typ, value, body):
            assert not rec, "recursive inner let not allowed"
            value_value, value_costs = expr_cost_spec(value, env, funcs)
            new_env = VariableMap(env.copy())
            new_env[ident] = value_value
            body_value, body_costs = expr_cost_spec(body, new_env, funcs)
            return body_value, [x + y for x, y in product(value_costs, body_costs)]
            return [x + y for x, y in product(value, body)]
        case EFunc(_):
            assert False, "local functions not supported"
        case EFuncCall(_):
            return None, [cost_of_funccall(expr, env, funcs)]
        case EMatch(_):
            # TODO: match on len
            assert False, "unimpl"


def eval_binop(
    op: EBinOpKinds, left: sp.Expr | None, right: sp.Expr | None
) -> sp.Expr | None:
    if left is None or right is None:
        return None
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


def function_generate_vcs(
    func: EFuncDef, env: dict[str, Expr]
) -> list[RecurrenceBranch]:
    pass

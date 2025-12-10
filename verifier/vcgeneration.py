import sympy as sp

from collections.abc import Callable
from language.lang import *
from language.lang_parser import parse
from utils.sympy_vars import create_fresh
from typing import NewType

FuncArgsMap = NewType("FuncArgsMap", dict[sp.Expr, sp.Expr | None])

# use fake function definitions that don't typecheck, just for parsing purposes
stdlib_src = """
let readArray (xs: 'a array) (idx: int): 'a @ O(1) measure [1] = 0;
let writeArray (xs: 'a array) (idx: int) (val: 'a): {v: 'a array | len v = len xs} @ O(len xs) measure [len xs] = 0;
let readList (xs: 'a list) (idx: int): 'a @ O(len xs) measure [len xs] = 0;
let newArray (length: int) (init: 'a): {v: 'a array | len v = length} @ O(1) measure [1] = 0
"""


@dataclass(frozen=True, slots=True, eq=True)
class FuncInfo:
    args: list[sp.Expr]
    timespec: sp.Expr
    size: sp.Expr


@dataclass(frozen=True, slots=True, eq=True)
class FuncCall:
    func_name: str
    args: FuncArgsMap


@dataclass(frozen=True, slots=True, eq=True)
class FunctionTest:
    name: str
    info: FuncInfo
    paths: list[list[FuncCall]]


FuncDefs = NewType("FuncDefs", dict[str, FuncInfo])
VariableMap = NewType("VariableMap", dict[str, sp.Expr | None])


def program_generate_vcs(prog: Program) -> list[FunctionTest]:
    stdlib: Program = parse(stdlib_src)  # type: ignore
    env = VariableMap({})
    funcs = FuncDefs({})
    for name, val in stdlib:
        assert isinstance(val, EFuncDef)
        _, func_info = arguments_to_env_and_info(name, val, env)
        funcs[name] = func_info

    result: list[FunctionTest] = []

    for name, val in prog:
        match val:
            case EMeasureDef(_):
                assert False, "custom measures not supported yet"
            case EFuncDef(rec, typ, _):
                assert isinstance(typ, TFunc)

                arg_env, func_info = arguments_to_env_and_info(name, val, env)
                exec_body = get_program_body(val)

                if rec:
                    funcs[name] = func_info

                _, paths = expr_cost_spec(exec_body, arg_env, funcs)
                result.append(FunctionTest(name, func_info, paths))

                if not rec:
                    funcs[name] = func_info

    return result


# returns environment after introducing all arguments
# also collects argument information to construct FuncInfo
def arguments_to_env_and_info(
    funcname: str, expr: EFuncDef, env: VariableMap
) -> tuple[VariableMap, FuncInfo]:
    args: list[sp.Expr] = []
    typ = expr.typ
    last_spec: Spec | None = None
    last_size: Spec | None = None
    env = VariableMap(env.copy())

    while True:
        match typ:
            case TFunc(ident, arg_type, ret, time):
                match arg_type:
                    case TRefinement(_, dtype, _) | TBase(dtype):
                        assert (
                            isinstance(dtype, DeltaInt)
                            or isinstance(dtype, DeltaParam)
                            or isinstance(dtype, DeltaList)
                            or isinstance(dtype, DeltaArray)
                        ), f"dtype is {dtype}"
                        cur_var = create_fresh(f"{funcname}_{ident}")
                    case _:
                        assert False, "unimpl"

                args.append(cur_var)
                env[ident] = cur_var
                last_spec = time.spec
                last_size = time.size
                typ = ret
            case _:
                break

    assert last_spec is not None and last_size is not None
    last_spec_expr = spec_to_expr(last_spec, env)
    last_size_expr = spec_to_expr(last_size, env)

    info = FuncInfo(args, last_spec_expr, last_size_expr)
    return env, info


def get_program_body(func: EFuncDef) -> Expr:
    body = func.body
    while isinstance(body, EFunc):
        body = body.ret
    return body


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
        case SPMeasureCall(SPVar("len"), body):
            return spec_to_expr(body, env)
        case SPIte(cond, then, els):
            cond = spec_to_expr(cond, env)
            then = spec_to_expr(then, env)
            els = spec_to_expr(els, env)
            return (cond >> then) & ((~cond) >> els)
    assert False, f"{spec} unimpl"


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
    cur: Expr = expr
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

    assert len(args) == len(arg_values), "partial application not allowed"
    argmap = FuncArgsMap({arg: value for arg, value in zip(args, arg_values)})
    this_call = FuncCall(fname, argmap)
    return merge_product([[this_call]], costs)


def expr_cost_spec(
    expr: Expr, env: VariableMap, funcs: FuncDefs
) -> tuple[sp.Expr | None, list[list[FuncCall]]]:
    match expr:
        case EInt(x) | EBool(x):
            return sp.sympify(x), [[]]
        case EVar(var):
            return env[var], [[]]
        case ENil():
            return sp.sympify(1), [[]]
        case ECons(body):
            body_value, body_costs = expr_cost_spec(body, env, funcs)
            value = bind_opt(body_value, lambda x: x + 1)
            costs = body_costs
            return value, costs
        case EFuncDef(_) | EMeasureDef(_):
            assert False, "not allowed in function body"
        case ENot(body):
            body_val, body_costs = expr_cost_spec(body, env, funcs)
            value = bind_opt(body_val, lambda x: ~x)
            costs = body_costs
            return value, costs
        case EBinOp(op, left, right):
            left_value, left_costs = expr_cost_spec(left, env, funcs)
            right_value, right_costs = expr_cost_spec(right, env, funcs)
            value = eval_binop(op, left_value, right_value)
            costs = merge_product(left_costs, right_costs)
            return value, costs
        case EIte(cond, then, els):
            # TODO: implement computing the value of a conditional
            _, cond_costs = expr_cost_spec(cond, env, funcs)
            _, then_costs = expr_cost_spec(then, env, funcs)
            _, els_costs = expr_cost_spec(els, env, funcs)
            then_costs = merge_product(cond_costs, then_costs)
            els_costs = merge_product(cond_costs, els_costs)
            return None, then_costs + els_costs
        case ELet(rec, ident, typ, value, body):
            assert not rec, "recursive inner let not allowed"
            value_value, value_costs = expr_cost_spec(value, env, funcs)
            new_env = VariableMap(env.copy())
            new_env[ident] = value_value
            body_value, body_costs = expr_cost_spec(body, new_env, funcs)
            costs = merge_product(value_costs, body_costs)
            return body_value, body_costs
        case EFunc(_):
            assert False, "local functions not supported"
        case EFuncCall(EVar("len"), body):
            return expr_cost_spec(body, env, funcs)
        case EFuncCall(_):
            return None, cost_of_funccall(expr, env, funcs)
        case EMatch(value, clauses):
            value_value, value_costs = expr_cost_spec(value, env, funcs)
            paths: list[list[FuncCall]] = []
            for clause in clauses:
                local_env = VariableMap(env.copy())
                match clause.pat:
                    case PCons(PVar(hd), PVar(tl)):
                        local_env[hd] = None
                        local_env[tl] = bind_opt(value_value, lambda x: x - 1)
                    case PCons(PVar(hd1), PCons(PVar(hd2), PVar(tl))):
                        local_env[hd1] = None
                        local_env[hd2] = None
                        local_env[tl] = bind_opt(value_value, lambda x: x - 2)
                    case PVar(ident):
                        local_env[ident] = value_value
                    case _:
                        pvars = get_all_pvars(clause.pat)
                        for var in pvars:
                            local_env[var] = None
                _, local_costs = expr_cost_spec(clause.expr, local_env, funcs)
                paths.extend(merge_product(value_costs, local_costs))
            return None, paths
    assert False, f"{expr} is unmatched"


def get_all_pvars(pat: Pattern) -> list[str]:
    match pat:
        case PVar(ident):
            return [ident]
        case PAny() | PInt(_) | PBool(_) | PNil():
            return []
        case PCons(hd, tl):
            return get_all_pvars(hd) + get_all_pvars(tl)
        case PPair(l, r):
            return get_all_pvars(l) + get_all_pvars(r)
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

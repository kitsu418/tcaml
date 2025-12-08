import pytest
import z3
from verifier.smt import *

def test_basic_types():
    translator = Z3Translator()
    n = translator.n
    res_const = translator.translate(sp.sympify(10))
    assert isinstance(res_const, z3.RatNumRef)
    assert float(res_const.as_decimal(2)) == 10.0

    res_n = translator.translate(n)
    assert str(res_n) == 'n'

def test_arithmetic_add_mul():
    translator = Z3Translator()
    n = translator.n
    expr = 2 * n + 5
    z3_expr = translator.translate(expr)

    s = z3.Solver()
    s.add(z3.Real('n') == 10)
    s.add(z3_expr == 25)
    assert s.check() == z3.sat

def test_polynomial_exact_integer():
    translator = Z3Translator()
    n = translator.n
    expr = (2 * n + 1) ** 2
    z3_expr = translator.translate(expr)
    
    s = z3.Solver()
    s.add(z3.Real('n') == 2)
    s.add(z3_expr == 25)
    assert s.check() == z3.sat

def test_polynomial_ceil_exponent():
    translator = Z3Translator()
    n = translator.n
    expr = n ** 2.1
    z3_expr = translator.translate(expr)
    
    s = z3.Solver()
    s.add(z3.Real('n') == 2)
    s.add(z3_expr == 8)
    assert s.check() == z3.sat

def test_log_simple():
    translator = Z3Translator()
    n = translator.n
    expr = sp.log(n)
    z3_expr = translator.translate(expr)
    
    assert str(z3_expr) == 'log_n'

def test_log_with_multiplier():
    translator = Z3Translator()
    n = translator.n
    # log(2*n) -> log(2) + log(n)
    # Constant part: log(2) / log(2) = 1.0 (代码中常数除以 log(2))
    # Variable part: log(n) -> 1 * log_n
    # Result: 1.0 + log_n
    expr = sp.log(2 * n)
    z3_expr = translator.translate(expr)
    
    assert "log_n" in str(z3_expr)
    
    log_n_var = z3.Real('log_n')
    s = z3.Solver()
    s.add(log_n_var == 0)
    s.add(z3_expr == 1.0)
    assert s.check() == z3.sat

def test_log_dominant_term_selection():
    translator = Z3Translator()
    n = translator.n
    # Expr: log(n**2 + n)
    # Dominant term: n**2
    # Multiplier: 2
    # Overapprox: log(2 * n**2) = log(2) + 2*log(n)
    # Constant: log(2)/log(2) = 1
    # LogN coeff: 2
    # Result: 1 + 2*log_n
    expr = sp.log(n**2 + n)
    z3_expr = translator.translate(expr)
    
    log_n_var = z3.Real('log_n')
    s = z3.Solver()
    
    s.add(log_n_var == 10)
    s.add(z3_expr == 21.0)
    assert s.check() == z3.sat

def test_log_power_inside():
    translator = Z3Translator()
    n = translator.n
    # log(n^3) -> 3 * log(n)
    expr = sp.log(n**3)
    z3_expr = translator.translate(expr)
    
    log_n_var = z3.Real('log_n')
    s = z3.Solver()
    s.add(log_n_var == 1)
    s.add(z3_expr == 3.0)
    assert s.check() == z3.sat

def test_size_definition_substitution():
    translator = Z3Translator()
    m = sp.Symbol('m', positive=True)

    translator.set_size_definition(m / 2)
    
    expr = m + 1
    z3_expr = translator.translate(expr)
    
    s = z3.Solver()
    s.add(z3.Real('n') == 5)
    s.add(z3_expr == 11)
    assert s.check() == z3.sat
    
def test_exponential_complex_structure():
    """
    1. b^n
    2. b^(c*n)
    3. b^(n^k)
    4. b^(c*n^k)
    """
    translator = Z3Translator()
    n = translator.n
    
    pow_var = translator.get_exp_var(2)

    # 2^n -> pow_2_n
    expr_basic = 2**n
    z3_basic = translator.translate(expr_basic)
    assert str(z3_basic) == 'pow_2_n'

    # 2^(3n) -> 2^3 * pow_2_n = 8 * pow_2_n
    expr_linear_coeff = 2**(3*n)
    z3_linear = translator.translate(expr_linear_coeff)
    
    s = z3.Solver()
    s.add(pow_var == 10)
    s.add(z3_linear == 80)
    assert s.check() == z3.sat

    # 2^(n^2) -> (pow_2_n)^2
    expr_poly = 2**(n**2)
    z3_poly = translator.translate(expr_poly)
    
    s.reset()
    s.add(pow_var == 5)
    s.add(z3_poly == 25)
    assert s.check() == z3.sat

    # 2^(3*n^2) -> 2^3 * (pow_2_n)^2 = 8 * (pow_2_n)^2
    expr_poly_coeff = 2**(3 * n**2)
    z3_poly_coeff = translator.translate(expr_poly_coeff)
    
    s.reset()
    s.add(pow_var == 5)
    s.add(z3_poly_coeff == 200)
    assert s.check() == z3.sat

    # 2^(n^2.1) -> (pow_2_n)^3
    expr_ceil = 2**(n**2.1)
    z3_ceil = translator.translate(expr_ceil)
    
    s.reset()
    s.add(pow_var == 2)
    s.add(z3_ceil == 8)
    assert s.check() == z3.sat

def test_merge_sort_is_nlogn():
    funcs = ['mergesort', 'split', 'merge']
    translators = {fname: Z3Translator(fname) for fname in funcs}
    _len = sp.Function('len')
    mergesort_l = sp.Symbol('mergesort_l')
    split_l = sp.Symbol('split_l')
    merge_l1 = sp.Symbol('merge_l1')
    merge_l2 = sp.Symbol('merge_l2')
    sorted1 = sp.Symbol('sorted1')
    sorted2 = sp.Symbol('sorted2')
    mergesort_local_l1 = sp.Symbol('mergesort_local_l1')
    mergesort_local_l2 = sp.Symbol('mergesort_local_l2')

    value_map = {_len(merge_l1): _len(mergesort_l) / 2, _len(merge_l2): _len(mergesort_l) / 2, \
                 _len(sorted1): _len(mergesort_l) / 2, _len(sorted2): _len(mergesort_l) / 2, \
                 _len(split_l): _len(mergesort_l), \
                 _len(mergesort_local_l1): _len(mergesort_l) / 2, _len(mergesort_local_l2): _len(mergesort_l) / 2}
    
    translators['mergesort'].set_cost_template(_len(mergesort_l) * sp.log(_len(mergesort_l)), _len(mergesort_l))
    translators['split'].set_cost_template(_len(split_l), _len(split_l))
    translators['merge'].set_cost_template(_len(merge_l1) + _len(merge_l2), _len(merge_l1) + _len(merge_l2))
    mergesort_n = translators['mergesort'].n

    n_split_prime = translators['split'].get_n_sub_at_call({_len(split_l): _len(mergesort_l)}).subs({translators['mergesort'].size_expr: mergesort_n})
    n_mergesort_prime_1 = translators['mergesort'].get_n_sub_at_call({_len(mergesort_l): value_map[_len(mergesort_local_l1)]}).subs({translators['mergesort'].size_expr: mergesort_n})
    n_mergesort_prime_2 = translators['mergesort'].get_n_sub_at_call({_len(mergesort_l): value_map[_len(mergesort_local_l2)]}).subs({translators['mergesort'].size_expr: mergesort_n})
    n_merge = translators['merge'].get_n_sub_at_call({_len(merge_l1): value_map[_len(sorted1)], _len(merge_l2): value_map[_len(sorted2)]}).subs({translators['mergesort'].size_expr: mergesort_n})

    costs = [translators['split'].decompose_to_linear_combination(translators['split'].cost_expr, n_split_prime),
             translators['mergesort'].decompose_to_linear_combination(translators['mergesort'].cost_expr, n_mergesort_prime_1),
             translators['mergesort'].decompose_to_linear_combination(translators['mergesort'].cost_expr, n_mergesort_prime_2),
             translators['merge'].decompose_to_linear_combination(translators['merge'].cost_expr, n_merge)]
    
    costexpr = z3.Sum([c[0] for c in costs])
    coeffs = set()
    for c in costs:
        coeffs.update(c[1])

    s = z3.Solver()
    s.add(costexpr <= translators['mergesort'].decompose_to_linear_combination(translators['mergesort'].cost_expr)[0])
    s.add(z3.Real('n') >= 0)
    for coeff in coeffs:
        s.add(coeff >= 0)
    s.add(z3.Sum(coeffs) != 0)

    assert s.check() == z3.sat

def test_merge_sort_is_n():
    funcs = ['mergesort', 'split', 'merge']
    translators = {fname: Z3Translator(fname) for fname in funcs}
    _len = sp.Function('len')
    mergesort_l = sp.Symbol('mergesort_l')
    split_l = sp.Symbol('split_l')
    merge_l1 = sp.Symbol('merge_l1')
    merge_l2 = sp.Symbol('merge_l2')
    sorted1 = sp.Symbol('sorted1')
    sorted2 = sp.Symbol('sorted2')
    mergesort_local_l1 = sp.Symbol('mergesort_local_l1')
    mergesort_local_l2 = sp.Symbol('mergesort_local_l2')

    value_map = {_len(merge_l1): _len(mergesort_l) / 2, _len(merge_l2): _len(mergesort_l) / 2, \
                 _len(sorted1): _len(mergesort_l) / 2, _len(sorted2): _len(mergesort_l) / 2, \
                 _len(split_l): _len(mergesort_l), \
                 _len(mergesort_local_l1): _len(mergesort_l) / 2, _len(mergesort_local_l2): _len(mergesort_l) / 2}
    
    translators['mergesort'].set_cost_template(_len(mergesort_l), _len(mergesort_l))
    translators['split'].set_cost_template(_len(split_l), _len(split_l))
    translators['merge'].set_cost_template(_len(merge_l1) + _len(merge_l2), _len(merge_l1) + _len(merge_l2))
    mergesort_n = translators['mergesort'].n

    n_split_prime = translators['split'].get_n_sub_at_call({_len(split_l): _len(mergesort_l)}).subs({translators['mergesort'].size_expr: mergesort_n})
    n_mergesort_prime_1 = translators['mergesort'].get_n_sub_at_call({_len(mergesort_l): value_map[_len(mergesort_local_l1)]}).subs({translators['mergesort'].size_expr: mergesort_n})
    n_mergesort_prime_2 = translators['mergesort'].get_n_sub_at_call({_len(mergesort_l): value_map[_len(mergesort_local_l2)]}).subs({translators['mergesort'].size_expr: mergesort_n})
    n_merge = translators['merge'].get_n_sub_at_call({_len(merge_l1): value_map[_len(sorted1)], _len(merge_l2): value_map[_len(sorted2)]}).subs({translators['mergesort'].size_expr: mergesort_n})

    costs = [translators['split'].decompose_to_linear_combination(translators['split'].cost_expr, n_split_prime),
             translators['mergesort'].decompose_to_linear_combination(translators['mergesort'].cost_expr, n_mergesort_prime_1),
             translators['mergesort'].decompose_to_linear_combination(translators['mergesort'].cost_expr, n_mergesort_prime_2),
             translators['merge'].decompose_to_linear_combination(translators['merge'].cost_expr, n_merge)]
    
    costexpr = z3.Sum([c[0] for c in costs])
    coeffs = set()
    for c in costs:
        coeffs.update(c[1])

    s = z3.Solver()
    s.add(costexpr <= translators['mergesort'].decompose_to_linear_combination(translators['mergesort'].cost_expr)[0])
    s.add(z3.Real('n') >= 0)
    for coeff in coeffs:
        s.add(coeff > 0)
    s.add(z3.Sum(coeffs) != 0)

    assert s.check() == z3.unsat
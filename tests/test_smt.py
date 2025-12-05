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

import itertools
import math
import z3
import sympy as sp
from typing import Dict, Optional

class Z3Translator:
    def __init__(self, func: str = 'f'):
        self.n = sp.Symbol('n', positive=True)
        self.log_n_var = z3.Real(f'log_n')
        self.exp_vars = {}
        self.func = func
        
        self.subs_source: Optional[sp.Symbol] = None
        self.subs_target: Optional[sp.Expr] = None
    
    def set_size_definition(self, size_expr: sp.Expr):
        free_vars = set(size_expr.free_symbols)

        func_terms = [t for t in size_expr.atoms(sp.Function)]

        symbols_in_funcs = set()
        for fcall in func_terms:
            symbols_in_funcs |= fcall.free_symbols

        free_vars = (free_vars | set(func_terms)) - symbols_in_funcs
        
        if not free_vars:
            return
        
        free_vars = sorted(free_vars, key=lambda s: s.name)
        
        eq = sp.Eq(self.n, size_expr)
        for target_var in free_vars:
            try:
                res = sp.solve(eq, target_var)
                if res:
                    self.subs_source = target_var
                    self.subs_target = res[0]
                    break
            except:
                continue

    def set_cost_template(self, cost_expr: sp.Expr, size_expr: sp.Expr):
        self.cost_expr = cost_expr
        self.size_expr = size_expr
        self.set_size_definition(size_expr)
    
    def _to_n_domain(self, expr: sp.Expr) -> sp.Expr:
        if self.subs_source is None or self.subs_target is None:
            return expr

        need_substitute = False
        if isinstance(self.subs_source, sp.Symbol):
            if self.subs_source in expr.free_symbols:
                need_substitute = True
        else:
            if expr.has(self.subs_source):
                need_substitute = True

        if not need_substitute:
            return expr
        

        new_expr = expr.subs(self.subs_source, self.subs_target)

        return sp.simplify(new_expr)
            
    def _is_pure_n(self, expr: sp.Expr) -> bool:
        syms = expr.free_symbols
        if not syms or (len(syms) == 1 and self.n in syms):
            return True
        else:
            return False
    
    def get_exp_var(self, base: int) -> z3.ArithRef:
        if base not in self.exp_vars:
            self.exp_vars[base] = z3.Real(f'pow_{base}_n')
        return self.exp_vars[base]
    
    def constant_eval(self, expr: sp.Expr) -> float:
        if isinstance(expr, sp.log):
            return float((expr / sp.log(2)).evalf())
        else:
            if expr.is_Number:
                return float(expr.evalf())
            elif expr.is_Add:
                total = 0.0
                for arg in expr.args:
                    total += self.constant_eval(arg)
                return total
            elif expr.is_Mul:
                total = 1.0
                for arg in expr.args:
                    total *= self.constant_eval(arg)
                return total
            elif expr.is_Pow:
                base, exponent = expr.args
                return self.constant_eval(base) ** self.constant_eval(exponent)
            else:
                raise ValueError(f"Unsupported constant expression: {expr}")

    def translate(self, expr: sp.Expr) -> z3.ExprRef:      
        expr_transformed = sp.expand(self._to_n_domain(expr))
          
        if expr_transformed.is_constant():
            z3expr = z3.RealVal(self.constant_eval(expr_transformed))
        
        elif expr_transformed.is_Symbol:
            if expr_transformed == self.n:
                z3expr = z3.Real('n')
            else:
                raise ValueError(f"Unsupported form: {expr}")
         
        elif expr_transformed.is_Add:
            z3_sum = z3.RealVal(0)
            constant_acc = 0.0
            for arg in expr_transformed.args:
                if arg.is_constant():
                    constant_acc += self.constant_eval(arg)
                else:
                    z3_sum += self.translate(arg)
            if constant_acc != 0:
                z3_sum += constant_acc
            z3expr = z3_sum
            
        elif expr_transformed.is_Mul:
            res = self.translate(expr_transformed.args[0])
            constant_acc = 1.0
            for arg in expr_transformed.args[1:]:
                if arg.is_constant():
                    constant_acc *= self.constant_eval(arg)
                else:
                    res = res * self.translate(arg)
            if constant_acc != 1:
                res = res * constant_acc
            z3expr = res
            
        elif expr_transformed.is_Pow:
            base, exponent = expr_transformed.args
            
            # exponential: b^f(n)
            if base.is_constant() and exponent.has(self.n):
                z3expr = self._handle_exponential(base, exponent)
            # polynomial: f(n)^k
            elif exponent.is_constant() and base.has(self.n):
                z3expr = self._handle_polynomial(base, exponent)
            else:
                raise NotImplementedError(f"Unsupported power form: {expr_transformed}")
            
        elif isinstance(expr_transformed, sp.log):
            z3expr = self._handle_log(expr_transformed)
            
        else:
            raise NotImplementedError(f"Unsupported SymPy type: {type(expr_transformed)}: {expr_transformed}")
        
        return z3.simplify(z3expr)

    def _handle_log(self, expr: sp.Expr) -> z3.ArithRef:
        # apply over-approximation to the logarithmic argument by keeping only the dominant term
        # and dropping negative terms to construct a safe upper bound
        arg = expr.args[0]
        terms = sp.Add.make_args(arg) if arg.is_Add else [arg]
                    
        positive_terms = [t for t in terms if t.as_coeff_Mul()[0] >= 0]
        if not positive_terms:
            raise ValueError(f"Log argument has no positive terms: {expr}")
        
        # find the dominant term in the positive terms
        dominant_term = positive_terms[0]
        for term in positive_terms[1:]:
            try:
                ratio = sp.limit(term / dominant_term, self.n, sp.oo)
                if ratio == sp.oo:
                    dominant_term = term
                elif ratio != 0 and ratio.is_finite:
                    if abs(term.as_coeff_Mul()[0]) > abs(dominant_term.as_coeff_Mul()[0]):
                        dominant_term = term
            except:
                continue
        
        # log(multiplier * C * n^k + b^f(n)) -> log(C * multiplier) + k * log(n) + log(b) * f(n)
        overapprox = len(positive_terms) * dominant_term
        
        expanded = sp.expand(sp.log(overapprox))
        log_terms = sp.Add.make_args(expanded) if expanded.is_Add else [expanded]
        
        z3_sum = z3.RealVal(0)
        constant_acc = 0.0
        
        for term in log_terms:
            if term.is_constant():
                constant_acc += self.constant_eval(term)
                
            elif term.has(sp.log(self.n)):
                coeff = term / sp.log(self.n)
                
                if not coeff.is_constant():
                    raise ValueError(f"Non-constant coefficient for log(n): {coeff}")
                
                k = float(coeff.evalf())
                z3_sum += k * self.log_n_var
                
            elif term.has(self.n):
                z3_sum += self.translate(term)
                
            else:
                raise ValueError(f"Unsupported log term: {term}")
            
        if constant_acc > 0.0:
            z3_sum += constant_acc
        
        return z3_sum
            

    def _handle_polynomial(self, base: sp.Expr, exponent: sp.Expr) -> z3.ArithRef:
        base_z3 = self.translate(base)
        k = math.ceil(float(exponent.evalf()))
        return base_z3 ** k
        
    def _handle_exponential(self, base: sp.Expr, exponent: sp.Expr) -> z3.ArithRef:
        # b^(c*n^k) -> b^c * (b^n)^k
        pow_z3 = self.get_exp_var(self.constant_eval(base))
        if exponent.is_Mul:
            coeff, rest = exponent.as_coeff_Mul()
            if rest.has(self.n):
                if rest.is_Pow:
                    inner_base, inner_exponent = rest.args
                    if inner_base == self.n and inner_exponent.is_constant():
                        k = math.ceil(self.constant_eval(inner_exponent))
                        constant_part = base ** coeff
                        return z3.RealVal(self.constant_eval(constant_part)) * (pow_z3 ** k)
                elif rest == self.n:
                    constant_part = base ** coeff
                    return z3.RealVal(self.constant_eval(constant_part)) * pow_z3
                else:
                    raise NotImplementedError(f"Unsupported exponential form: base={base}, exponent={exponent}")
            else:
                raise NotImplementedError(f"Unsupported exponential form: base={base}, exponent={exponent}")
        elif exponent == self.n:
            return pow_z3
        elif exponent.is_Pow:
            inner_base, inner_exponent = exponent.args
            if inner_base == self.n and inner_exponent.is_constant():
                k = math.ceil(self.constant_eval(inner_exponent))
                return pow_z3 ** k
        else:
            raise NotImplementedError(f"Unsupported exponential form: base={base}, exponent={exponent}")

    def _apply_n_sub_to_factor(self, factor, n_sub):
        if factor.is_Number or factor.is_constant():
            return factor

        n = self.n

        if factor.is_Number:
            return factor
        
        ratio = sp.simplify(n_sub / n)
        diff = sp.simplify(n - n_sub)

        if factor == sp.log(n):
            if ratio.is_Rational and ratio > 0:
                k = 1 / ratio
                if k.is_Integer and k > 0:
                    return sp.log(n) - sp.log(k)
            else:
                raise ValueError(f"log(n) with substitution {n_sub} not supported")

        if factor.is_Pow:
            base, exp = factor.as_base_exp()
            if exp == n and base.is_Number:
                if diff.is_Rational:
                    if diff > 0:
                        k = 1 / diff
                        if k.is_Integer and k > 0:
                            return base**n / (base**k)
                    else:
                        raise ValueError(f"Non-positive diff in substitution: {n_sub}")
                    
        base, exp = factor.as_base_exp()
        if exp.is_Integer and exp >= 1:
            return n_sub**exp
        
        raise ValueError(f"Unsupported factor for n substitution: {factor}")

    def decompose_to_linear_combination(self, expr, apply_expr: sp.Expr | None = None):
        expanded_expr = sp.expand(self._to_n_domain(expr))

        if expanded_expr.is_Add:
            terms = expanded_expr.args
        else:
            terms = [expanded_expr]

        positive_terms = [t for t in terms if t.as_coeff_Mul()[0] > 0]

        if not positive_terms:
            return 0, sp.S.Zero
        
        dominant_term = positive_terms[0]
        for term in positive_terms[1:]:
            try:
                ratio = sp.limit(term / dominant_term, self.n, sp.oo)
                if ratio == sp.oo:
                    dominant_term = term
                elif ratio != 0 and ratio.is_finite:
                    pass
            except:
                continue
        
        _, core_term = dominant_term.as_coeff_Mul()

        if core_term.is_Mul:
            factors = core_term.args
        else:
            factors = [core_term]

        factor_chains = []

        for factor in factors:
            chain = []
            base, exp = factor.as_base_exp()

            if expr.is_constant():
                chain.append(factor)
            elif exp.is_Integer and exp > 0:
                for k in range(int(exp) + 1):
                    chain.append(base**k)
            else:
                chain = [factor, sp.S.One]
                
            factor_chains.append(chain)

        result_terms = []
        coeffs = []
        product = list(itertools.product(*factor_chains))
        product = sorted(product, key=lambda x: float(sp.Mul(*x).subs(self.n, 1000).evalf()))
        for combo in product:
            if apply_expr is not None:
                new_combo = []
                for factor in combo:
                    new_factor = self._apply_n_sub_to_factor(factor, apply_expr)
                    new_combo.append(new_factor)
                combo = new_combo
            term = self.translate(sp.Mul(*combo))
            coeff = z3.Real(f"c_{self.func}_{len(result_terms)}")
            coeffs.append(coeff)
            result_terms.append(coeff * term)

        return z3.Sum(result_terms), coeffs
    
    def _clone_for_call(self):
        clone = Z3Translator(func=self.func)
        clone.cost_expr = self.cost_expr
        clone.size_expr = self.size_expr
        return clone

    def get_n_sub_at_call(self, size_subs: Dict[sp.Expr, sp.Expr]) -> sp.Expr:
        if self.size_expr is None:
            raise ValueError("size_expr not set on translator")

        call_tr = self._clone_for_call()
        instantiated_size = call_tr.size_expr.xreplace(size_subs)
        n = call_tr.n
        phi_n = instantiated_size.xreplace({self.size_expr: n})

        return sp.simplify(phi_n)

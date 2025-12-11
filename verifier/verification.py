from verifier.vcgeneration import FunctionTest, FuncDefs
from verifier.smt import Z3Translator
import z3
import sympy as sp

def argument_domain_constraints(inequalities, translator: Z3Translator):
    constraints = []
    n = translator.n
    n_interval = sp.Interval(-sp.oo, sp.oo)

    for ineq in inequalities:
        if ineq.has(n):
            interval = sp.solveset(ineq, n, domain=sp.S.Reals)
            n_interval = n_interval.intersect(interval)
        else:
            raise NotImplementedError(f"Only inequalities involving 'n' are supported in argument domain constraints. Unsupported inequality: {ineq}")
    
    n_z3 = z3.Real('n')
    logn_z3 = translator.log_n_var
    exps_z3 = translator.exp_vars
    
    if n_interval.start.is_finite:
        lb = n_interval.start.evalf()
        if n_interval.left_open:
            constraints.append(n_z3 > lb)
            if n_interval.start > 0:
                constraints.append(logn_z3 > sp.log(n_interval.start, 2).evalf())
            for base, exp_var in exps_z3.items():
                constraints.append(exp_var > base ** lb)
        else:
            constraints.append(n_z3 >= lb)
            if n_interval.start > 0:
                constraints.append(logn_z3 >= sp.log(n_interval.start, 2).evalf())
            for base, exp_var in exps_z3.items():
                constraints.append(exp_var >= base ** lb)

    if n_interval.end.is_finite:
        ub = n_interval.end.evalf()
        if n_interval.right_open:
            constraints.append(n_z3 < ub)
            if n_interval.end > 0:
                constraints.append(logn_z3 < sp.log(n_interval.end, 2).evalf())
            for base, exp_var in exps_z3.items():
                constraints.append(exp_var < base ** ub)
        else:
            constraints.append(n_z3 <= ub)
            if n_interval.end > 0:
                constraints.append(logn_z3 <= sp.log(n_interval.end, 2).evalf())
            for base, exp_var in exps_z3.items():
                constraints.append(exp_var <= base ** ub)
                
    return z3.And(constraints)

def verify_function(func_test: FunctionTest, funcs: FuncDefs) -> bool:
    translators = {}
    
    main_translator = Z3Translator(func_test.name)
    main_translator.set_cost_template(func_test.info.timespec, func_test.info.size)
    translators[func_test.name] = main_translator
    
    for path in func_test.paths:
        costs = []
        all_coeffs = set()
        dominant_coeffs = set()
        s = z3.Solver()
        argument_constraints = []

        for call in path:
            if call.func_name not in funcs:
                raise ValueError(f"Function {call.func_name} not found in FuncDefs")
                
            callee_info = funcs[call.func_name]
            
            if call.func_name not in translators:
                t = Z3Translator(call.func_name)
                t.set_cost_template(callee_info.timespec, callee_info.size)
                translators[call.func_name] = t
            
            callee_tr = translators[call.func_name]
            
            # Substitute args into callee size expression
            size_in_n = main_translator._to_n_domain(callee_tr.get_n_sub_at_call(call.args))

            if not size_in_n.has(main_translator.n):
                raise NotImplementedError("Multiple input sizes is not supported.")

            ineq = sp.Ge(size_in_n, 0)
            if ineq.is_Relational:
                argument_constraints.append(sp.Ge(size_in_n, 0))
            
            # Decompose cost
            cost_z3, (spec_coeffs, dominant_coeff) = callee_tr.decompose_to_linear_combination(callee_tr.cost_expr, size_in_n)
            costs.append(cost_z3)
            all_coeffs.update(spec_coeffs)
            dominant_coeffs.add(dominant_coeff)
            
        # Main spec cost (RHS)
        spec_z3, (spec_coeffs, dominant_coeff) = main_translator.decompose_to_linear_combination(main_translator.cost_expr)
        all_coeffs.update(spec_coeffs)
        dominant_coeffs.add(dominant_coeff)

        n_z3 = z3.Real('n')
        logn_z3 = main_translator.log_n_var
        const = z3.Real('const')
        s.add(const > 0)

        lhs = z3.Sum(costs) if costs else z3.RealVal(0)
        lhs += const
        rhs = spec_z3

        vars = list(main_translator.exp_vars.values()) + [main_translator.log_n_var] + [n_z3]
        domain = z3.And([v >= 0 for v in vars])
        domain = z3.And(domain, logn_z3 < n_z3)

        for base, exp_var in main_translator.exp_vars.items():
            if base < 2:
                raise ValueError("Exponential base must be greater than or equal to 2.")
            else:
                domain = z3.And(domain, exp_var > n_z3)
        
        if argument_constraints:
            domain = z3.And(domain, 
                            argument_domain_constraints(argument_constraints, main_translator))
        
        s.add(z3.ForAll(vars, z3.Implies(domain, lhs <= rhs)))
        
        for coeff in all_coeffs:
            if coeff in dominant_coeffs:
                s.add(coeff > 0)
            else:
                s.add(coeff >= 0)
        
        if s.check() != z3.sat:
            return False
            
    return True
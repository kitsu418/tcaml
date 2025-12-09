from verifier.vcgeneration import FunctionTest, FuncDefs
from verifier.smt import Z3Translator
import z3
import sympy as sp

def verify_function(func_test: FunctionTest, funcs: FuncDefs) -> bool:
    translators = {}
    
    main_translator = Z3Translator(func_test.name)
    main_translator.set_cost_template(func_test.info.timespec, func_test.info.size)
    translators[func_test.name] = main_translator
    
    for path in func_test.paths:
        costs = []
        all_coeffs = set()

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
            s.add(callee_tr.translate(size_in_n) >= 0)
            
            # Decompose cost
            cost_z3, coeffs = callee_tr.decompose_to_linear_combination(callee_tr.cost_expr, size_in_n)
            costs.append(cost_z3)
            all_coeffs.update(coeffs)
            
        # Main spec cost (RHS)
        spec_z3, spec_coeffs = main_translator.decompose_to_linear_combination(main_translator.cost_expr)
        all_coeffs.update(spec_coeffs)

        s = z3.Solver()
        n_z3 = z3.Real('n')
        
        o1 = z3.Real('const')
        s.add(o1 > 0)

        lhs = z3.Sum(costs) if costs else z3.RealVal(0)
        lhs += o1
        rhs = spec_z3
        
        s.add(z3.ForAll([n_z3], z3.Implies(n_z3 >= 0, lhs <= rhs)))
        
        for coeff in all_coeffs:
            s.add(coeff > 0)
        
        if s.check() != z3.sat:
            return False
            
    return True
let rec fib (n : {v: int | v >= 1}) : int @ O(2^n) =
  match n with
  | 1 -> 1
  | 2 -> 1
  | n -> fib (n - 1) + fib (n - 2)

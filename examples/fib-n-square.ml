let rec fib (n : {v: int | v >= 1}) : int @ O(n^2) measure [n] =
  match n with
  | 1 -> 1
  | 2 -> 1
  | n -> fib (n - 1) + fib (n - 2)

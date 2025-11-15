let rec insertion_sort (nums: int list): {v: int list | len v = len nums} @ O((len nums)^2) =
  let rec insert (x: int) (l: int list): {v: int list | len v = len l + 1} =
    match l with
    | [] -> x :: [],
    | hd :: tl ->
        if x < hd
          then x :: l
          else hd :: insert x tl
  in
    match nums with
    | [] -> []
    | hd :: tl -> insert hd (insertion_sort tl)

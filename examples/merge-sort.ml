let rec split (l: int list): (int list * int list) @ O(len l) measure (len l) =
  match l with
  | [] -> ([], [])
  | [x] -> ([x], [])
  | x :: y :: zs ->
    let (l1, l2) = split zs in
      (x :: l1, y :: l2);

let rec merge (l1: int list) (l2: int list): {v: int list | len v = len l1 + len l2} @ O(len l1 + len l2) measure (len l1 + len l2) =
  match (l1, l2) with
  | ([], l2) -> l2
  | (l1, []) -> l1
  | (h1 :: t1, h2 :: t2) ->
    if h1 <= h2 then
      h1 :: (merge t1 l2)
    else
      h2 :: (merge l1 t2);

let rec mergesort (l: {v: int list | len v >= 0}): {v: int list | len v = len l} @ O(len l * log(len l)) measure (len l) =
  match l with
  | [] -> []
  | [_] -> l
  | _ ->
    let (l1, l2) = split l in
      let sorted1 = mergesort l1 in
        let sorted2 = mergesort l2 in
          merge sorted1 sorted2

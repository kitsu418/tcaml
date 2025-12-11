let rec insert (x: int) (l: int list) : {v: int list | len v = len l + 1} @ O(len l) measure [len l] =
  match l with
  | [] -> x :: []
  | hd :: tl ->
      if x < hd
        then x :: l
        else hd :: insert x tl;

let rec insertion_sort (nums: int list): {v: int list | len v = len nums} @ O((len nums) * log (len nums)) measure [len nums] =
  match nums with
  | [] -> []
  | hd :: tl -> insert hd (insertion_sort tl)

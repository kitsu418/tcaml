let rec search (nums : int list) (l : int) (r : int) : int @ O(log (r - l)) =
  if l > r then
    -1
  else
    let m: int = (l + r) / 2 in
    let v: int = readList nums m in
    if x = v then
      m
    else if x < v then
      search nums l (m - 1)
    else
      search nums (m + 1) r;

let binary_search_list (nums : int list) (x : int) : int @ O((len nums) * log(len nums)) = 
  let n = len nums in
  search nums 0 (n - 1)

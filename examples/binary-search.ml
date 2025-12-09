let rec search (nums: int array) (l: int) (r: int) (x: int): int @ O(log (r - l)) measure [r - l] =
  if l > r then
    -1
  else
    let m: int = (l + r) / 2 in
    let v: int = readArray nums m in
    if x = v then
      m
    else (if x < v then
      search nums l (m - 1) x
    else
      search nums (m + 1) r x);

let binary_search (nums: int array) (x: int): int @ O(log (len nums)) measure [len nums] = 
  let n: int = len nums in
  search nums 0 (n - 1) x

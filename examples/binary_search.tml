let binary_search (nums: int array) (x: int): int @ O(log (len nums)) = 
  let rec search (l: int) (r: int): int @ O(log (r - l)) =
    if l > r then
      -1
    else
      let m: int = (l + r) / 2 in
      let v: int = readArray nums m in
      if x == v then
        m
      else if x < v then
        search l (m - 1)
      else
        search (m + 1) r
  in
    let n: int = len nums in
      search 0 (n - 1)
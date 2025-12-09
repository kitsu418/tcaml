let rec binExpo (a: int) (n: int) : int @ O(log n) measure n = 
  if n = 0 then
    1 
  else 
    let mul = binExpo a (n / 2) in 
    if (n mod 2) = 1 then
      a * mul * mul 
    else
      mul * mul

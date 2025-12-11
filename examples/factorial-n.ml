let rec factorial (n : {v : int | v >= 0}) : int @ O(n) measure [n] = 
  if n = 0 then 1 
  else n * factorial (n-1)


let swap (arr: int array) (x: int) (y: int): {v: int array | len v = len arr} @ O(len arr) =
  let old_x = readArray arr x in
  let old_y = readArray arr y in
  let write1 = writeArray arr x old_y in
  writeArray write1 y old_x;
  
let rec sift_down (arr: int array) (root: int): {v: int array | len v = len arr}
    @ O((len arr) * log(len arr)) = 
  let n: int = len arr in
  let left: int = 2 * root in
  let right: int = 2 * root + 1 in
  if left < n then
    let bigger_child: int =
      if right < n && (readArray arr left) < (readArray arr right) then
        right
      else
        left
     in
       let swapped_arr: {v: int array | len v = len arr}
         = swap arr root bigger_child in
       shift_down swapped_arr bigger_child
  else arr;

let rec part (xs: int array) (iter: int): {v: int array | len v = len xs} 
    @ O((iter + 1) * (len xs) * log(len xs)) =
  let n: int = len xs in
  let root: int = n - 1 - iter in
  if root < 0
    then xs
    else part (sift_down xs root) (root - 1);

let heapify (arr: int array): int array @ O((len arr)^2 * log(len arr)) =
  part arr 0

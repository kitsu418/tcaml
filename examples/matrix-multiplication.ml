measure num_rows (mat: int array array) : int =
  len mat;

measure num_cols (mat: int array array) : int =
  if num_rows mat > 0 then len (select mat 0) else 0;

measure is_matrix (mat: int array array) : bool =
  if num_rows mat == 0 then
    true
  else
    forall i. i >= 0 && i < num_rows mat ==> len (select mat i) == num_cols mat;

let matmul
  (a: {a: int array array | num_rows a > 0 && num_cols a > 0 && is_matrix a})
  (b: {b: int array array | num_rows b == num_cols a && num_cols b > 0 && is_matrix b})
  : {c: int array array | num_rows c == num_rows a && num_cols c == num_cols b && is_matrix c}
  @ O((num_rows a) * (num_cols a) * (num_cols b))
=
  let m = num_rows a in
  let n = num_cols a in
  let p = num_cols b in

  let dot_product (v1: int array) (v2: {v2: int array | len v2 == len v1}) : int @ O(len v1) =
    let rec loop (i: int) (acc: int) @ O(len v1 - i) =
      if i >= len v1 then
        acc
      else
        loop (i + 1) (acc + (readArray v1 i) * (readArray v2 i))
    in
    loop 0 0
  in

  let get_col (mat: int array array) (j: int): int array @ O(num_rows mat) =
    let col = newArray (num_rows mat) 0 in
    let rec fill_col (arr: int array) (i: {v: int | (len arr) + i == num_rows mat})
      : int array @ O((len arr) - i) =
      if i >= num_rows mat then
        arr
      else
        fill_col (writeArray arr i (readArray (readArray mat i) j)) (i + 1)
    in
      fill_col col 0
  in

  let result = newArray m (newArray p 0) in
  let rec fill_result (i: {v: int | v >= 0 && v < m}): int array array @ O((m - i) * p * n) =
    if i >= m then
      result
    else
      let rec fill_row (j: {v: int | v >= 0 && v < p}): int array array @ O((p - j) * n) =
        if j >= p then
          fill_result (i + 1)
        else
          let col_b = get_col b j in
          let value = dot_product (readArray a i) col_b in
          let updated_row = writeArray (readArray result i) j value in
          let updated_result = writeArray result i updated_row in
          fill_row (j + 1)
      in
        fill_row 0
  in
    fill_result 0


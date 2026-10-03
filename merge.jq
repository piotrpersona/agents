# Deep-merge two settings objects. Objects recurse, arrays concatenate
# (so hook events contribute entries from both files), scalars take $b.
def dm($a; $b):
  if   ($a|type) == "object" and ($b|type) == "object" then
    reduce (($a + $b) | keys_unsorted[]) as $k ({};
      .[$k] = (if   ($a|has($k)) and ($b|has($k)) then dm($a[$k]; $b[$k])
               elif ($b|has($k))                  then $b[$k]
               else                                    $a[$k] end))
  elif ($a|type) == "array" and ($b|type) == "array" then $a + $b
  else $b end;
dm(.[0]; .[1])

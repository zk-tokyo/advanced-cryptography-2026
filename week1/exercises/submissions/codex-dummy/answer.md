# Toy Commitment Answer

For the commitment `Com(m; r) = H(m || r)`, binding means that after a
commitment value `c` is published, it should be infeasible to find two different
openings `(m, r)` and `(m', r')` that both verify to the same `c`.

If an adversary can open the same commitment in two different ways, then:

```text
H(m || r) = c = H(m' || r')
```

Assuming the encoding of `m || r` is unambiguous and the two openings are truly
different, the two inputs to `H` are different strings with the same hash output.
That is exactly a collision in `H`. Therefore, an adversary that breaks binding
for this toy construction can be used to find a collision in the hash function.

This toy construction has limitations. It does not automatically prove hiding,
and real protocols should be careful about unambiguous encoding, length
prefixing, and domain separation.

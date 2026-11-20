"""Reproduce the illustrative pooled-binomial values of Decision C9 with the known-coverage helper and confirm each N by exact rational tails.
These are validation values for the search and distribution code. They are NOT the stratified procedure and NOT planning values."""
import math
import sys
import time
from fractions import Fraction

sys.dont_write_bytecode = True
sys.path.insert(0, ".")
from hammer_pilot import sizing_c9 as z

TABLE = [(16, 0.10, 0.10), (16, 0.10, 0.05), (32, 0.10, 0.10), (32, 0.10, 0.05), (32, 0.20, 0.10), (32, 0.20, 0.05),
         (100, 0.10, 0.10), (100, 0.10, 0.05), (100, 0.30, 0.10), (100, 0.30, 0.05)]
print("m    c     beta  N(search)  P(N)      exact: P(N-1)<1-beta<=P(N)   N=ceil(m/c)  P(ceil(m/c))")
t0 = time.time()
for m, c, beta in TABLE:
    r = z.size_known_coverage({"S": 100_000}, {"S": 0}, {"S": c}, m_prime=m, beta=beta, n_max=2600)
    n = r["N"]
    cf = Fraction(str(c))
    thr = 1 - Fraction(str(beta))
    tail = lambda k: sum(math.comb(k, j) * cf ** j * (1 - cf) ** (k - j) for j in range(m, k + 1))
    exact_ok = tail(n - 1) < thr <= tail(n)
    nm = math.ceil(m / c)
    print(f"{m:<5}{c:<6}{beta:<6}{n:<11}{r['probability_at_N']:.4f}    {str(exact_ok):<28}{nm:<12}{z.tail_probability(z.binomial_pmf(nm, c), m):.4f}")
print(f"elapsed {time.time() - t0:.1f}s")

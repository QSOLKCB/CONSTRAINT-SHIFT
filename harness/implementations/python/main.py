import sys

tokens = [int(token) for token in sys.stdin.buffer.read().split()]
n, values = tokens[0], tokens[1:]
if not 0 <= n <= 64 or len(values) != n or any(abs(x) > 1000 for x in values):
    sys.exit(2)
print(n, sum(values), sum(x * x for x in values))

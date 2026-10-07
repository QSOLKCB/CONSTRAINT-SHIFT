import sys

def decimal(token):
    negative = token.startswith(b"-")
    digits = token[1:] if token.startswith((b"+", b"-")) else token
    value = int(digits.lstrip(b"0") or b"0")
    return -value if negative else value


tokens = [decimal(token) for token in sys.stdin.buffer.read().split()]
n, values = tokens[0], tokens[1:]
if not 0 <= n <= 64 or len(values) != n or any(abs(x) > 1000 for x in values):
    sys.exit(2)
print(n, sum(values), sum(x * x for x in values))

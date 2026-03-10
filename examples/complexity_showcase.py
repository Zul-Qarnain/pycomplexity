"""
One example of every complexity class.
Run: bigopy analyze examples/complexity_showcase.py
"""


def constant(x, y):             # O(1)
    return x + y


def logarithmic(n):              # O(log n)
    i = 1
    while i < n:
        i = i * 2


def linear(arr):                 # O(n)
    return sum(arr)


def linearithmic(arr):           # O(n log n)
    return sorted(arr)


def quadratic(arr):              # O(n²)
    n = len(arr)
    for i in range(n):
        for j in range(n):
            pass


def cubic(arr):                  # O(n³)
    n = len(arr)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                pass


def exponential(n):              # O(2^n)
    if n <= 1:
        return n
    return exponential(n-1) + exponential(n-2)

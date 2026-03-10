"""
examples/demo_algorithms.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A showcase of algorithms at every complexity class.
Run:  pycomplexity analyze examples/demo_algorithms.py --verbose
"""


# ──────────────────────────────────────────────────────────────────────────────
# O(1) examples
# ──────────────────────────────────────────────────────────────────────────────

def get_first(arr):
    """Return the first element – O(1)."""
    return arr[0]


def is_even(n):
    """Bitwise even check – O(1)."""
    return (n & 1) == 0


# ──────────────────────────────────────────────────────────────────────────────
# O(log n) examples
# ──────────────────────────────────────────────────────────────────────────────

def binary_search(arr, target):
    """Classic binary search – O(log n)."""
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def count_digits(n):
    """Count digits by repeated halving – O(log n)."""
    count = 0
    while n > 0:
        n = n // 10
        count += 1
    return count


# ──────────────────────────────────────────────────────────────────────────────
# O(n) examples
# ──────────────────────────────────────────────────────────────────────────────

def find_max(arr):
    """Linear scan for maximum – O(n)."""
    best = arr[0]
    for x in arr:
        if x > best:
            best = x
    return best


def reverse_list(arr):
    """Reverse by building a new list – O(n)."""
    result = []
    for i in range(len(arr) - 1, -1, -1):
        result.append(arr[i])
    return result


# ──────────────────────────────────────────────────────────────────────────────
# O(n log n) examples
# ──────────────────────────────────────────────────────────────────────────────

def merge_sort(arr):
    """Classic merge sort – O(n log n)."""
    if len(arr) <= 1:
        return arr
    mid   = len(arr) // 2
    left  = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return _merge(left, right)


def _merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def sort_and_deduplicate(arr):
    """Sort then deduplicate – O(n log n)."""
    s = sorted(arr)
    unique = [s[0]]
    for i in range(1, len(s)):
        if s[i] != s[i - 1]:
            unique.append(s[i])
    return unique


# ──────────────────────────────────────────────────────────────────────────────
# O(n²) examples
# ──────────────────────────────────────────────────────────────────────────────

def bubble_sort(arr):
    """Bubble sort – O(n²)."""
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def selection_sort(arr):
    """Selection sort – O(n²)."""
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr


# ──────────────────────────────────────────────────────────────────────────────
# O(n³) example
# ──────────────────────────────────────────────────────────────────────────────

def naive_matrix_multiply(A, B):
    """Naive matrix multiplication – O(n³)."""
    n = len(A)
    C = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]
    return C


# ──────────────────────────────────────────────────────────────────────────────
# O(2^n) examples
# ──────────────────────────────────────────────────────────────────────────────

def fibonacci(n):
    """Naive Fibonacci – O(2^n)."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def generate_subsets(arr):
    """All subsets via recursion – O(2^n)."""
    if not arr:
        return [[]]
    rest = generate_subsets(arr[1:])
    return rest + [[arr[0]] + s for s in rest]

"""
tests/fixtures/algorithms.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Reference algorithms used as test fixtures.
Each function is annotated with its expected complexity class.
"""

# ─────────────────────────────────────────────────────────────────────────────
# O(1) – constant time
# ─────────────────────────────────────────────────────────────────────────────

def constant_lookup(d, key):           # expected: O(1)
    return d.get(key, None)


def swap(a, b):                        # expected: O(1)
    return b, a


# ─────────────────────────────────────────────────────────────────────────────
# O(log n) – logarithmic
# ─────────────────────────────────────────────────────────────────────────────

def binary_search(arr, target):        # expected: O(log n)
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


def power_of_two(n):                   # expected: O(log n)
    count = 0
    while n > 1:
        n = n // 2
        count += 1
    return count


# ─────────────────────────────────────────────────────────────────────────────
# O(n) – linear
# ─────────────────────────────────────────────────────────────────────────────

def linear_search(arr, target):        # expected: O(n)
    for item in arr:
        if item == target:
            return True
    return False


def compute_sum(arr):                  # expected: O(n)
    total = 0
    for x in arr:
        total += x
    return total


# ─────────────────────────────────────────────────────────────────────────────
# O(n log n) – linearithmic
# ─────────────────────────────────────────────────────────────────────────────

def merge_sort(arr):                   # expected: O(n log n)
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
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


def sort_and_count(arr):               # expected: O(n log n) via sorted()
    s = sorted(arr)
    return len(s)


# ─────────────────────────────────────────────────────────────────────────────
# O(n²) – quadratic
# ─────────────────────────────────────────────────────────────────────────────

def bubble_sort(arr):                  # expected: O(n²)
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def has_duplicate(arr):                # expected: O(n²)
    n = len(arr)
    for i in range(n):
        for j in range(i + 1, n):
            if arr[i] == arr[j]:
                return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# O(n³) – cubic
# ─────────────────────────────────────────────────────────────────────────────

def triple_sum(arr, target):           # expected: O(n³)
    n = len(arr)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if arr[i] + arr[j] + arr[k] == target:
                    return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# O(2^n) – exponential
# ─────────────────────────────────────────────────────────────────────────────

def fibonacci_naive(n):                # expected: O(2^n)
    if n <= 1:
        return n
    return fibonacci_naive(n - 1) + fibonacci_naive(n - 2)


def all_subsets(arr):                  # expected: O(2^n)
    if not arr:
        return [[]]
    rest = all_subsets(arr[1:])
    return rest + [[arr[0]] + s for s in rest]

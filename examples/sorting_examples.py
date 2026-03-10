"""
Sorting algorithm examples
Run: pycomplexity analyze examples/sorting_examples.py --verbose
"""


def bubble_sort(arr):
    """O(n²) — doubly nested loops"""
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def merge_sort(arr):
    """O(n log n) — divide and conquer"""
    if len(arr) > 1:
        mid   = len(arr) // 2
        left  = arr[:mid]
        right = arr[mid:]
        merge_sort(left)
        merge_sort(right)
        i = j = k = 0
        while i < len(left) and j < len(right):
            if left[i] < right[j]:
                arr[k] = left[i]; i += 1
            else:
                arr[k] = right[j]; j += 1
            k += 1
        while i < len(left):
            arr[k] = left[i]; i += 1; k += 1
        while j < len(right):
            arr[k] = right[j]; j += 1; k += 1


def binary_search(arr, target):
    """O(log n) — halving search space"""
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:   return mid
        elif arr[mid] < target:  lo = mid + 1
        else:                    hi = mid - 1
    return -1

import numpy as np


def calculate_mse(
    sequence1: list[float],
    sequence2: list[float],
) -> float:
    if len(sequence1) != len(sequence2):
        raise ValueError("Input lengths must match.")
    if len(sequence1) == 0:
        raise ValueError("Input sequences must not be empty.")

    x1 = np.asarray(sequence1, dtype=float)
    x2 = np.asarray(sequence2, dtype=float)
    return float(np.mean((x1 - x2) ** 2))


def calculate_normalized_mse(
    sequence1: list[float],
    sequence2: list[float],
) -> float:
    if len(sequence1) != len(sequence2):
        raise ValueError("Input lengths must match.")
    if len(sequence1) == 0:
        raise ValueError("Input sequences must not be empty.")

    x1 = np.asarray(sequence1, dtype=float)
    x2 = np.asarray(sequence2, dtype=float)

    if np.any(x2 == 0):
        raise ValueError("sequence2 contains zero; normalized MSE is undefined.")

    return float(np.mean(((x1 - x2) / x2) ** 2))
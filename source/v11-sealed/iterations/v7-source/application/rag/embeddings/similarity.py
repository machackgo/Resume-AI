"""Cosine accepts unnormalized finite vectors; zero vectors are invalid."""
import math


def validate(vector, dimension=None):
    values = tuple(vector)
    if not values or (dimension is not None and len(values) != dimension):
        raise ValueError('empty vector or dimension mismatch')
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise ValueError('vector must contain finite real numbers')
    if not any(values):
        raise ValueError('zero vector has undefined cosine')
    return values


def normalize(vector):
    values = validate(vector)
    scale = max(abs(v) for v in values)
    scaled = tuple(v / scale for v in values)
    norm = math.sqrt(math.fsum(v*v for v in scaled))
    return tuple(v / norm for v in scaled)


def cosine(left, right):
    left = validate(left)
    right = validate(right, len(left))
    score = math.fsum(a*b for a,b in zip(normalize(left), normalize(right)))
    return max(-1.0, min(1.0, score))

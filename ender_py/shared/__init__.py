import os
from typing import Callable, Any
from functools import wraps
import hashlib


def to_hashable(some: Any):
    s = f"{repr(some)}|{type(some).__name__}"
    return hashlib.sha256(s.encode()).hexdigest()


def find_file(directory: str, target_file: str):
    """
    Search for a file in a directory and its subdirectories.

    Args:
        directory (str): The path of the directory to search.
        target_file (str): The name of the file to search for.

    Returns:
        str: The full path of the file if found, otherwise None.
    """
    for root, _, files in os.walk(directory):
        if target_file in files:
            return os.path.join(root, target_file)
    return None


def cache(func: Callable[..., Any]):
    seen: dict[str, Any] = {}
    # hit: int = 0
    # miss = 0

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        # nonlocal hit, miss
        key = to_hashable(args) + "-" + to_hashable(tuple(sorted(kwargs.items())))
        if key in seen:
            # hit += 1
            return seen[key]
        # miss += 1

        output = func(*args, **kwargs)
        seen[key] = output
        # print("|", len(seen), hit, miss, func.__name__)
        return output

    return wrapper


from .logging import *
from .image_compression import *

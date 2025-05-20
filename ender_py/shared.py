from typing import overload, NoReturn, Literal
import os


import traceback


def print_traceback(traces_to_skip: int = 2):
    tb = traceback.extract_stack()[:-traces_to_skip]  # I love magic functions
    formatted = traceback.format_list(tb)
    print("[ERROR TRACEBACK]:\n>" + ">".join(formatted))


@overload
def log(level: Literal[4], message: str) -> NoReturn: ...


@overload
def log(level: int, message: str) -> None: ...


def log(level: int, message: str):
    if level == 0:
        print(f"[INFO] {message}")
    elif level == 1:
        print(f"[INFO] {message}")
    elif level == 2:
        print(f"[WARNING] {message}")
    elif level == 3:
        print(f"[ERROR] {message}")
    elif level == 4:
        print(f"[FATAL ERROR] {message}")
        print_traceback()
        quit(1)


DEBUG = 0
INFO = 1
WARNING = 2
ERROR = 3
FATAL = 4


def jp(*args) -> str:
    "Join path, not Japan"
    return os.path.join(*args)


def get_file_contents(path: str) -> str:
    # if not os.path.exists(path):
    #     log(FATAL, f"File {path} does not exist")
    with open(path, "r") as f:
        return f.read()


def replace(string: str, what_to: dict[str, str]):
    for key, value in what_to.items():
        string = string.replace("{" + str(key) + "}", value)
    return string


def dynamic_serializer(obj):
    if hasattr(obj, "__json__"):
        return obj.__json__()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


import inspect


def export_class(obj: object):
    """Exports an object's attributes as a dictionary."""
    export = {}
    if hasattr(obj, "__slots__"):
        for slot in obj.__slots__:  # type: ignore
            export[slot] = getattr(obj, slot, None)
    else:  # Fallback to __dict__ if __slots__ not defined
        export = obj.__dict__.copy()
    return export


def import_class(obj: type, data: dict):
    """Creates a new instance of cls with attributes from data."""
    init_params = {
        k: v
        for k, v in inspect.signature(obj.__init__).parameters.items()
        if k != "self"
    }

    init_args = {k: data[k] for k in init_params if k in data}
    remaining_attrs = {k: v for k, v in data.items() if k not in init_params}

    new_instance = obj(**init_args)

    for key, value in remaining_attrs.items():
        setattr(new_instance, key, value)

    return new_instance

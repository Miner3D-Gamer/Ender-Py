from typing import (
    overload,
    NoReturn,
    Literal,
    Union,
    Any,
    Optional,
    Protocol,
    runtime_checkable,
    Callable,
    Type,
)


@runtime_checkable
class JsonLike(Protocol):
    __json__: Any


@runtime_checkable
class ObjectWithSlots(Protocol):
    __slots__: list[str]


import os


import traceback
import inspect
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from . import Mod
    from .components import Texture


def print_traceback(traces_to_skip: int = 2):
    tb = traceback.extract_stack()[:-traces_to_skip]  # I love magic functions
    formatted = traceback.format_list(tb)
    print("[ERROR TRACEBACK]:\n>" + ">".join(formatted))


import hashlib


def to_hashable(some: Any):
    s = f"{repr(some)}|{type(some).__name__}"
    return hashlib.sha256(s.encode()).hexdigest()


from functools import wraps
from typing import Callable


def unique_inputs_only(func: Callable[..., Any]):
    seen: set[Any] = set()

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        key = (to_hashable(args), tuple(sorted(kwargs.items())))
        if key in seen:
            return None  # Or raise an exception if you prefer
        seen.add(key)
        return func(*args, **kwargs)

    return wrapper


@overload
def log(level: Literal[4], message: str | list[str]) -> NoReturn: ...


@overload
def log(level: int, message: str | list[str]) -> None: ...


@unique_inputs_only
def log(
    level: int, message: str | list[str]
):  # Oh shit the refactor to support lists worked first try wtf
    if isinstance(message, str):
        message = [message]
    levels = [
        ("DEBUG", (128, 128, 128)),
        ("INFO", (50, 172, 244)),
        ("WARNING", (255, 204, 80)),
        ("ERROR", (255, 30, 152)),
        ("FATAL ERROR", (204, 0, 0)),
    ]
    chosen = levels[level]
    message_insert = "[%s] " % chosen[0]
    further_insert = " " * len(message_insert)
    title = message[0]
    buffer = "\n".join(
        [message_insert + title] + [further_insert + x for x in message[1:]]
    )
    print(color_text(buffer, *chosen[1]))

    if level == len(levels) - 1:
        print_traceback()
        quit(1)


DEBUG = 0
INFO = 1
WARNING = 2
ERROR = 3
FATAL = 4


def color_text(text: str, r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m{text}\x1b[0m"


texture_type: TypeAlias = Union[
    str,
    dict[str, str],
    dict[
        Literal[
            "top",
            "bottom",
            "north",
            "south",
            "west",
            "east",
            "particle",
            "side",
            "render_type",
        ],
        str,
    ],
    "Texture",
]


def add_mod_id_if_missing(id: str, mod: "Mod"):

    if id.__contains__(":"):
        return id
    return f"{mod.id}:{id}"


def jp(*args: str) -> str:
    "Join path, not Japan"
    return os.path.join(*args)


def get_file_contents(path: str, info: Optional[str] = None) -> str:
    if not os.path.exists(path):
        log(
            FATAL,
            f"File {path} does not exist" + (" -> Info: %s" % info if info else ""),
        )
    with open(path, "r") as f:
        return f.read()


def replace(string: str, what_to: dict[str, str]):
    for key, value in what_to.items():
        string = string.replace("{" + str(key) + "}", value)
    return string


def dynamic_serializer(obj: Union[Callable[..., Any], JsonLike]):
    if isinstance(obj, JsonLike):
        return obj.__json__()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def export_class(obj: object):
    """Exports an object's attributes as a dictionary."""
    export = {}
    slots = getattr(obj, "__slots__", None)
    if slots is not None:
        if isinstance(slots, str):
            export[slots] = getattr(obj, slots, None)
        else:
            for slot in slots:
                export[slot] = getattr(obj, slot, None)
    else:  # Fallback to __dict__ if __slots__ not defined
        export = obj.__dict__.copy()
    return export


def import_class(obj: Type[Any], data: dict[str, Any]) -> Any:
    """Creates a new instance of a class with attributes from data."""
    try:
        sig = inspect.signature(obj.__init__)
    except (ValueError, TypeError):
        sig = inspect.Signature()

    init_params = {k: v for k, v in sig.parameters.items() if k != "self"}

    init_args = {k: data[k] for k in init_params if k in data}
    remaining_attrs = {k: v for k, v in data.items() if k not in init_params}

    new_instance = obj(**init_args)

    for key, value in remaining_attrs.items():
        setattr(new_instance, key, value)

    return new_instance

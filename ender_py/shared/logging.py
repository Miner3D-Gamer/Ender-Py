import traceback
from functools import wraps
from typing import Any, Callable, NoReturn, overload, Literal
from . import to_hashable


def print_traceback(traces_to_skip: int = 2):
    tb = traceback.extract_stack()[:-traces_to_skip]  # I love magic functions
    formatted = traceback.format_list(tb)
    print(
        color_text("[ERROR TRACEBACK]:\n>", *LOGGING_CALL_LEVELS[3][1])
        + color_text(">".join(formatted), *LOGGING_CALL_LEVELS[3][1])
    )


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


def color_text(text: str, r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m{text}\x1b[0m"


LOGGING_CALL_LEVELS = [
    ("DEBUG", (128, 128, 128)),
    ("INFO", (50, 172, 244)),
    ("WARNING", (255, 204, 80)),
    ("ERROR", (204, 0, 0)),
    ("FATAL ERROR", (255, 50, 52)),
]


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

    chosen = LOGGING_CALL_LEVELS[level]
    message_insert = "[%s] " % chosen[0]
    further_insert = " " * len(message_insert)
    title = message[0]
    buffer = "\n".join(
        [message_insert + title] + [further_insert + x for x in message[1:]]
    )
    print(color_text(buffer, *chosen[1]))

    if level == len(LOGGING_CALL_LEVELS) - 1:
        print_traceback(3)
        raise SystemExit()


DEBUG = 0
INFO = 1
WARN = 2
ERROR = 3
FATAL = 4

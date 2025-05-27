from shared import cache, find_file, log, WARNING, ERROR, FATAL

# from .fast_functions.load_rust import get_lib

# ender_rust = get_lib()


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
from PIL import Image
import os
import traceback
import inspect
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from . import Mod
    from .components import Texture


@runtime_checkable
class JsonLike(Protocol):
    __json__: Any


@runtime_checkable
class ObjectWithSlots(Protocol):
    __slots__: list[str]


@cache
def does_texture_have_transparency(texture: str) -> bool:
    asset_path = jp(os.path.dirname(__file__), "cache", "template", "assets")

    texture_path = find_file(asset_path, (texture.split("/")[-1]) + ".png")
    if texture_path is None:
        log(WARNING, f"Texture {texture} not found in {asset_path}")
        return False

    img = Image.open(texture_path).convert("RGBA")
    alpha = img.getchannel("A")

    return alpha.has_transparency_data


def generate_texture(
    provided: "texture_type",
    name: str = "",
) -> dict[str, str]:
    convert_to_correct_format: Callable[[str], str] = lambda x: (
        x if (x and x.__contains__(":")) else "{mod_id}:block/" + x
    )
    new: dict[str, str] = {}
    if isinstance(provided, str):
        new = {
            "top": convert_to_correct_format(provided),
            "bottom": convert_to_correct_format(provided),
            "north": convert_to_correct_format(provided),
            "south": convert_to_correct_format(provided),
            "west": convert_to_correct_format(provided),
            "east": convert_to_correct_format(provided),
            "particle": convert_to_correct_format(provided),
            "side": convert_to_correct_format(provided),
            "render_type": (
                "cutout_mipped" if does_texture_have_transparency(provided) else "solid"
            ),
        }
    else:
        sides = ["north", "south", "west", "east"]
        all = ["top", "bottom", "particle", "side"] + sides
        side = provided.get("side")
        if side:
            for thing in sides:
                if thing not in provided:
                    new[thing] = convert_to_correct_format(side)

        for thing in all:
            if thing not in new:
                new[thing] = convert_to_correct_format(
                    provided.get("north", provided["bottom"])
                )

        for key, val in provided.items():
            if key == "render_type":
                continue
            new[key] = convert_to_correct_format(str(val))

        new["render_type"] = provided.get(
            "render_type",
            (
                "cutout_mipped"
                if does_texture_have_transparency(new["bottom"])
                else "solid"
            ),
        )
    if new["render_type"].__contains__(":"):
        new["render_type"] = new["render_type"].split(":")[1]
    types = [
        "solid",
        "cutout",
        "cutout_mipped",
        "translucent",
        "cutout_mipped_all",
        "tripwire",
    ]
    if not new["render_type"] in types:
        log(
            ERROR,
            f"Invalid render_type: '{new.get('render_type')}'"
            + (" in context: " + name if name else ""),
        )

    new["render_type"] = "minecraft:" + new["render_type"]

    return new


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

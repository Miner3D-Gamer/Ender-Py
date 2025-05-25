from .shared import log, ERROR, WARNING, jp
from typing import Tuple, List, Callable, Iterator
from PIL import Image
import os
import json
import importlib.util
import sys

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .shared import texture_type


def find_closest_color(
    color: Tuple[int, int, int], targets: List[Tuple[int, int, int]], limit: float
):
    """q
    Finds the closest matching color from a list within a given limit.
    :param color: (r, g, b) tuple of the base color
    :param targets: List of (r, g, b) tuples to compare against
    :param limit: Maximum allowed distance for a match
    :return: Closest matching color or None if no match is within the limit
    """

    def color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]):
        """Euclidean distance between two RGB colors."""
        return (
            (c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2
        ) ** 0.5

    closest_color = None
    min_distance = float("inf")

    for target in targets:
        dist = color_distance(color, target)
        if dist < min_distance and dist <= limit:
            min_distance = dist
            closest_color = target

    return closest_color


def rgb_to_decimal(r: int, g: int, b: int):
    """Converts RGB to decimal."""
    return (r << 16) | (g << 8) | b


def get_average_color_of_image(png_path: str):
    """Calculates the average color of a PNG image."""
    with Image.open(png_path) as img:
        img = img.convert("RGB")  # Ensure RGB mode
        pixels: list[Tuple[int, int, int]] = list(img.getdata())  # type: ignore[attr-defined]
        avg_r = sum(p[0] for p in pixels) // len(pixels)
        avg_g = sum(p[1] for p in pixels) // len(pixels)
        avg_b = sum(p[2] for p in pixels) // len(pixels)
        return (avg_r, avg_g, avg_b)


def decimal_to_rgb(decimal: int):
    """Converts decimal to RGB tuple."""
    r = (decimal >> 16) & 0xFF
    g = (decimal >> 8) & 0xFF
    b = decimal & 0xFF
    return (r, g, b)


def get_closest_map_color(png_path: str, colors: str, fallback: str):
    with open(colors, "r") as f:
        color_data = json.load(f)

    new = [decimal_to_rgb(color) for _name, color in color_data.items()]
    if not os.path.exists(png_path):
        png_path = fallback

    tmp = find_closest_color(get_average_color_of_image(png_path), new, 255)
    if tmp is None:
        return None
    closest = rgb_to_decimal(*tmp)
    for color_name, color in color_data.items():
        if color == closest:
            return color_name
    return None


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


def import_module_from_full_path(full_path: str):
    # Extract the module name from the path (the filename without extension)
    module_name = full_path.split("\\")[-1].split(".")[0]

    # Create a module specification
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    if spec is None:
        raise ImportError(f"Invalid module path: {full_path}")

    # Create the module
    module = importlib.util.module_from_spec(spec)

    # Add the module to sys.modules (optional, but can help with subsequent imports)
    sys.modules[module_name] = module

    # Execute the module
    spec.loader.exec_module(module)  # type: ignore

    return module


def camel_to_snake(text: str) -> str:
    if not text:
        return text
    text = text.replace(" ", "")

    result = [text[0].lower()]
    triples: Iterator[Tuple[str, str, str]] = zip(text[:-2], text[1:-1], text[2:])

    for prev, curr, next in triples:
        # Add underscore if:
        # 1. Current char is uppercase and previous char is lowercase
        # 2. Current char is uppercase and next char is lowercase
        if (curr.isupper() and prev.islower()) or (curr.isupper() and next.islower()):
            result.extend(["_", curr.lower()])
        else:
            result.append(curr.lower())

    # Handle the last character
    if len(text) > 1:
        if text[-1].isupper() and text[-2].islower():
            result.extend(["_", text[-1].lower()])
        else:
            result.append(text[-1].lower())

    return "".join(result)


def snake_to_camel(text: str) -> str:
    return "".join(x.title() for x in text.split("_"))

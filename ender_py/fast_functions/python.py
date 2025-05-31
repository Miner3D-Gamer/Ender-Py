from PIL import Image
import os
from shared import cache
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
from typing import Union, Optional

from shared import log, FATAL


def find_closest_color(
    color: tuple[int, int, int], targets: list[tuple[int, int, int]], limit: float
):
    """q
    Finds the closest matching color from a list within a given limit.
    :param color: (r, g, b) tuple of the base color
    :param targets: List of (r, g, b) tuples to compare against
    :param limit: Maximum allowed distance for a match
    :return: Closest matching color or None if no match is within the limit
    """

    def color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]):
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


def decimal_to_rgb(decimal: int):
    """Converts decimal to RGB tuple."""
    r = (decimal >> 16) & 0xFF
    g = (decimal >> 8) & 0xFF
    b = decimal & 0xFF
    return (r, g, b)


@cache
def get_average_color_of_image(png_path: str):
    """Calculates the average color of a PNG image."""
    with Image.open(png_path) as img:
        img = img.convert("RGB")  # Ensure RGB mode
        pixels: list[tuple[int, int, int]] = list(img.getdata())  # type: ignore[attr-defined]
        avg_r = sum(p[0] for p in pixels) // len(pixels)
        avg_g = sum(p[1] for p in pixels) // len(pixels)
        avg_b = sum(p[2] for p in pixels) // len(pixels)
        return (avg_r, avg_g, avg_b)


def get_closest_map_color(png_path: str, colors: dict[str, int], fallback: str):
    # with open(colors, "r") as f:
    #     color_data = json.load(f)

    # new = [decimal_to_rgb(color) for _name, color in color_data.items()]
    if not os.path.exists(png_path):
        png_path = fallback

    tmp = find_closest_color(
        get_average_color_of_image(png_path), colors.values(), 255  # type: ignore
    )
    if tmp is None:
        return None
    closest = rgb_to_decimal(*tmp)
    for color_name, color in colors.items():
        if color == closest:
            return color_name
    return None


def write_to_file(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def write_to_files(paths: list[str], contents: list[str], _total_length: int):
    with ThreadPoolExecutor() as executor:
        executor.map(write_to_file, paths, contents)


def copy_and_rename_builtin(
    source: Union[str, Path], destination: Union[str, Path], mod_id: str
) -> None:
    """
    Copies a directory tree from source to destination, renaming all
    subfolders named 'builtin' to the specified mod_id.

    Args:
        source: The source directory path (str or Path object)
        destination: The destination directory path (str or Path object)
        mod_id: The new name to replace 'builtin' folders with

    Raises:
        FileNotFoundError: If the source directory doesn't exist
        ValueError: If mod_id is empty or contains invalid characters
        PermissionError: If lacking permissions to read/write directories
    """
    # Convert to Path objects for better path handling
    source_path = Path(source)
    dest_path = Path(destination)

    # Input validation
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_path}")

    # Create destination directory if it doesn't exist
    dest_path.mkdir(parents=True, exist_ok=True)

    try:
        for root, _dirs, files in os.walk(source_path):
            # Convert current path to Path object
            current_path = Path(root)

            # Calculate relative path from source
            relative_path = current_path.relative_to(source_path)

            # Build target path, replacing 'builtin' with mod_id if needed
            target_parts = [
                mod_id if part == "builtin" else part for part in relative_path.parts
            ]
            target_path = dest_path.joinpath(*target_parts)

            # Create target directory
            target_path.mkdir(parents=True, exist_ok=True)

            # Copy all files in current directory
            for file in files:
                source_file = current_path / file
                target_file = target_path / file

                # Use copy2 to preserve metadata
                shutil.copy2(source_file, target_file)

    except PermissionError as e:
        raise PermissionError(f"Permission denied while copying files: {e}") from e
    except Exception as e:
        raise RuntimeError(
            f"An error occurred while copying directory structure: {e}"
        ) from e


from fast_io import fast_rmtree


def get_file_contents(path: str, info: Optional[str] = None) -> str:
    if not os.path.exists(path):
        log(
            FATAL,
            f"File {path} does not exist" + (" -> Info: %s" % info if info else ""),
        )
    with open(path, "r") as f:
        return f.read()

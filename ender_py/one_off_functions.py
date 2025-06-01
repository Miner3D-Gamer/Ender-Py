# from .shared import log, ERROR, WARNING, jp
from typing import Tuple, List, Iterator, Optional
from PIL import Image
import importlib.util
import sys
import time
from collections import OrderedDict

# from typing import TYPE_CHECKING

from .internal_shared import cache


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
        pixels: list[Tuple[int, int, int]] = list(img.getdata())  # type: ignore[attr-defined]
        avg_r = sum(p[0] for p in pixels) // len(pixels)
        avg_g = sum(p[1] for p in pixels) // len(pixels)
        avg_b = sum(p[2] for p in pixels) // len(pixels)
        return (avg_r, avg_g, avg_b)


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


# instance -> list of (title, section, timestamp)
performance: dict[str, list[tuple[str, str, float]]] = OrderedDict()


def reset_performance_handler():
    """Reset the global performance tracking data."""
    global performance
    performance = {}


def performance_handler(
    instance: str, title: str, section: str, insert: Optional[float] = None
):
    """Record a performance measurement point."""
    global performance
    now = insert if insert else time.perf_counter()
    if instance not in performance:
        performance[instance] = []
    performance[instance].append((title, section, now))


def get_performance_handler():
    """Get the current performance data."""
    global performance
    return performance


def get_color_for_percentage(percentage: float, max_percentage: float):
    """
    Returns an ANSI color code based on percentage relative to max.
    Green for low percentages, red for high percentages.
    """
    if max_percentage == 0:
        return "\033[0m"  # Reset color

    # Normalize percentage to 0-1 range
    ratio = min(1.0, percentage / max_percentage)  # Cap at 1.0

    # Interpolate between green (0, 255, 0) and red (255, 0, 0)
    red = int(255 * ratio)
    green = int(255 * (1 - ratio))
    blue = 0

    # Return RGB ANSI escape code
    return f"\033[38;2;{red};{green};{blue}m"


def get_mixed_color_for_section(
    global_percentage: float,
    local_percentage: float,
    max_global: float,
    max_local: float,
):
    """
    Returns an ANSI color code based on a mix of global and local percentages.
    Combines both contributions for a more balanced color representation.
    """
    if max_global == 0 and max_local == 0:
        return "\033[0m"  # Reset color

    # Normalize both percentages to 0-1 range
    global_ratio = min(1.0, global_percentage / max_global) if max_global > 0 else 0
    local_ratio = min(1.0, local_percentage / max_local) if max_local > 0 else 0

    # Mix the ratios (60% global, 40% local weight)
    local_weight = 0.4
    mixed_ratio = (global_ratio * (1 - local_weight)) + (local_ratio * local_weight)

    # Interpolate between green (0, 255, 0) and red (255, 0, 0)
    red = int(255 * mixed_ratio)
    green = int(255 * (1 - mixed_ratio))
    blue = 0

    # Return RGB ANSI escape code
    return f"\033[38;2;{red};{green};{blue}m"


def print_performance():
    """Print formatted performance statistics with color coding."""
    perf = get_performance_handler()

    # Variables to accumulate times for the new info
    all_instance_total_times: list[float] = []
    all_start_times: list[float] = []
    all_end_times: list[float] = []

    for instance, records in perf.items():
        print(f"{instance}")
        if not records:
            print("  No performance data recorded")
            continue
        # Calculate actual total time from first to last measurement
        start_time = records[0][2]
        end_time = records[-1][2]

        all_start_times.append(start_time)
        all_end_times.append(end_time)

        # Check if we have an explicit end measurement or use current time
        # If the last record seems to be still running, use current time
        actual_total_time = end_time - start_time
        all_instance_total_times.append(actual_total_time)

        print(f"  Total: {actual_total_time:.4f}s")

        # Check if instance has an end marker
        has_end_marker = any(section == "END_MARKER" for _, section, _ in records)

        if not has_end_marker:
            print("  Instance errored (no end marker found)")
            continue

        grouped: OrderedDict[str, list[tuple[str, float, float]]] = OrderedDict()

        # Group measurements by title and calculate durations
        for i, (title, section, timestamp) in enumerate(records):
            if i + 1 < len(records):
                duration = records[i + 1][2] - timestamp
                end_ts = records[i + 1][2]
            else:
                # For the last record, we can't calculate duration without an end marker
                # Skip END_MARKER entries as they're just end points
                if section == "END_MARKER":
                    continue
                duration = 0.0  # or use a small default
                end_ts = timestamp
                print(
                    f"  Warning: No end time for final section '{section}' in '{title}'"
                )

            # Skip END_MARKER entries as they're just markers
            if section != "END_MARKER":
                grouped.setdefault(title, []).append((section, duration, end_ts))

        # Calculate statistics for color scaling
        title_times: dict[str, float] = {}
        title_percentages: list[float] = []
        all_section_global_percentages: list[float] = []
        all_section_local_percentages: list[float] = []

        for title, entries in grouped.items():
            title_time = sum(duration for _, duration, _ in entries)
            title_times[title] = title_time
            title_percentage = (
                (title_time / actual_total_time) * 100 if actual_total_time > 0 else 0
            )
            title_percentages.append(title_percentage)

            for section, duration, _ in entries:
                global_percentage = (
                    (duration / actual_total_time) * 100 if actual_total_time > 0 else 0
                )
                local_percentage = (
                    (duration / title_time) * 100 if title_time > 0 else 0
                )
                all_section_global_percentages.append(global_percentage)
                all_section_local_percentages.append(local_percentage)

        # Get max values for color scaling
        max_title_percentage = max(title_percentages) if title_percentages else 1
        max_section_global_percentage = (
            max(all_section_global_percentages) if all_section_global_percentages else 1
        )
        max_section_local_percentage = (
            max(all_section_local_percentages) if all_section_local_percentages else 1
        )

        reset_color = "\033[0m"

        # Check for timing inconsistencies
        total_accounted_time = sum(title_times.values())
        if (
            abs(total_accounted_time - actual_total_time) > 0.001
        ):  # Allow small floating point errors
            print(
                f"  Warning: Accounted time ({total_accounted_time:.4f}s) != Total time ({actual_total_time:.4f}s)"
            )
            print(f"  This suggests overlapping measurements or missing end markers")

        # Print results
        for title, entries in grouped.items():
            title_time = title_times[title]
            title_percentage = (
                (title_time / actual_total_time) * 100 if actual_total_time > 0 else 0
            )
            title_color = get_color_for_percentage(
                title_percentage, max_title_percentage
            )
            print(
                f"  > {title_color}{title}{reset_color} ({title_time:.4f}s - {title_percentage:.1f}%)"
            )

            for section, duration, end_ts in entries:
                global_percentage = (
                    (duration / actual_total_time) * 100 if actual_total_time > 0 else 0
                )
                local_percentage = (
                    (duration / title_time) * 100 if title_time > 0 else 0
                )
                section_color = get_mixed_color_for_section(
                    global_percentage,
                    local_percentage,
                    max_section_global_percentage,
                    max_section_local_percentage,
                )
                print(
                    f"    >> {section_color}{section}{reset_color}: {duration:.4f}s "
                    f"({global_percentage:.1f}% | {local_percentage:.1f}%) "
                )

    # At the end, print the two requested totals:
    if all_start_times and all_end_times:
        overall_start = min(all_start_times)
        overall_end = max(all_end_times)
        actual_elapsed_time = overall_end - overall_start
        single_threaded_total_time = sum(all_instance_total_times)

        print("\nSummary:")
        print(
            f"  Total execution time of all instances: {single_threaded_total_time:.4f}s"
        )
        print(f"  Total actual elapsed time: {actual_elapsed_time:.4f}s")


def performance_add_end_marker(instance: str):
    """Add an explicit end marker to close any open measurements."""
    performance_handler(instance, "END", "END_MARKER")


# The point is one too far - It shows how long it took until point instead of how long it took from point to next point
# 00:57 aah sentence building

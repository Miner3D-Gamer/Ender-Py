import ctypes, os

from . import ender_rust


def get_closest_map_color(
    png_path: str, color_data: dict[str, tuple[int, int, int]], fallback: str
) -> str | None:
    if not os.path.exists(png_path):
        png_path = fallback

    # Prepare targets as an array of RGB structs
    targets = (RGB * len(color_data))()
    for i, (color_name, (r, g, b)) in enumerate(color_data.items()):
        targets[i].r = r
        targets[i].g = g
        targets[i].b = b

    # Call the Rust function
    idx = ender_rust.average_and_find_closest_color_index(
        png_path.encode("utf-8"),
        targets,
        len(targets),
        ctypes.c_float(255.0),
    )

    if idx < 0 or idx == 1:
        # Error or no match found
        return None

    # Return the color name at the found index
    return list(color_data.keys())[idx]


class RGB(ctypes.Structure):
    _fields_ = [("r", ctypes.c_int), ("g", ctypes.c_int), ("b", ctypes.c_int)]


def get_closest_color(
    main: tuple[int, int, int], targets: list[tuple[int, int, int]], limit: float
):  # Performance improvement of 0.4 to 0.3
    base = RGB(*main)
    target_array = (RGB * len(targets))(*[RGB(*t) for t in targets])
    r, g, b = ctypes.c_int(), ctypes.c_int(), ctypes.c_int()

    result = ender_rust.find_closest_color(
        base,
        target_array,
        len(targets),
        limit,
        ctypes.byref(r),
        ctypes.byref(g),
        ctypes.byref(b),
    )
    if result == 0:
        return (r.value, g.value, b.value)
    else:
        return None


def write_to_file(path: str, content: str):
    path = os.path.normpath(path)
    path_bytes = path.encode("utf-8")
    content_bytes = content.encode("utf-8")
    ender_rust.write_file(path_bytes, content_bytes, len(content_bytes))


def write_to_files(file_paths: list[str], file_contents: list[str], total_length: int):
    encoded_paths = [os.path.normpath(p).encode() for p in file_paths]
    encoded_data = [d.encode() for d in file_contents]
    data_lengths = [len(d) for d in encoded_data]

    # Convert to ctypes arrays
    path_array = (ctypes.c_char_p * total_length)(*encoded_paths)
    data_array = (ctypes.c_char_p * total_length)(*encoded_data)
    len_array = (ctypes.c_size_t * len(data_lengths))(*data_lengths)

    # Call once
    ender_rust.write_files(path_array, data_array, len_array, total_length)


def copy_and_rename_builtin(source: str, destination: str, mod_id: str) -> None:
    """
    Python wrapper for the Rust FFI function that copies a directory tree
    and renames all subfolders named 'builtin' to `mod_id`.

    Raises:
        ValueError: On invalid input or if Rust returns an error.
    """
    if not all(isinstance(arg, str) for arg in [source, destination, mod_id]):
        raise ValueError("All arguments must be strings.")

    result = ender_rust.copy_and_rename_builtin_ffi(
        source.encode("utf-8"), destination.encode("utf-8"), mod_id.encode("utf-8")
    )

    if result == 0:
        return
    elif result == 1:
        raise ValueError("Invalid UTF-8 input or empty mod_id.")
    elif result == 2:
        raise IOError("I/O error occurred in Rust implementation.")
    else:
        raise RuntimeError(f"Unknown error code returned: {result}")


def fast_rmtree(path: str) -> None:
    ender_rust.delete_path_parallel(path.encode("utf-8"))

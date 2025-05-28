import ctypes
import os
import platform


def get_lib(name: str, search_path: str):
    if platform.system() == "Windows":
        libname = "%s.dll" % name
    elif platform.system() == "Darwin":
        libname = "lib%s.dylib" % name
    else:
        libname = "lib%s.so" % name

    path = find_file(search_path, libname)
    if path is None:
        return None

    # lib_path = os.path.join(path, libname)

    lib_path = os.path.abspath(path)
    # lib_path = os.path.abspath(f"ender_rust/target/release/{libname}")
    rust = ctypes.CDLL(lib_path)
    return rust


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

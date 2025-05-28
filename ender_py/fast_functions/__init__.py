from .load_rust import get_lib
import os


this_file_path = os.path.dirname(os.path.abspath(__file__))

ender_rust_path = os.path.join(this_file_path, "ender_rust", "target", "release")

try:
    temp = get_lib("ender_rust", ender_rust_path)
except Exception as e:
    temp = None
    print("ERROR: Could not load ender_rust for faster functions (did you build it?);")
    print(e)


from .python import *

if not temp is None:  # Overwrite python functions
    ender_rust = temp
    from .rust import *

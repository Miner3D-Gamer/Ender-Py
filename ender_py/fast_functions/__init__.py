from .load_rust import get_lib

try:
    temp = get_lib()
except Exception as e:
    temp = None
    print("ERROR: Could not load ender_rust for faster functions;")
    print(e)


from .python import *

if not temp is None:  # Overwrite python functions
    ender_rust = temp
    from .rust import *

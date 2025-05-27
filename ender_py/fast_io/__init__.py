import platform

system = platform.system()

if system == "Windows":
    # A speed increase of over 20 seconds to under 1 second, wtf (~3000 Files)
    from .windows import *


elif system in ["Linux", "Darwin"]:
    from .linux import *
else:
    from .fallback import *


__all__ = ["fast_copytree", "fast_rmtree"]

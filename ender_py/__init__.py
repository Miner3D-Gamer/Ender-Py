# Adding to path so internal modules can be imported
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


from .internal_shared import (
    add_mod_id_if_missing,
)

# Get the directory of the executing file -> For external resources
main_path = sys.modules["__main__"].__file__
if main_path:
    currect_dir = os.path.dirname(os.path.abspath(main_path))
else:
    currect_dir = os.getcwd()


this = os.path.dirname(__file__)

TRANSLATIONS = {
    "creative_tab": "creative_tab.{mod_id}.{component_id}",
    "item": "item.{mod_id}.{component_id}",
    "block": "block.{mod_id}.{component_id}",
}  # THIS IS VERY MUCH IN USE


from .mod_class import Mod, export_mod, import_mod


from . import presets
import shared
import fast_functions
import fast_io
from . import internal_shared
from . import components

__all__ = [
    "Mod",  # Mod class
    "presets",  # Templates
    "add_mod_id_if_missing",  # 'item' -> '{mod}:item', 'minecraft:log' -> 'minecraft:log'
    "shared",  # Expose internal function that might be useful
    "fast_functions",  # Same
    "fast_io",  # Same
    "internal_shared",  # Same
    "import_mod",
    "export_mod",
    "components",
]

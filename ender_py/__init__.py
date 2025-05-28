# I really need to break this file up, 2000 lines is too much

# Adding to path so internal modules can be imported
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from typing import Optional, Union, Any, TypedDict, Callable, cast, NoReturn

from .fast_io import fast_copytree

from concurrent.futures import ThreadPoolExecutor

# import csv # Later.
import json
import traceback
import shutil
import re
import time
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict

main_path = sys.modules["__main__"].__file__
if main_path:
    currect_dir = os.path.dirname(os.path.abspath(main_path))
else:
    currect_dir = os.getcwd()


from .components import (
    COMPONENT_TYPE,
    Block,
    Item,
    CreativeTab,
    LootTable,
    VoxelShape,
    Procedure,
    Recipe,
    Unused,
    Tag,
    TagManager,
    # RecipeCrafting,
    # RecipeItemTag,
    # RecipeCraftingShapeless,
)
from .internal_shared import (
    # DEBUG,
    jp,
    replace,
    export_class,
    import_class,
    add_mod_id_if_missing,
    java_minifier,
)
from .one_off_functions import (
    import_module_from_full_path,
    get_performance_handler,
    performance_handler,
    reset_performance_handler,
    print_performance,
    performance_add_end_marker,
    decimal_to_rgb,
    snake_to_camel,
)
from shared import (
    log,
    FATAL,
    ERROR,
    WARNING,
    INFO,
)

from .procedures import ProcedureInternal

from fast_functions import *

this = os.path.dirname(__file__)
common_cache = jp(this, "cache")


def is_valid_internal_mod_id(id: str):
    if not id.islower():
        return False
    for char in id:
        if char not in "qwertzuiopasdfghjklyxcvbnm._":
            return False
    if id.__contains__(".."):
        return False
    if len(id) > 255:
        return False

    return True


def is_valid_external_mod_id(id: str):
    if not id.islower():
        return False
    for char in id:
        if char not in "qwertzuiopasdfghjklyxcvbnm_-0123456789":
            return False
    if id.__contains__(".."):
        return False
    if len(id) > 255:
        return False

    return True


def is_valid_component_id(id: str):
    if not id.islower():
        return False
    for char in id:
        if char not in "qwertzuiopasdfghjklyxcvbnm_":
            return False
    if len(id) > 255:
        return False

    return True


# def get_default(dict: dict, type: str, key: str):
#     class Empty:
#         pass

#     thing = dict.get(key, Empty)
#     if isinstance(thing, Empty):
#         thing = DEFAULTS.get(type, {}).get(key, Empty)
#         if isinstance(thing, Empty):
#             return DEFAULTS.get(type, {"configuration": {}})["configuration"].get(
#                 key, None
#             )
#     return thing


# DEFAULTS = {
#     "mod": {
#         "internal_id": "com.example.mod",
#         "public_id": "example_mod",
#         "name": "Example Mod",
#         "author": "Example Author",
#         "version": "1.0.0",
#         "description": "This is an example mod.",
#         "license": "MIT",
#     },
#     "item": {
#         "type": "item",
#         "name": "Example Item",
#         "texture": "example_texture",
#         "is_block_item": False,
#         "configuration": {
#             "stack_size": 64,
#             "durability": None,
#             "unrepairable": True,
#             "fire_resistant": False,
#             "remains_after_crafting": False,
#             "rarity": "common",
#             "enchntability": 0,
#             "block_break_speed": 1.0,
#             "can_break_any_block": False,
#             "item_animation": None,
#         },
#     },
#     "creative_menu": {
#         "type": "creative_menu",
#         "name": "Example Creative Menu",
#         "configuration": {
#             "hide_title": False,
#             "no_scrollbar": False,
#             "alignment_right": False,
#         },
#     },
# }


def import_mod(data: dict[str, Any], mdk_folder: str):
    """Creates a new instance of mod_class from exported data."""

    from . import components

    mod_data = data.get("mod", {})
    components_data = data.get("components", {})
    mod_class = Mod

    # Create mod instance
    mod_instance = mod_class(
        internal_id=mod_data["internal_id"],
        public_id=mod_data["public_id"],
        name=mod_data["name"],
        author=mod_data["author"],
        version=mod_data["version"],
        description=mod_data["description"],
        license=mod_data["license"],
        mdk_parent_folder=mdk_folder,
    )

    # Import components
    for component_id, component_data in components_data.items():

        component_class = getattr(
            components,
            component_data["TYPE"].replace("_", " ").title().replace(" ", ""),
        )
        if component_class:
            mod_instance.components[component_id] = import_class(
                component_class, component_data
            )
        else:
            raise ValueError(f"Unknown component type for ID: {component_id}")

    return mod_instance


def export_mod(mod_class: "Mod") -> dict[str, str | dict[str, Any]]:
    mod_things = {
        "internal_id": mod_class.internal_id,
        "public_id": mod_class.id,
        "name": mod_class.name,
        "author": mod_class.author,
        "version": mod_class.version,
        "description": mod_class.description,
        "license": mod_class.license,
    }
    components: dict[str, dict[str, Any]] = {}
    for component_id, component in mod_class.components.items():
        components[component_id] = export_class(component)

    return {"mod": mod_things, "components": components}


translations = {
    "creative_tab": "creative_tab.{internal_mod_id}.{component_id}",
    "item": "item.{internal_mod_id}.{component_id}",
    "block": "block.{internal_mod_id}.{component_id}",
}  # THIS IS VERY MUCH IN USE


def generate_blocks(
    blocks: dict[str, Block],
    self: "Mod",
    template_path: str,
    replace_files: str,
    configurator: dict[str, Callable[..., Any]],
    java_path: str,
    color_path: Optional[str],
    error_texture: str,
    tag_manager: TagManager,
    unique_name: str,
    mod_info: "ModInfo",
    info_replace: dict[str, str],
) -> tuple[dict[str, Item], list[LootTable], dict[str, str]]:
    return_items: dict[str, Item] = {}
    return_loot_tables: list[LootTable] = []

    if not color_path is None:
        performance_handler(unique_name, "Blocks", "Finding closest map color", None)
        with open(color_path, "r") as f:
            color_data = json.load(f)
        colors = OrderedDict()
        for key, value in color_data.items():
            colors[key] = decimal_to_rgb(value)

        # Generate block items and loot table for every block
        for block_id, block in blocks.items():
            if block.map_color is None:
                stuff = format_text(
                    block.texture["top"], self, mod_info, info_replace
                ).split(":", 1)
                if len(stuff) == 2:
                    texture = jp(stuff[0], "textures", stuff[1])
                else:
                    raise BaseException(stuff)
                texture_path = jp(
                    template_path,
                    "assets",
                    texture + ".png",
                )

                block.map_color = get_closest_map_color(
                    texture_path, colors, error_texture
                )
    performance_handler(
        unique_name,
        "Blocks",
        "Adding block items, loot table, and 'mineable' tag",
        None,
    )
    for block_id, block in blocks.items():
        return_items.update(
            {
                block_id: (
                    Item(
                        name=block.name,
                        texture=block_id,
                        stack_size=block.stack_size,
                        fire_resistant=False,
                        unrepairable=False,
                        durability=None,
                        is_block_item=True,
                        block_item_type=block.blocktype,
                        display_item=block.display_item,
                        block_item_textures=block.texture,
                    )
                    if block.item is None
                    else block.item
                )
            }
        )
        if block.loot_table is None:
            loot_table_path = "default_block_drop"
            loot_table_path_with_type = loot_table_path + block.blocktype + ".json"
            mod_id = self.id
            if os.path.exists(loot_table_path_with_type):
                loot_table_path = loot_table_path_with_type
            else:
                loot_table_path = loot_table_path
        else:
            loot_table_path = block.loot_table
            mod_id = block.loot_table.split(":", 1)[0]

        return_loot_tables.append(
            LootTable(
                name=block_id,
                content=replace(
                    get_file_contents(
                        jp(
                            template_path,
                            "data",
                            loot_table_path.replace("builtin:", self.id + ":").replace(
                                ":", "/loot_tables/"
                            ),
                        )
                        + ".json",
                    ),
                    {"block_id": block_id, "mod_id": self.id},
                ),
                context="blocks",
                mod_id=mod_id,
            )
        )
        if not block.breakable_with is None:
            for tool in block.breakable_with:
                tag_manager["minecraft:blocks/mineable/" + tool] = block_id

    # Call code bundler to generate the code for each block
    performance_handler(unique_name, "Blocks", "Generating code (Bundler)", None)

    block_bundler, block_files, translation_keys = handle_bundler(
        {
            "bundler": jp(replace_files, "blocks/block_bundler.java"),
            "import": jp(replace_files, "blocks/import_line.java"),
            "code": jp(replace_files, "blocks/block_code.java"),
            "component": jp(replace_files, "blocks/block_component.java"),
            "properties": jp(replace_files, "blocks/properties.json"),
            "initializer": jp(replace_files, "blocks/block_type_initializer.json"),
        },
        self,
        blocks,  # type: ignore
        configurator,
        self.minify,
    )
    performance_handler(unique_name, "Blocks", "Writing code to cache", None)

    write_to_file(jp(java_path, "ModBlocks.java"), block_bundler)
    # things_added.append("blocks")

    for file, code in block_files.items():
        write_to_file(jp(java_path, f"blocks/{file}.java"), code)

    return return_items, return_loot_tables, translation_keys


class Model:
    def __init__(
        self, name: str, model: Optional[str], item: Optional[bool] = None
    ) -> None:
        self.name = name
        self.model = model
        self.item = item


def combine_dicts(dict1: dict[Any, Any], dict2: dict[Any, Any]) -> dict[str, str]:
    return {**dict1, **dict2}


def remove_brackets(string: str):
    if string.startswith("[") and string.endswith("]"):
        return string[1:-1]
    return string


def is_correct_type(type: str, item: Any):
    if type == "float":
        try:
            float(item)
        except:
            return False
        else:
            return True
    elif type == "int":
        try:
            int(item)
        except:
            return False
        else:
            return True
    elif type == "bounding_box":
        for i in item:
            if not isinstance(i, VoxelShape):
                return False
        return True
    elif type == "bool":
        return item == True or item == False

    raise ValueError("Unknown requested type to check: '%s' for %s" % (type, item))


def handle_hit(
    var: "TransFunctionValues",
    component: COMPONENT_TYPE,
    slot: str,
    property: dict[str, Any],  # Actually dict[str, str|dict] i think
    property_name: str,
    option_idx: Optional[int] = None,
) -> bool:

    if property.get("skip", False):
        return True

    builder: AttributeBuilder = var.stuff.get(property_name, AttributeBuilder())
    l = property.get("location")
    if l is None:
        log(FATAL, "Location not provided for %s" % property_name)
    builder.location = l
    builder.required_imports.extend(property.get("required_imports", []))
    builder.extra_code_after += property.get("extra_code_after", "")
    builder.extra_code_before += property.get("extra_code_before", "")

    if not option_idx is None:
        option = property["options"][option_idx]
        condition = option.get("condition")
        if not condition is None:
            if not is_full_condition_met(component, condition):
                return False
        to_insert = option.get("return")
        builder.required_imports.extend(option.get("required_imports", []))
        builder.extra_code_after += option.get("extra_code_after", "")
        builder.extra_code_before += option.get("extra_code_before", "")
        if to_insert:
            builder.insert_divider = property.get("option_divider", "")
            expected_value_type = option.get("type")
            value = component.__getattribute__(slot)
            if expected_value_type != "bool" and value == False:
                return True
            if not expected_value_type is None:
                if not is_correct_type(expected_value_type, value):
                    raise Exception(
                        "Incorrect type for %s, expected %s" % (slot, value)
                    )
                result = to_insert % value
            else:
                result = to_insert
            if isinstance(result, list):
                result = cast(list[str], result)
                builder.inserts.extend(result)
            else:
                builder.inserts.append(result)

    expected_value_type = property.get("type")
    value = component.__getattribute__(slot)
    if expected_value_type != "bool" and value == False:
        return True
    if not expected_value_type is None:

        if not is_correct_type(expected_value_type, value):
            raise Exception("Incorrect type for %s, expected %s" % (slot, value))
        if not property["insert"].__contains__("%s"):
            log(
                ERROR,
                "No %s detected even though it was expected do to an input type being defined: "
                + "%s" % property["insert"],
            )
            result = property["insert"]
        else:
            if isinstance(value, bool):
                value = str(value).lower()
            result = property["insert"] % value
    else:
        result = property.get("insert", "")
    builder.insert = result

    var.stuff[property_name] = builder

    return True


class AttributeBuilder:
    def __init__(self) -> None:
        self.location = ""
        self.insert = ""
        self.inserts: list[str] = []
        self.insert_divider = ""
        self.required_imports: list[str] = []
        self.extra_code_after = ""
        self.extra_code_before = ""

    def __repr__(self) -> str:
        return "<%s> (%s -> '%s') in %s %s" % (
            self.insert,
            self.inserts,
            self.insert_divider,
            self.location,
            self.required_imports,
        )


class TransFunctionValues:
    # You can't even escape the trans when coding
    def __init__(self) -> None:
        self.stuff: dict[str, AttributeBuilder] = {}

    def __repr__(self) -> str:
        result = ""
        for i in self.stuff:
            result += "\n%s:" % i
            result += "\n\t%s:" % self.stuff[i]
        return result


def is_condition_met(
    component: COMPONENT_TYPE, condition: dict[str, Any]
) -> Union[bool, NoReturn]:  # What even if this function for???
    condition_type = condition["type"]
    condition_name = condition["name"]

    if condition_type == "operator":
        if condition_name == "not":
            return not is_condition_met(component, condition["value"])
        elif condition_name == "and":
            return all([is_condition_met(component, c) for c in condition["value"]])
        elif condition_name == "or":
            return any([is_condition_met(component, c) for c in condition["value"]])
    elif condition_type == "slot":
        if getattr(component, condition_name) == condition["value"]:
            return True
        else:
            return False

    log(FATAL, "Unknown condition type/name %s (%s)" % (condition_type, condition_name))


def is_full_condition_met(
    component: COMPONENT_TYPE, conditions: list[list[dict[str, Any]]]
):
    return all(
        [
            any(
                is_condition_met(component, condition)
                for condition in or_condition_subsets
            )
            for or_condition_subsets in conditions
        ]
    )


def get_properties(component: COMPONENT_TYPE, path: str):
    # if component.type == "item":
    #     return "", ""
    with open(path, "r") as f:
        properties: dict[Any, Any] = json.load(f)

    var = TransFunctionValues()

    blacklist = [
        "texture",
        "item",
        "TYPE",
        "stack_size",
        "blocktype",
        "display_item",
        "loot_table",
        "is_block_item",
        "block_item_textures",
        "block_item_type",
        "icon_item",
        "items",
        "procedures",
    ]

    options = component.__slots__
    for option in options:
        if option in blacklist:
            continue
        skipped_properties_due_to_condition_not_met: list[Any] = []
        v = component.__getattribute__(option)
        if v is None:
            continue
        found_but_option_not_correct = False
        property = None
        for property in properties:
            if properties[property].get("condition", []) != []:
                if not is_full_condition_met(
                    component, properties[property].get("condition", [])
                ):
                    skipped_properties_due_to_condition_not_met.append(property)
                    continue  ############################################
            if property.startswith("_"):
                idx = 0
                for o in properties[property]["options"]:
                    if o["expected"] == option:
                        if handle_hit(
                            var,
                            component,
                            option,
                            properties[property],
                            property,
                            option_idx=idx,
                        ):
                            break
                    idx += 1
                else:
                    continue
                break
            else:
                ########################################################## IF IT HAS ['options'],  CHECK THE VALUE OF 'option'
                # tf is OPTION?
                if property == option:
                    if properties[property].get("options", []) == []:
                        if handle_hit(
                            var, component, option, properties[property], property
                        ):
                            break
                    else:
                        for idx, o in enumerate(properties[property]["options"]):
                            if o["expected"] == component.__getattribute__(option):
                                if handle_hit(
                                    var,
                                    component,
                                    option,
                                    properties[property],
                                    property,
                                    option_idx=idx,
                                ):
                                    break
                        else:
                            found_but_option_not_correct = True
                            continue
                    break  # IS THIS BREAK NEEDED??????

        else:
            if option in skipped_properties_due_to_condition_not_met:
                if properties[property].get(
                    "condition_not_met_okay", False
                ):  # TF DOES THIS EVEN MEAN??? THIS ISN'T A PROPERTY? IS IT?
                    continue
                else:
                    log(
                        ERROR, "Conditions were not met"
                    )  # improve this error messaging
            if found_but_option_not_correct:
                log(
                    FATAL,
                    "No option fitting for property %s found in %s (got %s)"
                    % (option, path, component.__getattribute__(option)),
                )
            else:
                log(FATAL, "Unable to find property %s in %s" % (option, path))

    return handle_transfunction_class_thingy_pls_help(var)


def handle_transfunction_class_thingy_pls_help(var: TransFunctionValues):
    imports: list[str] = []

    attribute_string = ""
    extra_code_before = ""
    extra_code_after = ""
    after = ""
    before = ""
    overrides: list[str] = []
    for i in var.stuff:
        builder = var.stuff[i]
        imports.extend(builder.required_imports)
        if builder.location == "override":
            if builder.insert:
                if len(builder.inserts) > 0:
                    insert_insert = ", ".join(builder.inserts)
                    insert = [builder.insert % insert_insert]
                else:
                    insert = [builder.insert]
            else:
                insert = builder.inserts

            overrides.extend(insert)
        elif builder.location == "attribute":
            if len(builder.inserts) > 0:
                insert_insert = ", ".join(builder.inserts)
                insert = builder.insert % insert_insert
            else:
                insert = builder.insert
            attribute_string += insert
        elif builder.location == "after":
            if len(builder.inserts) > 0:
                insert_insert = ", ".join(builder.inserts)
                insert = builder.insert % insert_insert
            else:
                insert = builder.insert
            after += insert
        elif builder.location == "before":
            if len(builder.inserts) > 0:
                insert_insert = ", ".join(builder.inserts)
                insert = builder.insert % insert_insert
            else:
                insert = builder.insert
            before += insert
        else:
            log(FATAL, "Unknown location '%s' in %s" % (builder.location, i))
        extra_code_before += builder.extra_code_before
        extra_code_after += builder.extra_code_after

    final_overrides = "".join(
        "\n\t@Override\n\t%s" % override for override in overrides
    )

    imports = list(set(imports))
    final_import = ""
    for i in imports:
        final_import += "\nimport %s;" % i

    return (
        attribute_string,
        final_overrides,
        final_import,
        extra_code_before,
        extra_code_after,
        after,
        before,
    )


def handle_bundler(
    paths: dict[str, str],
    mod: "Mod",
    components: Mapping[str, COMPONENT_TYPE],
    configurator: dict[str, Callable[..., Any]],
    minify: bool,
) -> tuple[str, dict[str, str], dict[str, str]]:
    # I don't like this function :|
    # It's slow, unreadable, and not very dynamic

    if not os.path.exists(paths["bundler"]):
        log(FATAL, f"File {paths['bundler']} does not exist")
        return "", {}, {}
    if not os.path.exists(paths["import"]):
        log(FATAL, f"File {paths['import']} does not exist")
        return "", {}, {}
    if not os.path.exists(paths["code"]):
        log(FATAL, f"File {paths['code']} does not exist")
        return "", {}, {}

    bundler = get_file_contents(paths["bundler"])
    import_line = get_file_contents(paths["import"])
    code = get_file_contents(paths["code"])
    bundler_component = get_file_contents(paths["component"])

    # order of operation
    # item code
    # import code
    # item component
    # item bundler
    all_code: dict[str, str] = {}
    all_imports = ""
    all_bundler_code = ""
    translation_keys: dict[str, str] = {}
    extra: dict[str, str] = {}
    for component_id, component in components.items():
        naming = component.TYPE
        new_code = code

        processing_block_item = False
        if isinstance(component, Item):
            processing_block_item = component.is_block_item
        elif isinstance(component, CreativeTab):
            single_item = get_file_contents(paths["item"])

            class none:
                TYPE = "not_found"

            tmp = ""
            for item in component.items:
                item_type = mod.components.get(item, none).TYPE
                tmp += replace(
                    single_item,
                    {"item": configurator["get_java_item"](item, type=item_type)},
                )
            creative_tab_items = tmp

            translation_key = replace(
                translations[naming],
                {"component_id": component_id, "internal_mod_id": mod.id},
            )

            item_type = mod.components.get(component.icon_item, none).TYPE
            new_code = replace(
                new_code,
                {
                    "tab_title": component.name,
                    "tab_icon": configurator["get_java_item"](
                        component.icon_item, item_type
                    ),
                    "items": creative_tab_items,
                    "translation_key": translation_key,
                },
            )
        elif isinstance(component, Block):

            extra["block_type"] = (
                component.blocktype.replace("_", " ")
                .title()
                .replace(" ", "")
                .replace("Cube", "")
            )

        else:
            raise Exception("Invalid type: " + component.TYPE)

        (
            properties,
            overrides,
            imports,
            extra_code_before,
            extra_code_after,
            after,
            before,
        ) = get_properties(component, paths["properties"])

        if component.TYPE == "block":
            imports += (
                (
                    "\nimport net.minecraft.world.level.block.%sBlock;"
                    % (component.blocktype.replace("_", " ").title()).replace(" ", "")  # type: ignore
                )
                if not component.blocktype == "cube"  # type: ignore
                else ""
            )
        file_name = snake_to_camel(component_id) + snake_to_camel(naming)

        replace_info = combine_dicts(
            {
                "internal_mod_id": mod.internal_id,
                "component_id_upper": component_id.title(),
                "component_id": component_id,
                "properties": properties,
                "overrides": overrides,
                "imports": imports,
                "additional_code_before": extra_code_before,
                "additional_code_after": extra_code_after,
                "after": after,
                "before": before,
                "component_file_id": snake_to_camel(component_id),
                "file_name": file_name,
            },
            extra,
        )

        new_code = replace(
            new_code,
            replace_info,
        )
        if minify:
            new_code = java_minifier(new_code)
        all_code[file_name] = new_code
        translation_key = replace(
            translations[naming],
            replace_info,
        )
        if processing_block_item:
            continue
        translation_keys[translation_key] = component.name

        # import line code
        all_imports += replace(
            import_line,
            replace_info,
        )

        # component registry
        all_bundler_code += replace(
            bundler_component,
            replace_info,
        )

    bundler = replace(
        bundler,
        {
            "internal_mod_id": mod.internal_id,
            "mod_id_upper": mod.id.title(),
            "components": all_bundler_code,
            "component_imports": all_imports,
        },
    )
    if minify:
        bundler = java_minifier(bundler)

    return bundler, all_code, translation_keys


def assemble_pack(
    resource_path: str,
    template_path: str,
    pack_path: str,
    mod_id: str,
    mod: "Mod",
    mod_info: "ModInfo",
    info_replace,
):
    copy_and_rename_builtin(resource_path, template_path, mod_id)

    required_file = jp(template_path, "required.json")
    if not os.path.exists(required_file):
        log(
            FATAL,
            f"Required file {required_file} does not exist, files like mod.toml and pack.mcmeta should be defined here.",
        )

    required_files = json.loads(get_file_contents(required_file))
    for file, format in required_files.items():
        path = jp(template_path, file)
        if not os.path.exists(path):
            log(
                FATAL,
                f"Required file {path} does not exist (Declared in {required_file})",
            )
        os.makedirs(jp(pack_path, os.path.dirname(file)), exist_ok=True)
        file_contents = get_file_contents(jp(template_path, file))

        if format:
            file_contents = format_text(file_contents, mod, mod_info, info_replace)

        write_to_file(jp(pack_path, file), file_contents)


from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


import importlib.util


def is_library_installed(library_name: str) -> bool:
    spec = importlib.util.find_spec(library_name)
    return spec is not None


if is_library_installed("tge"):
    import tge

    profile = tge.tbe.profile
else:

    def do_nothing(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    profile = do_nothing


class SortedComponents(TypedDict):
    item_textures: list[str]
    item_models: list[Model]
    block_textures: list[dict[str, str]]
    block_models: list[Model]
    language: dict[str, str]
    items: dict[str, Item]
    blocks: dict[str, Block]
    creative_tabs: dict[str, CreativeTab]
    internal_loot_tables: list[LootTable]
    tags: list[Tag]

    procedures: dict[str, Procedure]
    recipes: dict[str, Recipe]


class ModInfo(TypedDict):
    internal_id: str
    id: str
    minecraft_version: str
    mod_loader_version: str
    mod_loader: str


class Mod:
    __slots__ = [
        "internal_id",
        "id",
        "name",
        "author",
        "description",
        "version",
        "license",
        "available",
        "components",
        "unordered_components",
        "external_packs",
        "homepage",
        "minify",
    ]

    def __init__(
        self,
        internal_id: str,
        public_id: str,
        name: str,
        author: str,
        description: str,
        version: str,
        license: str,
        mdk_parent_folder: str,
        external_packs: list[str] = [],
        homepage: str = "",
    ) -> None:
        if not is_valid_internal_mod_id(internal_id):
            raise Exception("Invalid internal mod id")
        self.internal_id = internal_id
        self.id = public_id
        self.name = name
        self.author = author
        self.description = description
        self.version = version
        self.license = license
        self.external_packs = external_packs
        self.homepage = homepage
        if homepage != "" and not is_valid_url(homepage):
            log(WARNING, f"Homepage {homepage} is not a valid url")

        self.components: dict[str, COMPONENT_TYPE] = {}
        self.unordered_components: list[COMPONENT_TYPE] = []
        # self.tags: dict[str, dict[str, list[str]]] = {"minecraft": {}}
        # tools = ["axe", "pickaxe", "shovel", "hoe"]

        # for tool in tools:
        #     self.tags["minecraft"]["blocks/mineable/" + tool] = []

        self.available: list[str] = []

        for root, _folders, files in os.walk(mdk_parent_folder):

            if not root.startswith(mdk_parent_folder):
                continue

            for file in files:
                if file == "gradle.properties":
                    for v in self.available:
                        if root.startswith(v):
                            continue
                    # get name of deepest foler
                    f = os.path.normpath(root).split("\\")[-1]
                    if f.__contains__("-"):
                        self.available.append(root)
        if len(self.available) == 0:
            log(FATAL, "No available mdk (compilers) found in %s" % mdk_parent_folder)

        blacklist_file = jp(os.path.dirname(__file__), "blacklist.json")
        if os.path.exists(blacklist_file):
            mod_id_blacklist = json.loads(get_file_contents(blacklist_file))

            for id in mod_id_blacklist["blacklisted"]:
                message = None
                level = -1
                type = id["type"]
                if type == "literal":
                    if self.id == id["value"]:
                        message = id["message"]
                        level: int = getattr(internal_shared, id["level"])
                    else:
                        return
                elif type == "regex":
                    ...
                else:
                    return
                if not message:
                    log(FATAL, "Invalid blacklist message type")
                if message["type"] == "literal":
                    msg = message["value"]
                elif message["type"] == "template":
                    msg = mod_id_blacklist["messages"][message["value"]]
                else:
                    log(FATAL, "Invalid message type")

                log(level, msg)
            # if self.id in mod_id_blacklist["blacklisted"]:
            #     log(FATAL, f"Blacklisted mod id {self.id}")

    def add_component(self, *, component: COMPONENT_TYPE, id: Optional[str]):
        if component.TYPE in ["loot_table", "tag"]:
            self.unordered_components.append(component)
        if id is None:
            log(FATAL, "No id provided for component")
        elif not is_valid_component_id(id):
            log(FATAL, f"Invalid component id: '{id}'")

        self.components[id] = component

    def add_components(self, items: dict[str | Any, COMPONENT_TYPE]):
        for key in items.keys():
            if not is_valid_component_id(key):
                log(FATAL, f"Invalid component id: '{key}'")
        self.components.update(items)

    def remove_component(self, id: str):
        del self.components[id]

    def remove_components(self, ids: list[str]):
        for id in ids:
            del self.components[id]

    def get_components(self, ids: list[str]):
        return [self.components[id] for id in ids]

    def get_component(self, id: str):
        return self.components[id]

    def __repr__(self) -> str:
        return (
            f"Mod(internal_id='{self.internal_id}', id='{self.id}', name='{self.name}', "
            f"author='{self.author}', description='{self.description}', version='{self.version}', "
            f"license='{self.license}', "
            f"components={self.components}"
        )

    def get_sorted_components(self) -> SortedComponents:
        sorted = SortedComponents(
            item_textures=[],
            item_models=[],
            block_textures=[],
            block_models=[],
            language={},
            items={},
            blocks={},
            creative_tabs={},
            internal_loot_tables=[],
            procedures={},
            recipes={},
            tags=[],
        )
        for component_id, component in self.components.items():
            if isinstance(component, Item):
                sorted["item_textures"].append(component.texture)
                sorted["item_models"].append(Model(component_id, None, True))
                sorted["language"].update(({component_id: component.name}))
                sorted["items"].update({component_id: component})
            elif isinstance(component, CreativeTab):
                sorted["creative_tabs"].update({component_id: component})
            elif isinstance(component, Block):
                sorted["block_textures"].append(component.texture)
                sorted["block_models"].append(Model(component_id, None))
                sorted["language"].update(({component_id: component.name}))
                sorted["blocks"].update({component_id: component})
                # actions["items"]
            elif isinstance(component, Procedure):
                sorted["procedures"].update({component_id: component})
            elif isinstance(component, Recipe):
                sorted["recipes"].update({component_id: component})
            else:
                raise Exception("Unknown component type '%s" % type(component))

        for component in self.unordered_components:
            if isinstance(component, Tag):
                sorted["tags"].append(component)
            elif isinstance(component, LootTable):
                sorted["internal_loot_tables"].append(component)
            else:
                raise Exception("Unknown unsorted component type '%s" % type(component))

        return sorted

    @profile
    def generate(
        self, minify: bool = True, _language_update_file: Unused = None
    ) -> None:

        self.minify = minify

        actions = self.get_sorted_components()

        # log(DEBUG, "Cleaning Cache")
        fast_rmtree(common_cache)

        # log(DEBUG, "Iterating through available paths")
        multithreading = True
        if multithreading:
            with ThreadPoolExecutor() as executor:
                executor.map(
                    self.safe_generate_mod_for_path,
                    self.available,
                    [actions] * len(self.available),  # There has got to be a better way
                )
        else:
            for path in self.available:
                # Adding the try except doubled the generation time - Not gud :(
                self.safe_generate_mod_for_path(path, actions)
        print_performance()

    def safe_generate_mod_for_path(self, path: str, actions: SortedComponents):
        try:
            return self.generate_mod_for_path(path, actions)
        except SystemExit:
            pass
        except BaseException as e:
            print("An error occured while generating...")
            print(e)
        return None

    def generate_mod_for_path(self, mdk_path: str, actions: SortedComponents):
        start = time.perf_counter()
        things_added: list[str] = (
            []
        )  # Document what got added so no unncessary bundlers are inserted in the entry point file

        def get_info_from_path(path: str):
            info: list[str] = path.replace("\\", "/").split("/")[-1].split("-")

            match len(info):
                case 1:
                    raise Exception(
                        "Invalid mod path (Expected file of {mod_loader}-{minecraft_version}-{mod_loader_version} but got '%s'): %s"
                        % (info, path)
                    )
                case 2:
                    mod_loader, minecraft_version = info
                    mod_loader_version = ""
                case 3:
                    mod_loader, minecraft_version, mod_loader_version = info
                case _:
                    mod_loader, minecraft_version, mod_loader_version, *_ = info
            assert isinstance(mod_loader, str)
            assert isinstance(minecraft_version, str)
            assert isinstance(mod_loader_version, str)
            return mod_loader, minecraft_version, mod_loader_version

        mod_loader_, minecraft_version_, mod_loader_version_ = get_info_from_path(
            mdk_path
        )

        mod_info = ModInfo(
            internal_id=self.internal_id,
            id=self.id,
            minecraft_version=minecraft_version_,
            mod_loader_version=mod_loader_version_,
            mod_loader=mod_loader_,
        )

        triple_trouble = [
            mod_info["mod_loader"],
            mod_info["minecraft_version"],
            mod_info["mod_loader_version"],
        ]
        skip_message = f"skipping " + " ".join(triple_trouble)
        unique_name = "_".join(triple_trouble)

        replace_files = os.path.join(
            this,
            mod_info["mod_loader"],
            mod_info["minecraft_version"],
            mod_info["mod_loader_version"],
        )
        if mod_info["mod_loader_version"]:  # not os.path.exists(replace_files):
            replace_files = os.path.join(
                this, mod_info["mod_loader"], mod_info["minecraft_version"]
            )
            log(
                INFO,
                "Now generating for %s %s"
                % (mod_info["mod_loader"].title(), mod_info["minecraft_version"]),
            )
        else:
            log(
                INFO,
                "Now generating for %s %s (%s)"
                % (
                    mod_info["mod_loader"].title(),
                    mod_info["minecraft_version"],
                    mod_info["mod_loader_version"],
                ),
            )

        default_path = jp(this, "defaults")
        performance_handler(unique_name, "Init", "Figuring out version", start)

        performance_handler(
            unique_name, "Plugin setup", "Setting up Configurator", None
        )

        ##### GENERATING DATAPACK/RESOURCEPACK MOD THINGS
        configurator_path = jp(replace_files, "configurator.py")
        if not os.path.exists(configurator_path):
            log(
                FATAL,
                f"{unique_name} Configurator at {configurator_path} does not exist, skipping {mod_info['mod_loader']} {mod_info['minecraft_version']} {mod_info['mod_loader_version']}",
            )

        def apply_configurator_to_dict(
            configurator_path: str, configurator: dict[str, Callable[..., Any]]
        ):
            for key, value in import_module_from_full_path(
                configurator_path
            ).__dict__.items():
                if key.startswith("__"):
                    continue
                configurator[key] = value
            return configurator

        configurator: dict[str, Callable[..., Any]] = {}
        configurator = apply_configurator_to_dict(configurator_path, configurator)
        configurator = apply_configurator_to_dict(
            jp(default_path, "configurator.py"), configurator
        )

        final_cache_path = jp(common_cache, unique_name, "final")
        template_cache_path = jp(common_cache, unique_name, "template")

        ###

        info_path = jp(
            replace_files, "info.json"
        )  # This says what minecraft versions it supports
        if not os.path.exists(info_path):
            log(
                FATAL,
                f"{unique_name} Info path {info_path} does not exist, {skip_message}",
            )

        info_replace = json.loads(get_file_contents(info_path))

        ###

        resource_path = jp(replace_files, "things", "resources")
        if not os.path.exists(resource_path):
            resource_path = jp(default_path, "resources")
            # log(ERROR, f"Resource path {resource_path} does not exist, skipping {mod_loader} {minecraft_version} {mod_loader_version}")
            # continue

        performance_handler(
            unique_name,
            "Header",
            "Assembling cache data/resource packs (%s)" % len(self.external_packs),
            None,
        )

        assemble_pack(
            resource_path,
            template_cache_path,
            final_cache_path,
            self.id,
            self,
            mod_info,
            info_replace,
        )

        performance_handler(
            unique_name,
            "Header",
            "Merging given resources into cache (%s)" % len(self.external_packs),
            None,
        )
        del resource_path
        for pack in self.external_packs:
            copy_and_rename_builtin(pack, template_cache_path, self.id)

        os.makedirs(final_cache_path, exist_ok=True)

        performance_handler(
            unique_name, "Header", "Setting up datapack/resourcepack", None
        )

        mdk_src_main = os.path.join(mdk_path, "src/main")
        java_path = os.path.join(
            mdk_src_main, "java/" + self.internal_id.replace(".", "/")
        )
        resource_path = os.path.join(mdk_src_main, "resources/")

        # del resource_path, mdk_path, mdk_src_main

        code_java_cache_path = os.path.join(final_cache_path, "code", "java")

        pack_path = os.path.join(final_cache_path, "packs")
        resource_pack_path = os.path.join(pack_path, "assets", self.id)
        data_pack_path = os.path.join(pack_path, "data")

        # pack.mcmeta
        os.makedirs(jp(pack_path, "META-INF"), exist_ok=True)

        pack = get_file_contents(jp(this, "pack.mcmeta"))
        versions = json.loads(get_file_contents(jp(this, "versions.json")))
        pack_version = versions.get(mod_info["minecraft_version"], None)
        if pack_version is None:
            raise Exception(
                "Unknown pack version for %s in versions.json"
                % mod_info["minecraft_version"]
            )

        pack = replace(
            pack,
            {
                "version": str(pack_version),
            },
        )

        write_to_file(jp(pack_path, "pack.mcmeta"), pack)

        # mods.toml
        pack = get_file_contents(jp(this, "mods.toml"))

        write_to_file(jp(pack_path, "META-INF/mods.toml"), pack)

        ### Actual Mod stuff
        if not os.path.exists(code_java_cache_path):
            os.makedirs(code_java_cache_path)

        tag_manager = TagManager()

        block_amount = len(actions["blocks"])
        if block_amount == 0:
            pass
            # performance_handler(unique_name, "Blocks", "Skipping blocks", None)
        else:
            performance_handler(
                unique_name,
                "Blocks",
                "Generating code (%s)" % block_amount,
                None,
            )
            map_color_path = jp(replace_files, "blocks/map_colors.json")
            if not os.path.exists(map_color_path):
                log(
                    WARNING,
                    f"{unique_name} Block color path not found/not supported (%s)"
                    % map_color_path,
                )
                map_color_path = None

            fallback_path = jp(
                default_path,
                "resources",
                "assets",
                "builtin",
                "textures",
                "blocks",
                "error.png",
            )
            block_items, block_loot_tables, block_translations = generate_blocks(
                actions["blocks"],
                self,
                template_cache_path,
                replace_files,
                configurator,
                code_java_cache_path,
                map_color_path,
                fallback_path,
                tag_manager,
                unique_name,
                mod_info,
                info_replace,
            )
            actions["items"].update(block_items)
            actions["internal_loot_tables"].extend(block_loot_tables)
            actions["language"].update(block_translations)
            del block_items, block_loot_tables, block_translations

        # ITEMS

        item_amount = len(actions["items"])
        if item_amount == 0:
            # performance_handler(unique_name, "Items", "Skipping items", None)
            pass
        else:
            performance_handler(
                unique_name,
                "Items",
                "Generating code (Bundler) (%s)" % item_amount,
                None,
            )
            item_bundler, item_files, translation_keys = handle_bundler(
                {
                    "bundler": jp(replace_files, "items/item_bundler.java"),
                    "import": jp(replace_files, "items/import_line.java"),
                    "code": jp(replace_files, "items/item_code.java"),
                    "component": jp(replace_files, "items/item_component.java"),
                    "properties": jp(replace_files, "items/properties.json"),
                },
                self,
                actions["items"],
                configurator,
                self.minify,
            )

            actions["language"].update(translation_keys)
            performance_handler(unique_name, "Items", "Writing code to cache", None)

            write_to_file(jp(code_java_cache_path, "ModItems.java"), item_bundler)
            things_added.append("items")

            for file, code in item_files.items():
                write_to_file(jp(code_java_cache_path, f"items/{file}.java"), code)

            del item_bundler, item_files, translation_keys

        cerative_tab_amount = len(actions["creative_tabs"])
        if cerative_tab_amount == 0:
            pass
            # performance_handler(
            #     unique_name,
            #     "Creative Tabs",
            #     "Skipping creative tabs",
            #     None,
            # )
        else:
            performance_handler(
                unique_name,
                "Items",
                "Generating code (Bundler) (%s)" % cerative_tab_amount,
                None,
            )
            creative_tab_bundler, creative_tab_files, translation_keys = handle_bundler(
                {
                    "bundler": jp(
                        replace_files,
                        "creative_tabs/creative_tab_bundler.java",
                    ),
                    "import": jp(replace_files, "creative_tabs/import_line.java"),
                    "code": jp(
                        replace_files,
                        "creative_tabs/creative_tab_code.java",
                    ),
                    "component": jp(
                        replace_files,
                        "creative_tabs/creative_tab_component.java",
                    ),
                    "item": jp(
                        replace_files,
                        "creative_tabs/creative_tab_item.java",
                    ),
                    "properties": jp(replace_files, "creative_tabs/properties.json"),
                },
                self,
                actions["creative_tabs"],
                configurator,
                self.minify,
            )

            actions["language"].update(translation_keys)
            performance_handler(
                unique_name, "Creative Tabs", "Writing code to cache", None
            )

            with open(jp(code_java_cache_path, "ModCreativeModeTabs.java"), "w") as f:
                f.write(creative_tab_bundler)
            things_added.append("creative_mode_tabs")

            for file, code in creative_tab_files.items():
                write_to_file(
                    jp(code_java_cache_path, f"creative_tabs/{file}.java"), code
                )

            del creative_tab_bundler, creative_tab_files, translation_keys

        procedure_amount = len(actions["procedures"])
        if procedure_amount == 0:
            pass
            # performance_handler(
            #     unique_name,
            #     "Procedures",
            #     "Skipping procedures",
            #     None,
            # )
        else:
            performance_handler(
                unique_name, "Procedures", "Generating (%s)" % procedure_amount, None
            )
            event_wrapper_location = jp(replace_files, "procedures/event_handler.java")
            if not os.path.exists(event_wrapper_location):
                log(
                    FATAL,
                    f"{unique_name} Unable to find event wrapper at '%s', %s"
                    % (event_wrapper_location, skip_message),
                )
            total_code = ""
            total_contexts: dict[str, str] = {}
            total_imports: list[str] = []
            for id, procedure in actions["procedures"].items():
                procedure: Procedure
                if procedure.event:
                    new = ProcedureInternal()
                    new.load_blocks(jp(os.path.dirname(__file__), "procedures"))
                    code, contexts, imports = new.handle_event(
                        procedure.content,
                        "%s-%s"
                        % (
                            mod_info["mod_loader"],
                            mod_info["minecraft_version"],
                        ),  # Improve this
                        procedure.event,
                    )
                    total_code += "\n" + code
                    total_imports.extend(imports)
                    total_contexts.update(contexts)
                else:
                    log(
                        WARNING,
                        f"{unique_name} Procedure %s has no event, %s"
                        % (id, skip_message),
                    )

            total_imports = list(set(total_imports))
            event_wrapper = get_file_contents(event_wrapper_location)
            event_wrapper = format_text(
                event_wrapper,
                self,
                mod_info,
                {
                    "imports": "\n".join(["import %s;" % x for x in total_imports]),
                    "events": total_code,
                    "contexts": "\n".join(total_contexts.values()),
                },
            )
            performance_handler(unique_name, "Procedures", "Writing to file", None)

            write_to_file(jp(code_java_cache_path, "EventHandler.java"), event_wrapper)

            things_added.append("procedures")

        performance_handler(unique_name, "Translation", "Writing to file", None)
        ### Translations

        translation_path = jp(resource_pack_path, "lang/en_us.json")
        os.makedirs(os.path.dirname(translation_path), exist_ok=True)
        with open(translation_path, "w") as f:
            json.dump(actions["language"], f, indent=4)

        performance_handler(unique_name, "Models", "Setting up", None)

        ### Textures + Models
        class RquiredTexture(TypedDict):
            item: set[str]
            block: set[str]

        required_textures = RquiredTexture(
            item=set(),
            block=set(),
        )

        # Block models/blockstates
        block_model_path = jp(resource_pack_path, "models/block")
        if not os.path.exists(block_model_path):
            os.makedirs(block_model_path)
        blockstate_model_path = jp(final_cache_path, "assets", self.id, "blockstates")
        if not os.path.exists(blockstate_model_path):
            os.makedirs(blockstate_model_path)

        block_state_path_template = jp(
            template_cache_path, "assets", self.id, "blockstates"
        )

        block_states = {
            "none": jp(block_state_path_template, "cube.json"),
            "falling": jp(block_state_path_template, "cube.json"),
            "slab": jp(block_state_path_template, "slab.json"),
            "stair": jp(block_state_path_template, "stairs.json"),
            "fence": jp(block_state_path_template, "fence.json"),
            "fence_gate": jp(block_state_path_template, "fence_gate.json"),
            "door": jp(block_state_path_template, "door.json"),
            "trap_door": jp(block_state_path_template, "trap_door.json"),
            "button": jp(block_state_path_template, "button.json"),
            "leaves": jp(block_state_path_template, "cube.json"),
            "pressure_plate": jp(block_state_path_template, "pressure_plate.json"),
            "log": jp(block_state_path_template, "log.json"),
            "wall": jp(block_state_path_template, "wall.json"),
        }
        performance_handler(
            unique_name,
            "Models",
            "Generating Block Models and blockstates (%s)" % len(actions["blocks"]),
            None,
        )
        block_state_jobs_paths = []
        block_state_jobs_contents = []
        block_state_jobs_length = 0

        block_model_jobs_paths = []
        block_model_jobs_contents = []
        block_model_jobs_length = 0

        for block_id, block in actions["blocks"].items():
            block_id: str
            block: Block

            # Block state

            blockstate_path_for_this_block = jp(
                template_cache_path,
                "assets",
                self.id,
                "blockstates",
                (
                    block_states[block.rotation]
                    if block.blocktype == "cube"
                    else block_states[block.blocktype]
                ),
            )
            blockstate_data = replace(
                get_file_contents(blockstate_path_for_this_block),
                {"mod_id": self.id, "block_id": block_id},
            )

            blockstate_path = jp(blockstate_model_path, f"{block_id}.json")

            block_state_jobs_paths.append(blockstate_path)
            block_state_jobs_contents.append(blockstate_data)
            block_state_jobs_length += 1

            # BLOCK STATE DONE

            all_models = get_all_models_in_blockstate(
                get_file_contents(blockstate_path_for_this_block)
            )
            # Models

            for model in set(all_models):
                model_path = (
                    jp(
                        template_cache_path,
                        "assets",
                        model.replace(
                            "{mod_id}:block/{block_id}",
                            f"{self.id}/models/block/{block.blocktype}",
                        ),
                    )
                    + ".json"
                )
                if not os.path.exists(model_path):
                    old = model_path
                    model_path = (
                        jp(
                            template_cache_path,
                            "assets",
                            model.replace(
                                "{mod_id}:block/{block_id}",
                                f"{self.id}/models/block/cube",
                            ),
                        )
                        + ".json"
                    )
                    if not os.path.exists(model_path):
                        log(
                            FATAL,
                            f"{unique_name} Unable to find suitable model for block {self.id}, tried following paths: \n>{old}\n>{model_path}",
                        )

                model_data = get_file_contents(model_path)
                model_data = replace(model_data, block.texture)
                model_data = replace(
                    model_data,
                    {"mod_id": self.id},
                )
                for key, val in block.texture.items():
                    if key == "render_type":
                        continue
                    required_textures["block"].add(val.split("/")[-1])

                model_name_path_extension = model.replace(
                    "{mod_id}:block/{block_id}",
                    "",
                )
                model_path = jp(
                    block_model_path, f"{block_id}{model_name_path_extension}.json"
                )
                block_model_jobs_paths.append(model_path)
                block_model_jobs_contents.append(model_data)
                block_model_jobs_length += 1
        performance_handler(
            unique_name,
            "Models",
            "Writing block models to cache (%s)" % block_model_jobs_length,
            None,
        )
        write_to_files(
            block_model_jobs_paths, block_model_jobs_contents, block_model_jobs_length
        )

        # for block_model_path, block_model_data in block_model_jobs:
        #     with open(block_model_path, "w") as f:
        #         f.write(block_model_data)

        performance_handler(
            unique_name,
            "Models",
            "Generating (Block) Item Models (%s)" % len(actions["items"]),
            None,
        )
        # Item models

        item_model_path = jp(resource_pack_path, "models/item")
        item_model_jobs = []

        for item_id, item in actions["items"].items():
            item_id: str
            item: Item
            temp = item.display_item.split(";", 1)
            if len(temp) == 1:
                display_item_mod_id, display_item_texture = (
                    self.id,
                    item.texture,
                )
                display_type = temp[0]
            else:
                display_type, rest = temp
                if ":" in rest:
                    display_item_mod_id, display_item_texture = rest.split(":", 1)
                else:
                    display_item_mod_id = self.id
                    display_item_texture = rest

            match display_type:
                case "block":
                    item_model = jp(
                        template_cache_path,
                        "assets",
                        f"{self.id}/models/block/{item.block_item_type}_item.json",
                    )
                    if not os.path.exists(item_model):
                        item_model = jp(
                            template_cache_path,
                            "assets",
                            f"{self.id}/models/block/cube_item.json",
                        )
                    parent = json.loads(get_file_contents(item_model)).get("parent")

                    if parent:
                        ### ARE YOU SURE THIS WILL WORK?
                        # I HAVE NO IDEA

                        # HAHA NOPE IT DOES NOT
                        block_model_output_path = replace(
                            parent,
                            {
                                "mod_id": display_item_mod_id,
                                "block_id": display_item_texture,
                            },
                        ).replace(":", "/models/")
                        block_model_output_path = (
                            jp(final_cache_path, "assets", block_model_output_path)
                            + ".json"
                        )
                        if not os.path.exists(block_model_output_path):
                            if item.block_item_type is None:
                                log(
                                    FATAL,
                                    f"{unique_name} Block item type is None for block item",
                                )

                            block_model_input_path = replace(
                                parent,
                                {
                                    "mod_id": self.id,
                                    "block_id": item.block_item_type,
                                },
                            ).replace(":", "/models/")

                            model_path = (
                                jp(
                                    template_cache_path,
                                    "assets",
                                    block_model_input_path,
                                )
                                + ".json"
                            )
                            if not os.path.exists(model_path):
                                model_path = (
                                    jp(
                                        template_cache_path,
                                        "assets",
                                        os.path.dirname(block_model_input_path),
                                        "cube",
                                    )
                                    + ".json"
                                )
                                if not os.path.exists(model_path):
                                    log(
                                        FATAL,
                                        f"{unique_name} Cannot get item model path :(",
                                    )
                                else:
                                    log(
                                        WARNING,
                                        f"{unique_name} Unable to find item model for %s, using default cube instead"
                                        % item_id,
                                    )

                            item_model_data = replace(
                                get_file_contents(
                                    model_path,
                                    info="Getting item model",
                                ),
                                combine_dicts(item.block_item_textures, {"mod_id": display_item_mod_id}),  # type: ignore
                            )
                            item_model_jobs.append(
                                (block_model_output_path, item_model_data)
                            )

                    if not os.path.exists(item_model):
                        item_model = jp(
                            template_cache_path,
                            "assets",
                            f"{self.id}/models/block/cube_item.json",
                        )
                case "item":
                    item_model = jp(
                        template_cache_path,
                        "assets",
                        f"{self.id}/models/item/items.json",
                    )
                    required_textures["item"].add(item.texture)
                case _:
                    log(FATAL, f"{unique_name} Unknown display type {display_type}")

            model_data = replace(
                get_file_contents(item_model),
                (
                    {
                        "texture": item.texture,
                        "mod_id": display_item_mod_id,
                        "block_id": display_item_texture,
                    }
                ),
            )

            model_path = jp(item_model_path, f"{item_id}.json")
            item_model_jobs.append((model_path, model_data))
            del model_data, model_path, item

        performance_handler(
            unique_name,
            "Models",
            "Writing (block) item models (%s)" % len(item_model_jobs),
            None,
        )
        for path, model in item_model_jobs:
            write_to_file(block_model_output_path, item_model_data)

        performance_handler(
            unique_name,
            "Blockstates",
            "Writing blockstates generated in models section to cache (%s)"
            % block_state_jobs_length,
            None,
        )

        write_to_files(
            block_state_jobs_paths, block_state_jobs_contents, block_state_jobs_length
        )

        performance_handler(
            unique_name,
            "Textures",
            "Gathering required textures (%s)"
            % sum(
                [
                    len(cast(list[str], textures))
                    for textures in required_textures.values()
                ]
            ),
            None,
        )
        # write_to_file("./required_textures.json", json.dumps(required_textures))
        texture_jobs = []

        for dir, textures in required_textures.items():
            textures = cast(list[str], textures)
            for texture in textures:
                texture_path = jp(
                    template_cache_path, "assets", self.id, "textures", dir, texture
                )
                if not os.path.exists(jp(resource_pack_path, "textures", dir)):
                    os.makedirs(jp(resource_pack_path, "textures", dir))

                target_png = jp(texture_path) + ".png"
                if os.path.exists(target_png):
                    png_final_path = jp(
                        resource_pack_path, "textures", dir, texture + ".png"
                    )
                    texture_jobs.append((target_png, png_final_path))
                    if os.path.exists(jp(texture_path) + ".png.mcmeta"):
                        texture_jobs.append(
                            (
                                jp(texture_path) + ".png.mcmeta",
                                jp(
                                    resource_pack_path,
                                    "textures",
                                    dir,
                                    texture + ".png.mcmeta",
                                ),
                            )
                        )
                else:
                    if texture.__contains__(":"):
                        log(
                            INFO,
                            f"{unique_name} Texture {texture} not found. It will be assumed it exists elsewhere undefined.",
                        )
                    else:
                        log(
                            WARNING,
                            f"{unique_name} Texture {texture} not found. ({jp(texture_path) + '.png'})",
                        )

        performance_handler(
            unique_name,
            "Textures",
            "Copying gathered textures (%s)" % len(texture_jobs),
            None,
        )

        for target_png, png_final_path in texture_jobs:
            shutil.copyfile(target_png, png_final_path)

        performance_handler(
            unique_name,
            "Loot Tables",
            "Writing Loot Tables to cache (%s)" % len(actions["internal_loot_tables"]),
            None,
        )

        for loot_table in actions["internal_loot_tables"]:
            loot_table: LootTable
            new_loot_table_path = jp(
                data_pack_path,
                loot_table.mod_id,
                "loot_tables",
                loot_table.context,
                f"{loot_table.name}.json",
            )
            if isinstance(loot_table.entries, dict):
                entries = json.dumps(loot_table.entries)
            else:
                entries = loot_table.entries
            write_to_file(new_loot_table_path, entries)

        performance_handler(
            unique_name,
            "Loot Tables",
            "Writing Tags to cache (%s)" % len(tag_manager.tags),
            None,
        )

        for path, values in tag_manager.tags.items():
            tag_path = jp(data_pack_path, id, "tags", path + ".json")
            thing: dict[str, list[str] | bool] = {
                "values": [add_mod_id_if_missing(x, self) for x in values],
                "replace": False,  # Should this be configureable? Yes. Do I know how to properly do that while providing a clean api? No.
            }

            write_to_file(tag_path, json.dumps(thing))

        performance_handler(
            unique_name,
            "Loot Tables",
            "Generating Recipes (%s)" % len(actions["recipes"]),
            None,
        )

        recipes_jobs_paths = []
        recipes_jobs_contents = []
        recipes_jobs_length = 0

        for key, i in actions["recipes"].items():
            i: Recipe
            new_recipe_path = jp(
                data_pack_path,
                self.id,
                "recipes",
                i.recipe_type,
                f"{key}.json",
            )
            recipe = i.generate(self)
            if recipe:
                recipes_jobs_paths.append(new_recipe_path)
                recipes_jobs_contents.append(recipe)
                recipes_jobs_length += 1

        performance_handler(
            unique_name,
            "Loot Tables",
            "Writing to cache (%s)" % recipes_jobs_length,
            None,
        )
        write_to_files(recipes_jobs_paths, recipes_jobs_contents, recipes_jobs_length)

        ### EVERYTHING IS DONE -> COPY CACHE TO MDK

        performance_handler(unique_name, "Cache", "Clearing MDK", None)
        fast_rmtree(mdk_src_main)

        performance_handler(
            unique_name, "Cache", "Copying cache to MDK (Data/Resource pack)", None
        )
        fast_copytree(pack_path, resource_path)
        performance_handler(
            unique_name, "Cache", "Copying cache to MDK (Java code)", None
        )
        fast_copytree(code_java_cache_path, java_path)

        overwrite_time = time.perf_counter()
        total_overwrites = 0
        # Deal with overwrites
        overwrite_file_path = jp(replace_files, "overwrite.json")
        if os.path.exists(overwrite_file_path):
            overwrite_data = json.loads(get_file_contents(overwrite_file_path))
            total_overwrites = len(overwrite_data)
            for action, overwrites in overwrite_data.items():
                if action == "java_path":
                    action_path = java_path
                elif action == "surface":
                    action_path = mdk_path
                elif action == "resources":
                    action_path = resource_path
                else:
                    log(
                        FATAL,
                        f"{unique_name} Unknown action path '{action}' in {overwrite_file_path}",
                    )
                for overwrite in overwrites:
                    file = jp(replace_files, overwrite["file"])
                    if not os.path.exists(file):
                        log(
                            FATAL, f"{unique_name} Overwrite file {file} does not exist"
                        )
                    offset = overwrite["offset"]
                    file_contents = get_file_contents(file)
                    rename = overwrite.get("rename")

                    if overwrite["format"]:
                        file_contents = format_text(
                            file_contents, self, mod_info, info_replace
                        )

                    write_file_path = jp(
                        action_path,
                        offset,
                        (
                            format_text(rename, self, mod_info, info_replace)
                            if rename
                            else os.path.basename(file)
                        ),
                    )
                    write_to_file(write_file_path, file_contents)

        performance_handler(
            unique_name,
            "Cache",
            "Dealing with overwrite files (Plugin) (%s)" % total_overwrites,
            overwrite_time,
        )

        performance_handler(
            unique_name, "Cache", "Generating and writing server/entry point", None
        )

        server_file_path = jp(replace_files, "server.java")

        if not os.path.exists(server_file_path):
            log(
                FATAL,
                f"{unique_name} Server file at {server_file_path} does not exist, {skip_message}",
            )

        server_import_file_path = jp(replace_files, "settings.json")
        if not os.path.exists(server_import_file_path):
            log(
                FATAL,
                f"{unique_name} Server config file at {server_import_file_path} does not exist, {skip_message}",
            )

        server_file = get_file_contents(server_file_path)
        server_import_file = json.loads(get_file_contents(server_import_file_path))
        # client_file = get_file_contents(client_file_path)
        pre_imports: list[str] = []
        pre_setups: list[str] = []
        # settings.json, you'll figure it out
        # Alright past me, I did because of your snazzy comment. Still hate you though
        for x in things_added:
            pre_imports.append(server_import_file[x]["import"])
            pre_setups.append(server_import_file[x]["setup"])

        imports = format_text("\n".join(pre_imports), self, mod_info, info_replace)
        setups = format_text("\n".join(pre_setups), self, mod_info, info_replace)

        server_file = format_text(
            server_file, self, mod_info, {"imports": imports, "setups": setups}
        )
        # client_file = format_text(client_file, self)

        write_to_file(jp(java_path, f"{self.id.title()}.java"), server_file)
        # write_to_file(jp(java_path, f"ClientEvents.java"), client_file)

        del server_file

        performance_add_end_marker(unique_name)


def format_text(
    text: str,
    mod: Mod,
    mod_info: ModInfo,
    info_replace: dict[str, str],
    additional_replace: dict[str, str] = {},
) -> str:
    return replace(
        text,
        combine_dicts(
            combine_dicts(
                {
                    "mod_id": mod.id,
                    "internal_mod_id": mod.internal_id,
                    "mod_id_upper": mod.id.title(),
                    "mod_name": mod.name,
                    "author": mod.author,
                    "description": mod.description,
                    "version": mod.version,
                    "mod_version": mod.version,
                    "homepage": mod.homepage,
                    "minecraft_version": mod_info["minecraft_version"],
                    "mod_loader_version": mod_info["mod_loader_version"],
                },
                info_replace,
            ),
            additional_replace,
        ),
    )


def get_all_models_in_blockstate(blockstate: str):
    return re.findall('"model": "(.*?)"', blockstate)


from . import presets

__all__ = ["Mod", "presets", "add_mod_id_if_missing"]

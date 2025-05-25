import os
from typing import Optional, Union, Any, TypedDict, Callable, cast, NoReturn

from .fast_copy import fast_copytree


# import csv # Later.
import json
import shutil
import re
from pathlib import Path
import time
from collections.abc import Mapping
import sys

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
    # RecipeCrafting,
    # RecipeItemTag,
    # RecipeCraftingShapeless,
)
from .shared import (
    log,
    FATAL,
    ERROR,
    WARNING,
    INFO,
    DEBUG,
    jp,
    get_file_contents,
    replace,
    export_class,
    import_class,
)
from .one_off_functions import get_closest_map_color, import_module_from_full_path
from .procedures import ProcedureInternal


def add_mod_id_if_missing(id: str, mod: "Mod"):

    if id.__contains__(":"):
        return id
    return f"{mod.id}:{id}"


def is_valid_internal_mod_id(id: str):
    if not id.islower():
        return False
    for char in id:
        if char not in "qwertzuiopasdfghjklyxcvbnm.":
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
        mdk_folder=mdk_folder,
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


# def import_mod(mod_code: dict[str, Any], path: str):
#     components: dict[str, dict[str, Any]] = mod_code.get("components", {})
#     mod_credintials: dict[str, str] = mod_code.get("mod", {})
#     del mod_code
#     mod = Mod(
#         internal_id=mod_credintials.get("internal_id", "com.example.mod"),
#         public_id=mod_credintials.get("public_id", "example_mod"),
#         name=mod_credintials.get("name", "Example Mod"),
#         description=mod_credintials.get("description", ""),
#         author=mod_credintials.get("author", ""),
#         version=mod_credintials.get("version", "0.0.0"),
#         license=mod_credintials.get("license", "None"),
#         mdk_folder=path,
#     )

#     for component_id, component_content in components.items():
#         type = component_content.pop("type")

#         match type:
#             case "item":
#                 configuration = component_content.pop("configuration", {})
#                 food_properties: dict[str, Any] = configuration.pop(
#                     "food_properties", None
#                 )
#                 if food_properties is None:
#                     food_properties = {}
#                 component = Item(
#                     name=component_content.pop("name", ""),
#                     texture=component_content.pop("texture", ""),
#                     stack_size=configuration.pop("stack_size", 1),
#                     durability=configuration.pop("durability", None),
#                     unrepairable=configuration.pop("unrepairable", False),
#                     fire_resistant=configuration.pop("fire_resistant", False),
#                     is_block_item=component_content.pop("is_block_item", False),
#                     remains_after_crafting=configuration.pop(
#                         "remains_after_crafting", False
#                     ),
#                     rarity=configuration.pop("rarity", "common"),
#                     enchantability=configuration.pop("enchntability", 0),
#                     block_break_speed=configuration.pop("block_break_speed", 1.0),
#                     can_break_any_block=configuration.pop("can_break_any_block", False),
#                     item_animation=configuration.pop("item_animation", 0),
#                     is_meat=food_properties.pop("is_meat", False),
#                     nutrition=food_properties.pop("nutrition", 0),
#                     saturation=food_properties.pop("saturation", 0),
#                     fast_consumed=food_properties.pop("fast_consumed", False),
#                     always_edible=food_properties.pop("always_edible", False),
#                 )
#             case "creative_menu":
#                 configuration = component_content.pop("configuration", {})
#                 component = CreativeTab(
#                     name=component_content.pop("name", ""),
#                     icon_item=component_content.pop("icon_item", ""),
#                     items=configuration.pop("item_ids", []),
#                     hide_title=configuration.pop("hide_title", False),
#                     no_scrollbar=configuration.pop("no_scrollbar", False),
#                     alignment_right=configuration.pop("alignment_right", False),
#                 )

#             case _:
#                 log(ERROR, f"Unknown component type: {type}")

#         if not component_content == {}:
#             log(WARNING, f"Unknown component properties: {component_content}")
#         mod.add_component(id=component_id, component=component)

#     return mod


translations = {
    "CreativeModeTab": "creative_tab.{internal_mod_id}.{component_id}",
    "Item": "item.{internal_mod_id}.{component_id}",
    "Block": "block.{internal_mod_id}.{component_id}",
}


def generate_blocks(
    blocks: dict[str, Block],
    self: "Mod",
    template_path: str,
    replace_files: str,
    configurator: dict[str, Callable[..., Any]],
    java_path: str,
    color_path: Optional[str],
    fallback_path: str,
) -> tuple[bool, dict[str, Item], list[LootTable], dict[str, str]]:
    return_items: dict[str, Item] = {}
    return_loot_tables: list[LootTable] = []
    # Generate block items and loot table for every block
    for block_id, block in blocks.items():
        block: Block
        if block.map_color is None and not color_path is None:
            stuff = format_text(block.texture["top"], self).split(":", 1)
            if len(stuff) == 2:
                texture = jp(stuff[0], "textures", stuff[1])
            else:
                raise BaseException(stuff)
            texture_path = jp(
                template_path,
                "assets",
                # self.id,
                # "textures",
                # "block",
                texture + ".png",
            )

            block.map_color = get_closest_map_color(
                texture_path, color_path, fallback_path
            )
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
                self.tags["minecraft"]["blocks/mineable/" + tool].append(block_id)

    # Call code bundler to generate the code for each block

    skip, block_bundler, block_files, translation_keys = handle_bundler(
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
    )

    if skip:
        return True, {}, [], {}

    write_to_file(jp(java_path, "ModBlocks.java"), block_bundler)
    # self.things_added.append("blocks")

    for file, code in block_files.items():
        write_to_file(jp(java_path, f"blocks/{file}.java"), code)

    return False, return_items, return_loot_tables, translation_keys


class Model:
    def __init__(
        self, name: str, model: Optional[str], item: Optional[bool] = None
    ) -> None:
        self.name = name
        self.model = model
        self.item = item


def combine_dicts(dict1: dict[Any, Any], dict2: dict[Any, Any]) -> dict[str, str]:
    return {**dict1, **dict2}


def write_to_file(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


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
) -> tuple[bool, str, dict[str, str], dict[str, str]]:
    if not os.path.exists(paths["bundler"]):
        log(ERROR, f"File {paths['bundler']} does not exist")
        return True, "", {}, {}
    if not os.path.exists(paths["import"]):
        log(ERROR, f"File {paths['import']} does not exist")
        return True, "", {}, {}
    if not os.path.exists(paths["code"]):
        log(ERROR, f"File {paths['code']} does not exist")
        return True, "", {}, {}

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
        new_code = code
        # component code

        processing_block_item = False
        if isinstance(component, Item):
            naming = "Item"
            processing_block_item = component.is_block_item
        elif isinstance(component, CreativeTab):
            naming = "CreativeModeTab"
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
            naming = "Block"
            # type_initializer = json.loads(get_file_contents(paths["initializer"]))
            # extra["initializer"] = type_initializer.get(
            #     component.blocktype, type_initializer["cube"]
            # ).get("before", "")

            # extra["after"] = type_initializer.get(
            #     component.blocktype, type_initializer["cube"]
            # ).get("after", "")

            extra["block_type"] = (
                component.blocktype.replace("_", " ")
                .title()
                .replace(" ", "")
                .replace("Cube", "")
            )

        else:
            raise Exception("Invalid type: " + component.TYPE)

        # typed_component_id = camel_to_snake(naming) + "_" + component_id

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
            imports += ("\nimport net.minecraft.world.level.block.%sBlock;" % (component.blocktype.replace("_", " ").title()).replace(" ", "")) if not component.blocktype == "cube" else ""  # type: ignore
        new_code = replace(
            new_code,
            combine_dicts(
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
                },
                extra,
            ),
        )

        all_code[component_id.title() + naming] = new_code
        translation_key = replace(
            translations[naming],
            {"component_id": component_id, "internal_mod_id": mod.id},
        )
        if processing_block_item:
            continue
        translation_keys[translation_key] = component.name

        # import line code
        all_imports += replace(
            import_line,
            {
                "component_id": component_id,
                "internal_mod_id": mod.internal_id,
                "item_id_upper": component_id.title(),
            },
        )

        # component registry
        all_bundler_code += replace(
            bundler_component,
            {
                "component_id": component_id,
                "component_id_upper": component_id.title(),
            },
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

    return False, bundler, all_code, translation_keys


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

    if not mod_id or not mod_id.strip():
        raise ValueError("mod_id cannot be empty")

    if any(char in r'\/:*?"<>|' for char in mod_id):
        raise ValueError(f"mod_id contains invalid characters: {mod_id}")

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


def assemble_pack(
    resource_path: str,
    template_path: str,
    pack_path: str,
    mod_id: str,
    mod: "Mod",
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
            file_contents = format_text(file_contents, mod)

        write_to_file(jp(pack_path, file), file_contents)


def merge_packs(internal_pack: str, external_pack: str, mod_id: str):
    copy_and_rename_builtin(external_pack, internal_pack, mod_id)
    # shutil.copytree(external_pack, internal_pack, dirs_exist_ok=True)


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
    internal_items: dict[str, Item]
    internal_blocks: dict[str, Block]
    internal_creative_tabs: dict[str, CreativeTab]
    internal_loot_tables: list[LootTable]

    procedures: dict[str, Procedure]
    recipes: dict[str, Recipe]


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
        "tags",
        "unordered_components",
        "external_packs",
        "homepage",
        "minecraft_version",
        "mod_loader_version",
        "mod_loader",
        "info_replace",
        "things_added",
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
        mdk_folder: str,
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
        self.tags: dict[str, dict[str, list[str]]] = {"minecraft": {}}
        tools = ["axe", "pickaxe", "shovel", "hoe"]

        for tool in tools:
            self.tags["minecraft"]["blocks/mineable/" + tool] = []

        self.available: list[str] = []

        for root, _folders, files in os.walk(mdk_folder):

            if not root.startswith(mdk_folder):
                continue

            for file in files:
                if file == "gradle.properties":
                    for v in self.available:
                        if root.startswith(v):
                            continue
                    self.available.append(root)
        if len(self.available) == 0:
            log(FATAL, "No available mdk (compilers) found in %s" % mdk_folder)

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
                        level: int = getattr(shared, id["level"])
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

        self.components[id] = component

    def add_components(self, items: dict[str | Any, COMPONENT_TYPE]):
        for x in items.keys():
            if not isinstance(x, str):
                log(FATAL, f"Invalid component id: '{x}'")
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
            internal_items={},
            internal_blocks={},
            internal_creative_tabs={},
            internal_loot_tables=[],
            procedures={},
            recipes={},
        )
        for component_id, component in self.components.items():
            if isinstance(component, Item):
                sorted["item_textures"].append(component.texture)
                sorted["item_models"].append(Model(component_id, None, True))
                sorted["language"].update(({component_id: component.name}))
                sorted["internal_items"].update({component_id: component})
            elif isinstance(component, CreativeTab):
                sorted["internal_creative_tabs"].update({component_id: component})
            elif isinstance(component, Block):
                sorted["block_textures"].append(component.texture)
                sorted["block_models"].append(Model(component_id, None))
                sorted["language"].update(({component_id: component.name}))
                sorted["internal_blocks"].update({component_id: component})
                # actions["internal_items"]
            elif isinstance(component, Procedure):
                sorted["procedures"].update({component_id: component})
            elif isinstance(component, Recipe):
                sorted["recipes"].update({component_id: component})
            else:
                raise Exception("Unknown component type '%s" % type(component))

        return sorted

    @profile
    def generate(self, language_update_file: Optional[str] = None) -> None:
        this = os.path.dirname(__file__)

        log(DEBUG, "Sorting components")

        actions = self.get_sorted_components()

        log(DEBUG, "Cleaning Cache")

        common_cache = jp(this, "cache")

        try:
            shutil.rmtree(common_cache)
        except:
            pass

        log(DEBUG, "Iterating through available paths")
        for path in self.available:
            start = time.time()
            self.things_added: list[str] = (
                []
            )  # Document what got added so no unncessary bundlers are inserted in the entry point file

            def get_info_from_path(path: str):
                info: list[str] = path.replace("\\", "/").split("/")[-1].split("-")

                match len(info):
                    case 1:
                        raise Exception("Invalid mod path: %s" % path)
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

            self.mod_loader, self.minecraft_version, self.mod_loader_version = (
                get_info_from_path(path)
            )
            triple_trouble = [
                self.mod_loader,
                self.minecraft_version,
                self.mod_loader_version,
            ]
            skip_message = f"skipping " + " ".join(triple_trouble)
            unique_name = "_".join(triple_trouble)

            replace_files = os.path.join(
                this, self.mod_loader, self.minecraft_version, self.mod_loader_version
            )
            if self.mod_loader_version:  # not os.path.exists(replace_files):
                replace_files = os.path.join(
                    this, self.mod_loader, self.minecraft_version
                )
                log(
                    INFO,
                    "Now generating for %s %s"
                    % (self.mod_loader.title(), self.minecraft_version),
                )
            else:
                log(
                    INFO,
                    "Now generating for %s %s (%s)"
                    % (
                        self.mod_loader.title(),
                        self.minecraft_version,
                        self.mod_loader_version,
                    ),
                )

            default_path = jp(this, "defaults")

            log(DEBUG, "Setting up for given plugin")

            ##### GENERATING DATAPACK/RESOURCEPACK MOD THINGS
            configurator_path = jp(replace_files, "configurator.py")
            if not os.path.exists(configurator_path):
                log(
                    ERROR,
                    f"Configurator at {configurator_path} does not exist, skipping {self.mod_loader} {self.minecraft_version} {self.mod_loader_version}",
                )
                continue

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

            info_path = jp(replace_files, "info.json")
            if not os.path.exists(info_path):
                log(ERROR, f"Info path {info_path} does not exist, {skip_message}")
                continue

            self.info_replace = json.loads(get_file_contents(info_path))

            ###

            resource_path = jp(replace_files, "things", "resources")
            if not os.path.exists(resource_path):
                resource_path = jp(default_path, "resources")
                # log(ERROR, f"Resource path {resource_path} does not exist, skipping {mod_loader} {minecraft_version} {mod_loader_version}")
                # continue

            assemble_pack(
                resource_path, template_cache_path, final_cache_path, self.id, self
            )
            del resource_path
            for pack in self.external_packs:
                merge_packs(template_cache_path, pack, self.id)

            os.makedirs(final_cache_path, exist_ok=True)

            ###

            main_src_path = os.path.join(path, "src/main")
            java_path = os.path.join(
                main_src_path, "java/" + self.internal_id.replace(".", "/")
            )
            resource_path = os.path.join(main_src_path, "resources/")
            assets_path_self = os.path.join(final_cache_path, "assets", self.id)
            data_path = os.path.join(final_cache_path, "data")
            # data_path_self = os.path.join(final_cache_path, "data", self.id)
            try:
                shutil.rmtree(main_src_path)
            except:
                pass
            try:
                shutil.rmtree(resource_path)
            except:
                pass

            ### Initial Replacements

            # property_file = os.path.join(replace_files, "gradle.properties")

            # if not os.path.exists(property_file):
            #     log(ERROR, f"Property file at {property_file} does not exist, skipping {mod_loader} {minecraft_version} {mod_loader_version}")
            #     continue

            # properties = get_file_contents(property_file)

            # properties = replace(
            #     properties,
            #     combine_dicts(
            #         {
            #             "mod_version": self.version,
            #             "mod_name": self.name,
            #             "mod_author": self.author,
            #             "mod_description": self.description,
            #             "mod_license": self.license,
            #             "internal_mod_id": self.internal_id,
            #             "mod_id": self.id,
            #             "minecraft_version": minecraft_version,
            #             "mod_loader_version": mod_loader_version,
            #         },
            #         propertie_info,
            #     ),
            # )

            # write_to_file(jp(path, "gradle.properties"), properties)

            # pack.mcmeta
            os.makedirs(jp(resource_path, "META-INF"), exist_ok=True)

            pack = get_file_contents(jp(this, "pack.mcmeta"))
            versions = json.loads(get_file_contents(jp(this, "versions.json")))
            pack_version = versions.get(self.minecraft_version, None)
            if pack_version is None:
                raise Exception(
                    "Unknown pack version for %s in versions.json"
                    % self.minecraft_version
                )

            pack = replace(
                pack,
                {
                    "version": str(pack_version),
                },
            )

            write_to_file(jp(resource_path, "pack.mcmeta"), pack)

            # mods.toml
            pack = get_file_contents(jp(this, "mods.toml"))

            write_to_file(jp(resource_path, "META-INF/mods.toml"), pack)

            log(DEBUG, "Generating Content - Blocks")

            ### Actual Mod stuff
            if not os.path.exists(java_path):
                os.makedirs(java_path)

            # BLOCKS
            map_color_path = jp(replace_files, "blocks/map_colors.json")
            if not os.path.exists(map_color_path):
                log(
                    WARNING,
                    "Block color path not found/not supported (%s)" % map_color_path,
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

            if actions["internal_blocks"]:
                skip, block_items, block_loot_tables, block_translations = (
                    generate_blocks(
                        actions["internal_blocks"],
                        self,
                        template_cache_path,
                        replace_files,
                        configurator,
                        java_path,
                        map_color_path,
                        fallback_path,
                    )
                )
                actions["internal_items"].update(block_items)
                actions["internal_loot_tables"].extend(block_loot_tables)
                actions["language"].update(block_translations)
                del block_items, block_loot_tables, block_translations

            log(DEBUG, "Generating Content - Items")
            # ITEMS
            if actions["internal_items"]:
                skip, item_bundler, item_files, translation_keys = handle_bundler(
                    {
                        "bundler": jp(replace_files, "items/item_bundler.java"),
                        "import": jp(replace_files, "items/import_line.java"),
                        "code": jp(replace_files, "items/item_code.java"),
                        "component": jp(replace_files, "items/item_component.java"),
                        "properties": jp(replace_files, "items/properties.json"),
                    },
                    self,
                    actions["internal_items"],
                    configurator,
                )

                if skip:
                    continue
                actions["language"].update(translation_keys)

                write_to_file(jp(java_path, "ModItems.java"), item_bundler)
                self.things_added.append("items")

                for file, code in item_files.items():
                    write_to_file(jp(java_path, f"items/{file}.java"), code)

                del item_bundler, item_files, translation_keys

            log(DEBUG, "Generating Content - Creative Tabs")
            #### Creative Mode Tabs
            if actions["internal_creative_tabs"]:
                skip, creative_tab_bundler, creative_tab_files, translation_keys = (
                    handle_bundler(
                        {
                            "bundler": jp(
                                replace_files,
                                "creative_tabs/creative_tab_bundler.java",
                            ),
                            "import": jp(
                                replace_files, "creative_tabs/import_line.java"
                            ),
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
                            "properties": jp(
                                replace_files, "creative_tabs/properties.json"
                            ),
                        },
                        self,
                        actions["internal_creative_tabs"],
                        configurator,
                    )
                )
                if skip:
                    continue
                actions["language"].update(translation_keys)

                with open(jp(java_path, "ModCreativeModeTabs.java"), "w") as f:
                    f.write(creative_tab_bundler)
                self.things_added.append("creative_mode_tabs")

                for file, code in creative_tab_files.items():
                    write_to_file(jp(java_path, f"creative_tabs/{file}.java"), code)

                del creative_tab_bundler, creative_tab_files, translation_keys

            log(DEBUG, "Generating Content - Procedures")
            ### Procedures

            if actions["procedures"] != {}:
                event_wrapper_location = jp(
                    replace_files, "procedures/event_handler.java"
                )
                if not os.path.exists(event_wrapper_location):
                    log(
                        ERROR,
                        "Unable to find event wrapper at '%s', %s"
                        % (event_wrapper_location, skip_message),
                    )
                    continue
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
                            % (self.mod_loader, self.minecraft_version),  # Improve this
                            procedure.event,
                        )
                        total_code += "\n" + code
                        total_imports.extend(imports)
                        total_contexts.update(contexts)
                    else:
                        log(
                            WARNING,
                            "Procedure %s has no event, %s" % (id, skip_message),
                        )

                total_imports = list(set(total_imports))
                event_wrapper = get_file_contents(event_wrapper_location)
                event_wrapper = format_text(
                    event_wrapper,
                    self,
                    {
                        "imports": "\n".join(["import %s;" % x for x in total_imports]),
                        "events": total_code,
                        "contexts": "\n".join(total_contexts.values()),
                    },
                )

                write_to_file(jp(java_path, "EventHandler.java"), event_wrapper)

                self.things_added.append("procedures")

            log(DEBUG, "Generating Content - Translation")
            ### Translations

            translation_path = jp(assets_path_self, "lang/en_us.json")
            os.makedirs(os.path.dirname(translation_path), exist_ok=True)
            with open(translation_path, "w") as f:
                json.dump(actions["language"], f, indent=4)

            log(DEBUG, "Generating Content - Block Models")

            ### Textures + Models
            class RquiredTexture(TypedDict):
                item: list[str]
                block: list[str]

            required_textures = RquiredTexture(
                item=[],
                block=[],
            )

            # Block models/blockstates
            block_model_path = jp(assets_path_self, "models/block")
            if not os.path.exists(block_model_path):
                os.makedirs(block_model_path)
            blockstate_model_path = jp(
                final_cache_path, "assets", self.id, "blockstates"
            )
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

            for block_id, block in actions["internal_blocks"].items():
                block_id: str
                block: Block

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

                with open(blockstate_path, "w") as f:
                    f.write(blockstate_data)
                all_models = get_all_models_in_blockstate(
                    get_file_contents(blockstate_path_for_this_block)
                )

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
                                f"Unable to find suitable model for block {self.id}, tried following paths: \n>{old}\n>{model_path}",
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
                        required_textures["block"].append(val.split("/")[-1])

                    model_name_path_extension = model.replace(
                        "{mod_id}:block/{block_id}",
                        "",
                    )
                    model_path = jp(
                        block_model_path, f"{block_id}{model_name_path_extension}.json"
                    )
                    with open(model_path, "w") as f:
                        f.write(model_data)

            log(DEBUG, "Generating Content - item Models")
            # Item models

            item_model_path = jp(assets_path_self, "models/item")

            for item_id, item in actions["internal_items"].items():
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
                                    log(FATAL, "Block item type is None for block item")

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
                                        log(FATAL, "Cannot get item model path :(")
                                    else:
                                        log(
                                            WARNING,
                                            "Unable to find item model for %s, using default cube instead"
                                            % item_id,
                                        )

                                item_model_data = replace(
                                    get_file_contents(
                                        model_path,
                                        info="Getting item model",
                                    ),
                                    combine_dicts(item.block_item_textures, {"mod_id": display_item_mod_id}),  # type: ignore
                                )
                                write_to_file(block_model_output_path, item_model_data)

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
                        required_textures["item"].append(item.texture)
                    case _:
                        log(FATAL, f"Unknown display type {display_type}")

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
                write_to_file(model_path, model_data)
                del model_data, model_path, item

            log(DEBUG, "Managing Content - Textures")

            for dir, textures in required_textures.items():
                textures = cast(list[str], textures)
                for texture in textures:
                    texture_path = jp(
                        template_cache_path, "assets", self.id, "textures", dir, texture
                    )
                    if not os.path.exists(jp(assets_path_self, "textures", dir)):
                        os.makedirs(jp(assets_path_self, "textures", dir))

                    if os.path.exists(jp(texture_path) + ".png"):
                        shutil.copyfile(
                            jp(texture_path) + ".png",
                            jp(assets_path_self, "textures", dir, texture + ".png"),
                        )
                        if os.path.exists(jp(texture_path) + ".png.mcmeta"):
                            shutil.copyfile(
                                jp(texture_path) + ".png.mcmeta",
                                jp(
                                    assets_path_self,
                                    "textures",
                                    dir,
                                    texture + ".png.mcmeta",
                                ),
                            )
                    else:
                        if texture.__contains__(":"):
                            log(
                                INFO,
                                f"Texture {texture} not found. It will be assumed it exists elsewhere undefined.",
                            )
                        else:
                            log(
                                WARNING,
                                f"Texture {texture} not found. ({jp(texture_path) + '.png'})",
                            )

            # loot_table_path = jp(data_path_self, "loot_tables")

            log(DEBUG, "Generating Content? - Loot Tables")

            for loot_table in actions["internal_loot_tables"]:
                loot_table: LootTable
                new_loot_table_path = jp(
                    data_path,
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

            log(DEBUG, "Generating Content? - Tags")

            for id, actual_tag in self.tags.items():
                for tag, value in actual_tag.items():
                    tag_path = jp(data_path, id, "tags", tag + ".json")
                    thing: dict[str, list[str] | bool] = {
                        "values": [
                            f"{self.id}:{x}" if not x.__contains__(":") else x
                            for x in value
                        ],
                        "replace": False,
                    }

                    write_to_file(tag_path, json.dumps(thing))

            log(DEBUG, "Generating Content - Recipes")

            for key, i in actions["recipes"].items():
                i: Recipe
                new_recipe_path = jp(
                    data_path,
                    self.id,
                    "recipes",
                    i.recipe_type,
                    f"{key}.json",
                )
                recipe = i.generate(self)
                write_to_file(new_recipe_path, recipe)

            ### EVERYTHING IS DONE -> COPY CACHE TO MDK

            log(DEBUG, "Done generating, copying to MDK")
            copy_start = time.time()

            log(DEBUG, "Cleaning MDK")
            shutil.rmtree(resource_path)

            log(DEBUG, "Copying cache content to MDK")
            # shutil.copytree(final_cache_path, resource_path)
            fast_copytree(final_cache_path, resource_path)

            log(DEBUG, "Dealing with replace/overwrite files (Defined by plugin)")
            # Deal with overwrites
            overwrite_file_path = jp(replace_files, "overwrite.json")
            if os.path.exists(overwrite_file_path):
                overwrite_data = json.loads(get_file_contents(overwrite_file_path))
                for action, overwrites in overwrite_data.items():
                    if action == "java_path":
                        action_path = java_path
                    elif action == "surface":
                        action_path = path
                    elif action == "resources":
                        action_path = resource_path
                    else:
                        log(
                            FATAL,
                            f"Unknown action path '{action}' in {overwrite_file_path}",
                        )
                    for overwrite in overwrites:
                        file = jp(replace_files, overwrite["file"])
                        if not os.path.exists(file):
                            log(FATAL, f"Overwrite file {file} does not exist")
                        offset = overwrite["offset"]
                        file_contents = get_file_contents(file)
                        rename = overwrite.get("rename")

                        if overwrite["format"]:
                            file_contents = format_text(file_contents, self)

                        write_file_path = jp(
                            action_path,
                            offset,
                            (
                                format_text(rename, self)
                                if rename
                                else os.path.basename(file)
                            ),
                        )
                        write_to_file(write_file_path, file_contents)

            log(DEBUG, "Writing server file (Entry point) to MDK")

            server_file_path = jp(replace_files, "server.java")

            if not os.path.exists(server_file_path):
                log(
                    ERROR,
                    f"Server file at {server_file_path} does not exist, {skip_message}",
                )
                continue

            server_import_file_path = jp(replace_files, "settings.json")
            if not os.path.exists(server_import_file_path):
                log(
                    ERROR,
                    f"Server config file at {server_import_file_path} does not exist, {skip_message}",
                )
                continue

            server_file = get_file_contents(server_file_path)
            server_import_file = json.loads(get_file_contents(server_import_file_path))
            # client_file = get_file_contents(client_file_path)
            pre_imports: list[str] = []
            pre_setups: list[str] = []
            # settings.json, you'll figure it out
            # Alright past me, I did because of your snazzy comment. Still hate you though
            for x in self.things_added:
                pre_imports.append(server_import_file[x]["import"])
                pre_setups.append(server_import_file[x]["setup"])

            imports = format_text("\n".join(pre_imports), self)
            setups = format_text("\n".join(pre_setups), self)

            server_file = format_text(
                server_file, self, {"imports": imports, "setups": setups}
            )
            # client_file = format_text(client_file, self)

            write_to_file(jp(java_path, f"{self.id.title()}.java"), server_file)
            # write_to_file(jp(java_path, f"ClientEvents.java"), client_file)

            del server_file

            end = time.time()
            entire = end - start
            copying = end - copy_start
            log(
                INFO,
                [
                    f"Finished in {entire} seconds:",
                    f"> {entire-copying}s generating/managing content",
                    f"> {copying}s Copying generated/managed content to mdk",
                ],
            )


def format_text(text: str, mod: Mod, additional_replace: dict[str, str] = {}) -> str:
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
                    "minecraft_version": mod.minecraft_version,
                    "mod_loader_version": mod.mod_loader_version,
                },
                mod.info_replace,
            ),
            additional_replace,
        ),
    )


def get_all_models_in_blockstate(blockstate: str):
    return re.findall('"model": "(.*?)"', blockstate)


from . import presets

__all__ = [
    "Mod",
    "presets",
]

from typing import (
    Optional,
    Any,
    Callable,
)
from . import TRANSLATIONS

from fast_functions import get_file_contents, write_to_file

# import csv # Later.
import json
import os
from collections.abc import Mapping
from collections import OrderedDict
from .properties_helper import get_properties
from .internal_shared import combine_dicts

from .components import (
    COMPONENT_TYPE,
    Block,
    Item,
    CreativeTab,
    LootTable,
    TagManager,
)
from .internal_shared import (
    jp,
    replace,
    java_minifier,
)
from .one_off_functions import (
    performance_handler,
    decimal_to_rgb,
    snake_to_camel,
)
from shared import (
    log,
    FATAL,
    # ERROR,
    # WARN,
    # INFO,
)
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .mod_class import Mod, ModInfo

from .mod_helper import format_text, get_closest_map_color


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
        colors: OrderedDict[str, tuple[int, int, int]] = OrderedDict()
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
                TRANSLATIONS[naming],
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
            component = cast(Block, component)
            if not component.blocktype == "cube":
                imports += "\nimport net.minecraft.world.level.block.%sBlock;" % (
                    component.blocktype.replace("_", " ").title()
                ).replace(" ", "")

        file_name = snake_to_camel(component_id) + snake_to_camel(naming)

        replace_info = combine_dicts(
            {
                "internal_mod_id": mod.internal_id,
                "mod_id": mod.id,
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
            TRANSLATIONS[naming],
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

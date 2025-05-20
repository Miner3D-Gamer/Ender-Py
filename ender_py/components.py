from typing import Optional, TypeAlias, Union, Literal, NoReturn, Any, Tuple, List
from .one_off_functions import generate_texture
from .shared import export_class, get_file_contents, log, FATAL, ERROR, WARNING, INFO
import os, json


class VoxelShape:
    def __init__(self, min_x, min_y, min_z, max_x, max_y, max_z) -> None:
        self.min_x = min_x
        self.min_y = min_y
        self.min_z = min_z
        self.max_x = max_x
        self.max_y = max_y
        self.max_z = max_z

        self.TYPE = "voxel_shape"

    def __repr__(self) -> str:
        return f"box({self.min_x}, {self.min_y}, {self.min_z}, {self.max_x}, {self.max_y}, {self.max_z})"

    def __json__(self):
        return export_class(self)


class RecipeItem:
    def __init__(
        self, name: str, count: int = 1, components: Optional[dict[str, str]] = None
    ) -> None:
        self.name = name
        self.count = count
        self.components = components
        self.TYPE = "recipe_item"


class Recipe:
    def __init__(
        self,
        *,
        result: str,
        result_count: int = 1,
    ) -> None:
        self.result = result
        self.result_count = result_count

        self.TYPE = "recipe"


class RecipeCrafting(Recipe):
    def __init__(
        self,
        *,
        result: str,
        result_count: int = 1,
        shape: Optional[str] = None,
        ingredients: Optional[dict[str, Union[str, list[str]]] | list[str]] = None,
        condition=None,
    ) -> None:
        super().__init__(result=result, result_count=result_count)

        self.shape = shape
        self.ingredients = ingredients
        self.TYPE = "recipe_crafting"


class Item:
    __slots__ = [
        "name",
        "texture",
        "stack_size",
        "durability",
        "unrepairable",
        "fire_resistant",
        "TYPE",
        "is_block_item",
        "remains_after_crafting",
        "rarity",
        "enchantability",
        "block_break_speed",
        "can_break_any_block",
        "item_animation",
        "is_meat",
        "nutrition",
        "saturation",
        "fast_consumed",
        "always_edible",
        "block_item_type",
        "display_item",
        "block_item_textures",
    ]

    def __init__(
        self,
        *,
        name: str,
        texture: str,
        stack_size: int = 64,
        durability: Optional[int] = None,
        unrepairable: bool = False,
        fire_resistant: bool = False,
        is_block_item: bool = False,
        block_item_type: Optional[str] = None,
        remains_after_crafting: bool = False,
        rarity: str = "common",
        enchantability: int = 0,
        block_break_speed: Optional[float] = None,
        can_break_any_block: bool = False,
        item_animation: Optional[
            Literal["eat", "shield_blocking", "bow", "crossbow", "drink", "spear"]
        ] = None,
        is_meat: bool = False,
        nutrition: int = 0,
        saturation: int = 0,
        fast_consumed: bool = False,
        always_edible: bool = False,
        display_item: str = "item",
        block_item_textures: Optional[dict[str, str]] = None,
    ) -> None:
        self.name = name
        self.texture = texture
        self.stack_size = stack_size
        self.durability = durability
        self.unrepairable = unrepairable
        self.fire_resistant = fire_resistant
        self.TYPE = "item"
        self.block_item_textures = block_item_textures
        self.block_item_type = block_item_type
        self.is_block_item = is_block_item
        self.remains_after_crafting = remains_after_crafting
        self.rarity = rarity
        self.enchantability = enchantability
        self.block_break_speed = block_break_speed
        self.can_break_any_block = can_break_any_block
        self.item_animation = item_animation
        self.is_meat = is_meat
        self.nutrition = nutrition
        self.saturation = saturation
        self.fast_consumed = fast_consumed
        self.always_edible = always_edible
        self.display_item = display_item


class CreativeTab:
    __slots__ = [
        "name",
        "icon_item",
        "items",
        "hide_title",
        "no_scrollbar",
        "alignment_right",
        "TYPE",
        "search_bar",
    ]

    def __init__(
        self,
        *,
        name: str,
        icon_item: str,
        items: list[str] | dict[str, Any],
        hide_title: bool = False,
        no_scrollbar: bool = False,
        alignment_right: bool = True,
    ) -> None:
        self.name = name
        self.icon_item = icon_item

        self.search_bar = True  # Else it crashes ¯\_(ツ)_/¯
        self.hide_title = hide_title
        self.no_scrollbar = no_scrollbar
        self.alignment_right = alignment_right
        self.items = [x for x in items]
        self.TYPE = "creative_tab"


ROTATION: TypeAlias = Literal[
    "none", "log", "blockface", "y_blockface", "playerside", "y_playerside"
]

# strip_wood_procedure = get_file_contents(
#     os.path.join(os.path.dirname(__file__), "default_procedures", "strip_wood.json")
# )


class Block:
    __slots__ = [
        "name",
        "texture",
        "item",
        "TYPE",
        "stack_size",
        "blocktype",
        "hardness",
        "resistance",
        "friction",
        "speed_factor",
        "luminance",
        "no_collision",
        "emmisive_texture",
        "requires_correct_tool_for_drops",
        "random_model_offset",
        "has_transparency",
        "sounds",
        "bounding_box",
        "opacity",
        "is_replaceable",
        "can_sustain_plants",
        "is_climbable",
        "flammability",
        "fire_spread_speed",
        "breakable_with",
        "connect_to_redstone",
        "emmit_redstone_signal",
        "push_reaction",
        "connected_sides",
        "hide_fluid_when_submerged",
        "catches_fire_from_lava",
        "display_item",
        "loot_table",
        "rotation",
        "map_color",
        "block_material_type",
        "button_ticks_pressed",
        "button_pressed_by_arrow",
        "pressure_plate_activation",
        "procedures",
    ]

    def __init__(
        self,
        *,
        name: str,
        texture: (
            str
            | dict[
                Literal[
                    "top",
                    "bottom",
                    "north",
                    "south",
                    "west",
                    "east",
                    "particle",
                    "side",
                    "render_type",
                ],
                str,
            ]
        ),
        hardness: float,
        resistance: float,
        rotation: Optional[ROTATION] = None,
        friction: float = 0.6,
        speed_factor: float = 1,
        luminance: int = 0,
        no_collision: bool = False,
        emmisive_texture: bool = False,
        requires_correct_tool_for_drops: bool = False,
        random_model_offset: Optional[Literal["XZ", "XYZ"]] = None,
        has_transparency: bool = False,
        sounds: str = "stone",
        bounding_box: list["VoxelShape"] = [VoxelShape(0, 0, 0, 16, 16, 16)],
        opacity: Optional[int] = None,
        is_replaceable: bool = False,
        can_sustain_plants: bool = False,
        is_climbable: bool = False,
        flammability: int = 0,
        breakable_with: Optional[
            list[Literal["axe", "pickaxe", "shovel", "hoe"]]
        ] = None,
        fire_spread_speed: int = 0,
        connect_to_redstone: bool = False,
        emmit_redstone_signal: int = 0,
        connected_sides: bool = False,
        hide_fluid_when_submerged: bool = False,
        push_reaction: Optional[
            Literal["destroy", "block", "push_only", "ignore", "normal"]
        ] = None,
        blocktype: Literal[
            "cube",
            "slab",
            "stair",
            "fence",
            "wall",
            "pressure_plate",
            "fence_gate",
            "button",
            "trap_door",
            "door",
            "leaves",
            "falling",
        ] = "cube",
        item: Union["Item", None],
        catches_fire_from_lava: bool = False,
        display_item: str = "block",
        loot_table: Optional[str] = None,
        map_color: Optional[str] = None,
        block_material_type: Optional[str] = "oak",
        button_ticks_pressed: int = 20,
        button_pressed_by_arrow: bool = True,
        pressure_plate_activation: Literal["all", "mobs"] = "all",
        procedures: Optional[list] = None,
    ) -> None:
        """
        Name: Title of the block
        Texture Name: Name of the texture file (.png)
        Description: Tooltip description of the block
        Item: Associated item, insert None to generate a generic block-item for it
        """
        self.name = name
        self.texture = generate_texture(texture, name)
        self.item = item
        self.TYPE = "block"
        self.blocktype = blocktype
        if item is None:
            self.stack_size = 64
        else:
            self.stack_size = item.stack_size

        self.hardness = hardness
        self.catches_fire_from_lava = catches_fire_from_lava
        self.resistance = resistance
        self.friction = friction
        self.display_item = display_item
        self.speed_factor = speed_factor
        self.luminance = luminance
        self.no_collision = no_collision
        self.emmisive_texture = emmisive_texture
        self.requires_correct_tool_for_drops = requires_correct_tool_for_drops
        self.random_model_offset = random_model_offset
        self.has_transparency = has_transparency
        self.sounds = sounds
        self.bounding_box = bounding_box
        self.opacity = opacity
        self.is_replaceable = is_replaceable
        self.can_sustain_plants = can_sustain_plants
        self.is_climbable = is_climbable
        self.flammability = flammability
        self.fire_spread_speed = fire_spread_speed
        self.connect_to_redstone = connect_to_redstone
        self.emmit_redstone_signal = emmit_redstone_signal
        self.connected_sides = connected_sides
        self.hide_fluid_when_submerged = hide_fluid_when_submerged
        self.push_reaction = push_reaction
        self.breakable_with = breakable_with
        self.rotation = rotation if rotation is not None else "none"
        self.loot_table = loot_table
        self.map_color = map_color
        self.block_material_type = block_material_type
        self.button_ticks_pressed = button_ticks_pressed
        self.button_pressed_by_arrow = button_pressed_by_arrow
        self.pressure_plate_activation = pressure_plate_activation
        self.procedures = procedures


class Tag:
    __slots__ = ["name", "replace", "content", "context", "TYPE"]

    def __init__(self, name: str, replace: bool, content: list[str], context: str):
        self.name = name
        self.replace = replace
        self.content = content
        self.context = context

        self.TYPE = "tag"


class LootTable:
    __slots__ = ["name", "entries", "context", "TYPE", "mod_id"]

    def __init__(self, name: str, content: Union[str, dict], context: str, mod_id: str):
        self.name = name
        self.entries = content
        self.context = context
        self.mod_id = mod_id
        # context: location
        self.TYPE = "loot_table"


class Procedure:
    __slots__ = ["event", "content", "TYPE"]

    def __init__(self, event, content: str | list):
        new: list
        self.event = event
        if isinstance(content, str):
            if os.path.exists(content) and os.path.isfile(content):
                new = json.loads(get_file_contents(content))
            else:
                b = content
                try:
                    new = json.loads(content)
                except:
                    log(
                        FATAL,
                        f"Failed to parse {content} as json, check if it is valid json",
                    )
        else:
            new = content
        self.content: list = new
        self.TYPE = "procedure"


COMPONENT_TYPE: TypeAlias = Item | CreativeTab | Block | Tag | LootTable | Procedure

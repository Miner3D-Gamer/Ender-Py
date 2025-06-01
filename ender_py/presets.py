from .components import (
    Block,
    COMPONENT_TYPE,
    RecipeCrafting,
    ALLOWED_BLOCK_TYPES,
    ROTATION,
)
from .one_off_functions import camel_to_snake
from .internal_shared import texture_type
from typing import TypedDict, Optional, TypeVar


def brick_set(
    name: str,
    textures: "texture_type",
    hardness: float,
    resistance: float,
    cut_last_letter: bool = True,
    block: bool = True,
    stairs: bool = True,
    slab: bool = True,
    wall: bool = True,
) -> dict[str, COMPONENT_TYPE]:
    components: dict[str, COMPONENT_TYPE] = {}
    id = camel_to_snake(name.replace(" ", ""))
    original_id = id
    if block:
        components[id] = Block(
            name=name,
            texture=textures,
            hardness=hardness,
            resistance=resistance,
            item=None,
        )
    if cut_last_letter:
        id = id[:-1]
        name = name[:-1]

    if stairs:
        stair_id = id + "_stairs"
        components[stair_id] = Block(
            name=name + " Stairs",
            texture=textures,
            hardness=hardness,
            resistance=resistance,
            item=None,
            blocktype="stair",
        )
        components[stair_id + "_recipe"] = RecipeCrafting(
            result=stair_id,
            ingredients=[
                [original_id, None, None],
                [original_id, original_id, None],
                [original_id, original_id, original_id],
            ],
            result_count=4,
            category="building",
        )
    if slab:
        slab_id = id + "_slab"
        components[slab_id] = Block(
            name=name + " Slab",
            texture=textures,
            hardness=hardness,
            resistance=resistance,
            item=None,
            blocktype="slab",
        )
        components[slab_id + "_recipe"] = RecipeCrafting(
            result=slab_id,
            ingredients=[
                [None, None, None],
                [original_id, original_id, original_id],
                [None, None, None],
            ],
            result_count=6,
            category="building",
        )
    if wall:
        wall_id = id + "_wall"
        components[wall_id] = Block(
            name=name + " Wall",
            texture=textures,
            hardness=hardness,
            resistance=resistance,
            item=None,
            blocktype="wall",
        )
        components[wall_id + "_recipe"] = RecipeCrafting(
            result=wall_id,
            ingredients=[
                [None, None, None],
                [original_id, original_id, original_id],
                [original_id, original_id, original_id],
            ],
            result_count=6,
            category="building",
        )

    return components


T = TypeVar("T")


class WoodSetTextures(TypedDict):
    log_side: str | None
    log_end: str | None
    stripped_log_side: str | None
    stripped_log_end: str | None
    planks: str | None
    leaves: str | None
    door_top: str | None
    door_bottom: str | None
    door_item: str | None
    trapdoor: str | None
    render_types: dict[str, str]


def wood_set(
    name: str,
    textures: WoodSetTextures,
    hardness: float,
    resistance: float,
    flammability: int,
    names: Optional[dict[str, str]] = None,
) -> dict[str, COMPONENT_TYPE]:
    components: dict[str, COMPONENT_TYPE] = {}
    default = {
        "log": "%s Log",
        "stripped_log": "Stripped %s Log",
        "wood": "%s Wood",
        "stripped_wood": "Stripped %s Wood",
        "planks": "%s Planks",
        "leaves": "%s Leaves",
        "stairs": "%s Stairs",
        "slab": "%s Slab",
        "fence": "%s Fence",
        "fence_gate": "%s Fence Gate",
        "door": "%s Door",
        "trapdoor": "%s Trapdoor",
        "pressure_plate": "%s Pressure Plate",
        "button": "%s Button",
    }
    naming = default
    if isinstance(names, dict):
        naming.update(names)

    def helper(required_textures: list[str], helper_name: str):

        if all([textures.get(x) for x in required_textures]) and naming.get(
            helper_name
        ):
            create_block = True
        else:
            create_block = False
        if create_block:
            block_name = default[helper_name] % name
            block_id = camel_to_snake(block_name)
        else:
            block_name = ""
            block_id = default[helper_name] % name

        return create_block, block_name, block_id

    def texture_get(t: str) -> str:
        return textures.get(t) or t

    def create_block(
        texture: dict[str, str],
        name: str,
        block_type: ALLOWED_BLOCK_TYPES,
        default_render_type: str = "solid",
        rotation: Optional[ROTATION] = None,
        display_item: Optional[str] = None,
    ):

        create_block, block_name, block_id = helper([x for x in texture.values()], name)
        new: dict[str, str] = {}
        for key, item in texture.items():
            new[key] = texture_get(item)
        new.update(
            {
                "render_type": textures.get("render_types", {}).get(name)
                or default_render_type
            }
        )

        if create_block:
            components[block_id] = Block(
                name=block_name,
                texture=new,
                hardness=hardness,
                resistance=resistance,
                item=None,
                flammability=flammability,
                catches_fire_from_lava=flammability != 0,
                has_transparency=new["render_type"] != "solid",
                rotation=rotation,
                display_item=display_item,
                blocktype=block_type,
            )

    create_block(
        texture={
            "side": "log_side",
            "bottom": "log_end",
        },
        name="log",
        block_type="cube",
        default_render_type="solid",
        rotation="log",
    )
    create_block(
        texture={
            "side": "stripped_log_side",
            "bottom": "stripped_log_end",
        },
        name="stripped_log",
        block_type="cube",
        default_render_type="solid",
        rotation="log",
    )
    create_block(
        texture={
            "bottom": "planks",
        },
        name="planks",
        block_type="cube",
        default_render_type="solid",
        rotation=None,
    )
    create_block(
        texture={
            "bottom": "planks",
        },
        name="stairs",
        block_type="stair",
        default_render_type="solid",
        rotation=None,
    )
    create_block(
        texture={
            "bottom": "planks",
        },
        name="slab",
        block_type="slab",
        default_render_type="solid",
        rotation=None,
    )
    create_block(
        texture={
            "bottom": "planks",
        },
        name="fence",
        block_type="fence",
        default_render_type="solid",
        rotation=None,
    )
    create_block(
        texture={
            "bottom": "planks",
        },
        name="fence_gate",
        block_type="fence_gate",
        default_render_type="solid",
        rotation=None,
    )
    create_block(
        texture={
            "bottom": "planks",
        },
        name="pressure_plate",
        block_type="pressure_plate",
        default_render_type="solid",
        rotation=None,
    )
    create_block(
        texture={
            "bottom": "planks",
        },
        name="button",
        block_type="button",
        default_render_type="solid",
        rotation=None,
    )
    create_block(
        texture={
            "bottom": "leaves",
        },
        name="leaves",
        block_type="leaves",
        default_render_type="cutout_mipped",
        rotation=None,
    )
    create_block(
        texture={
            "bottom": "door_bottom",
            "top": "door_top",
        },
        name="door",
        block_type="door",
        default_render_type="cutout_mipped",
        rotation=None,
        display_item=(
            "item;" + textures["door_item"] if textures["door_item"] else None
        ),
    )
    create_block(
        texture={
            "bottom": "trapdoor",
        },
        name="trapdoor",
        block_type="trap_door",
        default_render_type="cutout_mipped",
        rotation=None,
        display_item=None,
    )

    return components

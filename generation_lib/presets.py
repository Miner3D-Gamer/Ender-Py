from .components import Block, Item, CreativeTab, COMPONENT_TYPE
from typing import Any






def wood_set(
    name: str,
    textures: dict[str, Any],
    hardness: float,
    resistance: float,
    flammability: int,
) -> dict[str, COMPONENT_TYPE]:
    components: dict[str, COMPONENT_TYPE] = {}
    components[name + "_log"] = Block(
        name=name.title() + " Log",
        texture={
            "side": textures["log_side"],
            "top": textures["log_end"],
            "bottom": textures["log_end"],
            "render_type": textures.get("render_types", {}).get("log", "solid"),
        },
        hardness=hardness,
        resistance=resistance,
        item=None,
        flammability=flammability,
        catches_fire_from_lava=flammability != 0,
        has_transparency=textures.get("render_types", {}).get("log", "solid")
        != "solid",
        rotation="log",
    )
    components["stripped_"+name + "_log"] = Block(
        name=name.title() + " Log",
        texture={
            "side": textures["log_side_stripped"],
            "top": textures["log_end_stripped"],
            "bottom": textures["log_end_stripped"],
            "render_type": textures.get("render_types", {}).get("log", "solid"),
        },
        hardness=hardness,
        resistance=resistance,
        item=None,
        flammability=flammability,
        catches_fire_from_lava=flammability != 0,
        has_transparency=textures.get("render_types", {}).get("log", "solid")
        != "solid",
        rotation="log",
    )
    components[name + "_planks"] = Block(
        name=name.title() + " Planks",
        texture={
            "bottom": textures["planks"],
            "render_type": textures.get("render_types", {}).get("planks", "solid"),
        },
        hardness=hardness,
        resistance=resistance * 1.5,
        item=None,
        catches_fire_from_lava=flammability != 0,
        has_transparency=textures.get("render_types", {}).get("planks", "solid")
        != "solid",
    )
    components[name + "_leaves"] = Block(
        name=name.title() + " Leaves",
        texture={
            "bottom": textures["leaves"],
            "render_type": textures.get("render_types", {}).get(
                "leaves", "cutout_mipped"
            ),
        },
        hardness=0.2,
        resistance=0.2,
        item=None,
        catches_fire_from_lava=flammability != 0,
        blocktype="leaves",
        has_transparency=textures.get("render_types", {}).get("leaves", "cutout_mipped")
        != "solid",
        opacity=0,
        requires_correct_tool_for_drops=True,
    )
    components[name + "_stairs"] = Block(
        name=name.title() + " Stairs",
        texture={
            "bottom": textures["planks"],
            "render_type": textures.get("render_types", {}).get("stairs", "solid"),
        },
        hardness=hardness,
        resistance=resistance * 1.5,
        item=None,
        catches_fire_from_lava=flammability != 0,
        blocktype="stair",
        has_transparency=textures.get("render_types", {}).get("stairs", "solid")
        != "solid",
    )
    components[name + "_slab"] = Block(
        name=name.title() + " Slab",
        texture={
            "bottom": textures["planks"],
            "render_type": textures.get("render_types", {}).get("slab", "solid"),
        },
        hardness=hardness,
        resistance=resistance * 1.5,
        item=None,
        catches_fire_from_lava=flammability != 0,
        blocktype="slab",
        has_transparency=textures.get("render_types", {}).get("slab", "solid")
        != "solid",
    )
    components[name + "_fence"] = Block(
        name=name.title() + " Fence",
        texture={
            "bottom": textures["planks"],
            "render_type": textures.get("render_types", {}).get("fence", "solid"),
        },
        hardness=hardness,
        resistance=resistance * 1.5,
        item=None,
        catches_fire_from_lava=flammability != 0,
        blocktype="fence",
        has_transparency=textures.get("render_types", {}).get("fence", "solid")
        != "solid",
        opacity=0,
    )
    components[name + "_fence_gate"] = Block(
        name=name.title() + " Fence Gate",
        texture={
            "bottom": textures["planks"],
            "render_type": textures.get("render_types", {}).get("fence_gate", "solid"),
        },
        hardness=hardness,
        resistance=resistance * 1.5,
        item=None,
        catches_fire_from_lava=flammability != 0,
        blocktype="fence_gate",
        has_transparency=textures.get("render_types", {}).get("fence_gate", "solid")
        != "solid",
        opacity=0,
    )
    components[name + "_door"] = Block(
        name=name.title() + " Door",
        texture={
            "top": textures["door_top"],
            "bottom": textures["door_bottom"],
            "render_type": textures.get("render_types", {}).get(
                "door", "cutout_mipped"
            ),
        },
        hardness=hardness,
        resistance=resistance * 1.5,
        item=None,
        catches_fire_from_lava=flammability != 0,
        blocktype="door",
        display_item="item;" + textures["door_item"],
        has_transparency=textures.get("render_types", {}).get("door", "cutout_mipped")
        != "solid",
        opacity=0,
    )
    components[name + "_pressure_plate"] = Block(
        name=name.title() + " Pressure Plate",
        texture={
            "bottom": textures["planks"],
            "render_type": textures.get("render_types", {}).get(
                "pressure_plate", "solid"
            ),
        },
        hardness=hardness,
        resistance=resistance * 1.5,
        item=None,
        catches_fire_from_lava=flammability != 0,
        blocktype="pressure_plate",
        has_transparency=textures.get("render_types", {}).get("pressure_plate", "solid")
        != "solid",
        opacity=0,
    )
    components[name + "_trapdoor"] = Block(
        name=name.title() + " Trapdoor",
        texture={
            "bottom": textures["trapdoor"],
            "render_type": textures.get("render_types", {}).get(
                "trapdoor", "cutout_mipped"
            ),
        },
        hardness=hardness,
        resistance=resistance * 1.5,
        item=None,
        catches_fire_from_lava=flammability != 0,
        blocktype="trap_door",
        has_transparency=textures.get("render_types", {}).get(
            "trapdoor", "cutout_mipped"
        )
        != "solid",
        opacity=0,
    )
    components[name + "_button"] = Block(
        name=name.title() + " Button",
        texture={
            "bottom": textures["planks"],
            "render_type": textures.get("render_types", {}).get("button", "solid"),
        },
        hardness=hardness,
        resistance=resistance * 1.5,
        item=None,
        catches_fire_from_lava=flammability != 0,
        blocktype="button",
        has_transparency=textures.get("render_types", {}).get("button", "solid")
        != "solid",
    )

    return components

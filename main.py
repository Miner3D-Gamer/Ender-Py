import generation_lib
import json

bobstruction = generation_lib.Mod(
    internal_id="com.miner.bobstruction",
    public_id="bobstruction",
    name="Bobstruction",
    author="Miner3D",
    description="Description",
    version="1.0.0",
    license="All Rights Reserved",
    mdk_folder=r"..\mods\all",
    external_packs=["./external_resources"],
)

set = generation_lib.presets.wood_set(
    name="test",
    textures={
        "log_side": "test_log_side",
        "log_end": "test_log_end",
        "log_side_stripped": "test_log_side_stripped",
        "log_end_stripped": "test_log_end_stripped",
        "planks": "test_planks",
        "leaves": "test_leaves",
        "trapdoor": "test_trapdoor",
        "door_bottom": "test_door_bottom",
        "door_top": "test_door_top",
        "door_item": "test_door",
    },
    hardness=5,
    resistance=10,
    flammability=1,
)

bobstruction.add_components(set)
bobstruction.add_component(
    component=generation_lib.components.CreativeTab(
        name="Custom Tab", icon_item="minecraft:diamond", items=set
    ),
    id="creat",
)

pro_str = generation_lib.shared.get_file_contents("generation_lib/strip_wood.json")
bobstruction.add_component(
    component=generation_lib.components.Procedure(
        event="block_right_click",
        content=pro_str,
    ),
    id="strip_wood",
)


bobstruction.generate()

# out = generation_lib.export_mod(bobstruction)
# with open("mod1.json", "w") as f:
#     json.dump(out, f, indent=4, default=generation_lib.shared.dynamic_serializer)
# some = generation_lib.import_mod(out, "../mods/all")
# out = generation_lib.export_mod(some)
# with open("mod2.json", "w") as f:
#     json.dump(out, f, indent=4, default=generation_lib.shared.dynamic_serializer)


# bobstruction.add_component(
#     id="bobstruction",
#     component=generation_lib.CreativeTab(
#         name="Bobstruction",
#         icon_item="minecraft:diamond",
#         items=list(set),
#         hide_title=False,
#         no_scrollbar=False,
#         alignment_right=False,
#     ),
# )


# bobstruction.add_component(
#     id="test_item_i_believe", component=generation_lib.Item(name="Test Item", texture="sapphire")
# )
# print(str(bobstruction.export()))
# import json
# with open("mod2.json", "w") as f:
#     json.dump(generation_lib.export_mod(bobstruction), f, indent=4)
# print(generation_lib.import_mod(generation_lib.export_mod(bobstruction), "../mods/forge"))

import ender_py

mod = ender_py.Mod(
    internal_id="com.author.example_mod",
    public_id="some_mod",
    name="Example",
    author="Me",
    description="Description",
    version="1.0.0",
    license="All Rights Reserved",
    mdk_parent_folder=r"..\mods\all",
    external_packs=["./external_resources"],
)

block_set = ender_py.presets.wood_set(
    name="Test",
    textures=ender_py.presets.WoodSetTextures(
        log_end="test_log_end",
        log_side="test_log_side",
        stripped_log_side="test_log_side_stripped",
        stripped_log_end="test_log_end_stripped",
        planks="test_planks",
        leaves="test_leaves",
        trapdoor="test_trapdoor",
        door_bottom="test_door_bottom",
        door_top="test_door_top",
        door_item="test_door",
        render_types={},
    ),
    hardness=5,
    resistance=10,
    flammability=1,
)

mod.add_components(block_set)
mod.add_component(
    component=ender_py.components.CreativeTab(
        name="Custom Tab", icon_item="minecraft:diamond", items=block_set
    ),
    id="creative_tab",
)

procedure = ender_py.get_file_contents("ender_py/default_procedures/strip_log.json")
procedure = procedure.replace("{log}", ender_py.add_mod_id_if_missing("test_log", mod))
procedure = procedure.replace(
    "{stripped_log}", ender_py.add_mod_id_if_missing("stripped_test_log", mod)
)
mod.add_component(
    component=ender_py.components.Procedure(
        event="block_right_click",
        content=procedure,
    ),
    id="strip_wood",
)


mod.generate(minify=False)

# out = ender_py.export_mod(bobstruction)
# with open("mod1.json", "w") as f:
#     json.dump(out, f, indent=4, default=ender_py.shared.dynamic_serializer)
# some = ender_py.import_mod(out, "../mods/all")
# out = ender_py.export_mod(some)
# with open("mod2.json", "w") as f:
#     json.dump(out, f, indent=4, default=ender_py.shared.dynamic_serializer)


# bobstruction.add_component(
#     id="bobstruction",
#     component=ender_py.CreativeTab(
#         name="Bobstruction",
#         icon_item="minecraft:diamond",
#         items=list(set),
#         hide_title=False,
#         no_scrollbar=False,
#         alignment_right=False,
#     ),
# )


# bobstruction.add_component(
#     id="test_item_i_believe", component=ender_py.Item(name="Test Item", texture="sapphire")
# )
# print(str(bobstruction.export()))
# import json
# with open("mod2.json", "w") as f:
#     json.dump(ender_py.export_mod(bobstruction), f, indent=4)
# print(ender_py.import_mod(ender_py.export_mod(bobstruction), "../mods/forge"))

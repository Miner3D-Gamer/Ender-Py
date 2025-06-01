import ender_py

# Create new mod instance
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

# Use a template to quickly generate some blocks
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

# Actuall add the blocks to the mod
mod.add_components(block_set)

# Add a creative tab to hold the blocks
mod.add_component(
    component=ender_py.components.CreativeTab(
        name="Custom Tab", icon_item="minecraft:diamond", items=block_set
    ),
    id="creative_tab",
)

# Load a default procedure
procedure = ender_py.fast_functions.get_file_contents(
    "ender_py/default_procedures/strip_log.json"
)

# Replace placeholders
procedure = procedure.replace("{log}", ender_py.add_mod_id_if_missing("test_log", mod))
procedure = procedure.replace(
    "{stripped_log}", ender_py.add_mod_id_if_missing("stripped_test_log", mod)
)

# Add the procedure under the Block Right Click event
mod.add_component(
    component=ender_py.components.Procedure(
        event="block_right_click",
        content=procedure,
    ),
    id="strip_wood",
)

# Convert the mod to a string (json)
file_name = "mod.json"
with open(file_name, "w", encoding="utf-8") as f:
    f.write(mod.export(indent=4, include_external_packs=True))

# Import the mod by inputting the file path, file content, or unseralized json
new_mod = ender_py.Mod.import_mod(file_name, mod.mdk_paths)

# Use the added components to generate the mod(s)
new_mod.generate()

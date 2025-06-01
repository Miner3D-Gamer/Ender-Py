# A little project that strives to convert python-to-minecraft

Library in the 'ender_py' folder

Installation/Usage guide:

- Copy repository to local disk
- Install any currently supported mdk and make sure you can run it at least once
- Edit main.py to point to the parent directory of the unpackaged mdk
- Run main.py to test if generation works fine
- Make your own creation

### Development is halted until my other project, 'Procedure Crafter', is working. This side project can generate code in a visual workspace and is crucial for creating custom java code

## But what version of Minecraft?

- Any version
- Any mod loader

## How does it work?

- It receives the concept of what you want to make and generates code based on a plugin system for the specified versions

## What is Currently supported by default:

### Loaders:

- Forge 1.20.1

### Features:

- Creative Tabs
- Blocks (All types, missing custom hitbox)
- Items (Including food)
- Procedures (Partially, json -> java)
- Loot tables (Loading only)
- Recipes (All but smithing and brewing)

### To be added:

(Unsorted)

- Proper loot table support
- Procedure support (visual -> json -> java) -> Events
- Signs
- Mobs
- Boats
- Particles
- Effects
- Blockstates (Data components) -> Inventory
- UI/GUI -> Block/Item/Creature bound ⤴
- Block entities
- Hud -> Screen (Unbound)
- Throwables/Projectiles
- Ore generation
- Custom trees
- Biomes
- Dimension
- Music disk
- Villager types
- Villager trades
- Flower pot
- Armor
- Crops
- Tooltips
- Fuel modifier for items
- Horse Armor
- Armor trims
- Paintings
- Sitable blocks
- Keybinds
- Structures
- Fluids
- Energy Handling (in container)
- Fluid Handling (Millibuckets in container)
- Tags
- Advancements
- Game rules
- Enchantments
- Damage types
- Commands
- Config (File/UI, Cloth?)
- Support for popular mods
- Support for custom colors
- Multiblocks

### Mods to be supported by default:

- Create
- Serene Seasons
- Curious API
- JEI/REI/EMI
- Jade/Waila
- Farmer's Delight
- GeckoLib
- Tinkers' Construct
- FTB Quests
- Quark
- I like wood

## Final words

This is **not** a magic library that replaces pure Java modding. It's essentially a proof of concept created because working with MCreator is about as effective as asking your cat to fetch your TV remote.

Having said that;
this project sucks,
Java causes me physical pain,
and I have no idea where all these ghost features are come from.

**Nonetheless, it miraculously works!** If you come across any bugs or issues, _please_ hesitate to create an github issue. Your feedback is invaluable.

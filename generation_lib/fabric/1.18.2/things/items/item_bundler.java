package com.miner.bobstruction;

import com.miner.bobstruction.Bobstruction;
import net.minecraft.item.Item;

import net.minecraft.item.ItemGroup;
import net.minecraft.util.Identifier;
import net.minecraft.util.registry.Registry;

public class ModItems {

    // Declare your items
    public static final Item CUSTOM_ITEM = registerItem("custom_item", new Item(new Item.Settings().group(ItemGroup.MISC)));
    public static final Item SAPPHIRE = registerItem("sapphire", new Item(new Item.Settings().group(ItemGroup.MISC)));

    // Helper method for item registration
    private static Item registerItem(String name, Item item) {
        return Registry.register(Registry.ITEM, new Identifier(Bobstruction.MOD_ID, name), item);
    }

    // This method should be called from the main mod class
    public static void registerModItems() {
        Bobstruction.LOGGER.info("Registering Mod Items for " + Bobstruction.MOD_ID);
        // You can include other initialization or logging if needed
    }
}
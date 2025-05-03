package {internal_mod_id};

import {internal_mod_id}.{mod_id_upper};
import net.minecraft.world.item.Item;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.level.block.Block;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

{component_imports}


public class ModItems {
    public static final DeferredRegister<Item> ITEMS =
            DeferredRegister.create(ForgeRegistries.ITEMS, {mod_id_upper}.MOD_ID);

    {components}
    
    private static RegistryObject<Item> blockItem(RegistryObject<Block> block) {
		return ITEMS.register(block.getId().getPath(), () -> new BlockItem(block.get(), new Item.Properties()));
	}


    public  static void register(IEventBus eventBus) {
        ITEMS.register(eventBus);
    }
}

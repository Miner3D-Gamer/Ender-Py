package {internal_mod_id};


import {internal_mod_id}.{mod_id_upper};
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;
{component_imports}

import java.util.function.Supplier;

public class ModBlocks {
    public static final DeferredRegister<Block> BLOCKS =
            DeferredRegister.create(ForgeRegistries.BLOCKS, Bobstruction.MOD_ID);

    // public static final RegistryObject<Block> SAPPHIRE_BLOCK = registerBlock("sapphire_block",
    //         ()->new Block(BlockBehaviour.Properties.copy(Blocks.IRON_BLOCK).sound(SoundType.AMETHYST)), new Item.Properties());
    {components}



    private static <T extends Block> RegistryObject<T> registerBlock(String name, Supplier<T> block, Item.Properties item) {
        RegistryObject<T> toReturn = BLOCKS.register(name, block);
        registerBlockItem(name, toReturn, item);
        return toReturn;
    }

    

    private static <T extends Block> RegistryObject<Item> registerBlockItem(String name, RegistryObject<T> block, Item.Properties item) {
        return ModItems.ITEMS.register(name, () -> new BlockItem(block.get(), item));
    }

    

    public static void register(IEventBus eventBus) {
        BLOCKS.register(eventBus);
    }
}

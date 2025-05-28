package {internal_mod_id};

import {internal_mod_id}.{mod_id_upper};
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;
{component_imports}


public class ModCreativeModeTabs {
    public static  final DeferredRegister<CreativeModeTab> CREATIVE_MODE_TABS=
    DeferredRegister.create(Registries.CREATIVE_MODE_TAB,{mod_id_upper}.MOD_ID);

    {components}
    public static void register(IEventBus eventBus) {
        CREATIVE_MODE_TABS.register(eventBus);
    }
}

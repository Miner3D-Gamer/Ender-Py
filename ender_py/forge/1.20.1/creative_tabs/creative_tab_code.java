package {internal_mod_id}.creative_tabs;

import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import {internal_mod_id}.ModItems;
import {internal_mod_id}.ModBlocks;

public class {file_name} extends CreativeModeTab {
    public {file_name}() {
        super(CreativeModeTab.builder()
                .icon(()->new ItemStack({tab_icon}))
                .title(Component.translatable("{translation_key}"))
                .displayItems((pParameters, pOutput) -> {
                    {items}
                }){properties});
    }
}

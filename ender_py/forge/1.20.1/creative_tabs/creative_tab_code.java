package {internal_mod_id}.creative_tabs;

import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import com.miner.bobstruction.ModItems;
import com.miner.bobstruction.ModBlocks;

public class {component_id_upper}CreativeModeTab extends CreativeModeTab {
    public {component_id_upper}CreativeModeTab() {
        super(CreativeModeTab.builder()
                .icon(()->new ItemStack({tab_icon}))
                .title(Component.translatable("{translation_key}"))
                .displayItems((pParameters, pOutput) -> {
                    {items}
                }){properties});
    }
}

package {internal_mod_id}.items;

import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.item.ItemStack;

{imports}

public class {component_id_upper}Item extends Item {
    {additional_code_before}
	public static final Item.Properties PROPERTIES = new Item.Properties(){properties};

	public {component_id_upper}Item() {
		super(PROPERTIES);
        {additional_code_after}
	}
	{overrides}
}
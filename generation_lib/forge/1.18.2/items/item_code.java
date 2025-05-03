
package {internal_mod_id}.items;

import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.Item;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.item.ItemStack;

public class {component_id_upper}Item extends Item {
	public static final Item.Properties PROPERTIES = new Item.Properties(){properties};

	public {component_id_upper}Item() {
		super(PROPERTIES);
	}
	{overrides}
}
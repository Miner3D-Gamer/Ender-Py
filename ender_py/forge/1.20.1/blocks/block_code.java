package {internal_mod_id}.blocks;

import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.Block;

{imports}

public class {component_file_id}Block extends {block_type}Block {
    {additional_code_before}
    public {component_file_id}Block()  {
        super({before}BlockBehaviour.Properties.of(){properties}{after});
        {additional_code_after}
    }
    {overrides}
}
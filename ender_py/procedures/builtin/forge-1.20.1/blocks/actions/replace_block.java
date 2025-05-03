
BlockState oldState = {dimension}.getBlockState({pos});
BlockEntity blockEntity = {dimension}.getBlockEntity({pos});
CompoundTag blockNBT = blockEntity != null ? blockEntity.saveWithFullMetadata() : null;
Block newBlock = {block};
if (newBlock != null) {
    // Preserve blockstate if possible
    BlockState newState = newBlock.defaultBlockState();
    newState = copyBlockProperties(newState, oldState);

    // Set the new block with blockstate and NBT
    {dimension}.setBlock({pos}, newState, Block.UPDATE_ALL);
    if (blockNBT != null) {
        BlockEntity newBlockEntity = {dimension}.getBlockEntity({pos});
        if (newBlockEntity != null) {
            newBlockEntity.load(blockNBT);
        }
    }
}
// private static BlockState copyBlockProperties(BlockState newState, BlockState oldState) {
//         for (var property : oldState.getProperties()) {
//             if (newState.hasProperty(property)) {
//                 newState = newState.setValue(property, oldState.getValue(property));
//             }
//         }
//         return newState;
//     }
private static <T> BlockState copyBlockProperties(BlockState newState, BlockState oldState) {
        for (Property<?> property : oldState.getProperties()) {
            if (newState.hasProperty(property)) {
                newState = setProperty(newState, property, oldState);
            }
        }
        return newState;
    }
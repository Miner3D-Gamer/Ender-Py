private static <T extends Comparable<T>> BlockState setProperty(BlockState state, Property<T> property, BlockState oldState) {
        return state.setValue(property, (T) oldState.getValue(property));
    }
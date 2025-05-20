private static <T> BlockState copyBlockProperties(
  BlockState newState,
  BlockState oldState
) {
  for (Property<?> property : oldState.getProperties()) {
    if (newState.hasProperty(property)) {
      newState = setProperty(newState, property, oldState);
    }
  }
  return newState;
}

public static boolean isEntityGamemode(Entity entity, GameType gamemode) {
  if (!(entity instanceof ServerPlayer serverPlayer)) {
    return false;
  }
  return serverPlayer.gameMode.getGameModeForPlayer() == gamemode;
}

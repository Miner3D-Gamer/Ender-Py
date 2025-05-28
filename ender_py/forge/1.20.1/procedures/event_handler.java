package {internal_mod_id};

import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

{imports}

@Mod.EventBusSubscriber(modid = {mod_id_upper}.MOD_ID)
public class EventHandler {
    {events}

    {contexts}
}
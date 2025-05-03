def get_java_item(item, type):
    if item.startswith("minecraft:"):
        return "Items." + item.split(":")[1].upper()
    if item.__contains__(":"):
        raise Exception("Invalid item name: " + item)
    return f"Mod{type.title()+'s'}." + item + ".get()"


    


def recipe_shape_converter(shape):
    if isinstance(shape, str):
        return f'"{shape[0:2]}","{shape[3:5]}","{shape[5:8]}"'
    elif isinstance(shape, list):
        if len(shape) == 3:
            return f'"{shape[0]}","{shape[1]}","{shape[2]}"'
        else:
            return f'"{shape[0]}{shape[1]}{shape[2]}","{shape[3]}{shape[4]}{shape[5]}","{shape[6]}{shape[7]}{shape[8]}"'

    return shape


def get_item(item, mod):
    _ = item.count(":")
    if _ == 1:
        return f"{item}"
    elif _ == 0:
        return f"{mod.id}:{item}"
    else:
        raise Exception("Invalid item name: " + item)


def recipe_item_converter(item: dict[str, str | list[str]], mod):
    total = {}
    for key, items in item.items():
        if isinstance(items, str):
            total.update({key: get_item(items, mod)})
        elif isinstance(items, list):
            total.update({key: [get_item(i, mod) for i in items]})
        else:
            raise Exception("Invalid item name: " + items)
    
    return total
            
            

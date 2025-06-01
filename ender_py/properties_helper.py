from .components import VoxelShape, COMPONENT_TYPE

from shared.logging import log, ERROR, FATAL
import json
from typing import Optional, Union, cast, Any, NoReturn


def get_properties(
    component: COMPONENT_TYPE, path: str
) -> tuple[str, str, str, str, str, str, str]:
    # if component.type == "item":
    #     return "", ""
    with open(path, "r") as f:
        properties: dict[Any, Any] = json.load(f)

    var = TransFunctionValues()

    blacklist = [
        "texture",
        "item",
        "TYPE",
        "stack_size",
        "blocktype",
        "display_item",
        "loot_table",
        "is_block_item",
        "block_item_textures",
        "block_item_type",
        "icon_item",
        "items",
        "procedures",
    ]

    options = component.__slots__
    for option in options:
        if option in blacklist:
            continue
        skipped_properties_due_to_condition_not_met: list[Any] = []
        v = component.__getattribute__(option)
        if v is None:
            continue
        found_but_option_not_correct = False
        property = None
        for property in properties:
            if properties[property].get("condition", []) != []:
                if not is_full_condition_met(
                    component, properties[property].get("condition", [])
                ):
                    skipped_properties_due_to_condition_not_met.append(property)
                    continue  ############################################
            if property.startswith("_"):
                idx = 0
                for o in properties[property]["options"]:
                    if o["expected"] == option:
                        if handle_hit(
                            var,
                            component,
                            option,
                            properties[property],
                            property,
                            option_idx=idx,
                        ):
                            break
                    idx += 1
                else:
                    continue
                break
            else:
                ########################################################## IF IT HAS ['options'],  CHECK THE VALUE OF 'option'
                # tf is OPTION?
                if property == option:
                    if properties[property].get("options", []) == []:
                        if handle_hit(
                            var, component, option, properties[property], property
                        ):
                            break
                    else:
                        for idx, o in enumerate(properties[property]["options"]):
                            if o["expected"] == component.__getattribute__(option):
                                if handle_hit(
                                    var,
                                    component,
                                    option,
                                    properties[property],
                                    property,
                                    option_idx=idx,
                                ):
                                    break
                        else:
                            found_but_option_not_correct = True
                            continue
                    break  # IS THIS BREAK NEEDED??????

        else:
            if option in skipped_properties_due_to_condition_not_met:
                if properties[property].get(
                    "condition_not_met_okay", False
                ):  # TF DOES THIS EVEN MEAN??? THIS ISN'T A PROPERTY? IS IT?
                    continue
                else:
                    log(
                        ERROR, "Conditions were not met"
                    )  # improve this error messaging
            if found_but_option_not_correct:
                log(
                    FATAL,
                    "No option fitting for property %s found in %s (got %s)"
                    % (option, path, component.__getattribute__(option)),
                )
            else:
                log(FATAL, "Unable to find property %s in %s" % (option, path))

    return handle_transfunction_class_thingy_pls_help(var)


def is_correct_type(type: str, item: Any):
    if type == "float":
        try:
            float(item)
        except:
            return False
        else:
            return True
    elif type == "int":
        try:
            int(item)
        except:
            return False
        else:
            return True
    elif type == "bounding_box":
        for i in item:
            if not isinstance(i, VoxelShape):
                return False
        return True
    elif type == "bool":
        return item == True or item == False

    raise ValueError("Unknown requested type to check: '%s' for %s" % (type, item))


def handle_hit(
    var: "TransFunctionValues",
    component: COMPONENT_TYPE,
    slot: str,
    property: dict[str, Any],  # Actually dict[str, str|dict] i think
    property_name: str,
    option_idx: Optional[int] = None,
) -> bool:

    if property.get("skip", False):
        return True

    builder: AttributeBuilder = var.stuff.get(property_name, AttributeBuilder())
    l = property.get("location")
    if l is None:
        log(FATAL, "Location not provided for %s" % property_name)
    builder.location = cast(str, l)  # Yeah, this is probably fine
    builder.required_imports.extend(property.get("required_imports", []))
    builder.extra_code_after += property.get("extra_code_after", "")
    builder.extra_code_before += property.get("extra_code_before", "")

    if not option_idx is None:
        option = property["options"][option_idx]
        condition = option.get("condition")
        if not condition is None:
            if not is_full_condition_met(component, condition):
                return False
        to_insert = option.get("return")
        builder.required_imports.extend(option.get("required_imports", []))
        builder.extra_code_after += option.get("extra_code_after", "")
        builder.extra_code_before += option.get("extra_code_before", "")
        if to_insert:
            builder.insert_divider = property.get("option_divider", "")
            expected_value_type = option.get("type")
            value = component.__getattribute__(slot)
            if expected_value_type != "bool" and value == False:
                return True
            if not expected_value_type is None:
                if not is_correct_type(expected_value_type, value):
                    raise Exception(
                        "Incorrect type for %s, expected %s" % (slot, value)
                    )
                result = to_insert % value
            else:
                result = to_insert
            if isinstance(result, list):
                result = cast(list[str], result)
                builder.inserts.extend(result)
            else:
                builder.inserts.append(result)

    expected_value_type = property.get("type")
    value = component.__getattribute__(slot)
    if expected_value_type != "bool" and value == False:
        return True
    if not expected_value_type is None:

        if not is_correct_type(expected_value_type, value):
            raise Exception("Incorrect type for %s, expected %s" % (slot, value))
        if not property["insert"].__contains__("%s"):
            log(
                ERROR,
                "No %s detected even though it was expected do to an input type being defined: "
                + "%s" % property["insert"],
            )
            result = property["insert"]
        else:
            if isinstance(value, bool):
                value = str(value).lower()
            result = property["insert"] % value
    else:
        result = property.get("insert", "")
    builder.insert = result

    var.stuff[property_name] = builder

    return True


def is_full_condition_met(
    component: COMPONENT_TYPE, conditions: list[list[dict[str, Any]]]
):
    return all(
        [
            any(
                is_condition_met(component, condition)
                for condition in or_condition_subsets
            )
            for or_condition_subsets in conditions
        ]
    )


def is_condition_met(
    component: COMPONENT_TYPE, condition: dict[str, Any]
) -> Union[bool, NoReturn]:  # What even if this function for???
    condition_type = condition["type"]
    condition_name = condition["name"]

    if condition_type == "operator":
        if condition_name == "not":
            return not is_condition_met(component, condition["value"])
        elif condition_name == "and":
            return all([is_condition_met(component, c) for c in condition["value"]])
        elif condition_name == "or":
            return any([is_condition_met(component, c) for c in condition["value"]])
    elif condition_type == "slot":
        if getattr(component, condition_name) == condition["value"]:
            return True
        else:
            return False

    log(FATAL, "Unknown condition type/name %s (%s)" % (condition_type, condition_name))


def handle_transfunction_class_thingy_pls_help(var: "TransFunctionValues"):
    imports: list[str] = []

    attribute_string = ""
    extra_code_before = ""
    extra_code_after = ""
    after = ""
    before = ""
    overrides: list[str] = []
    for i in var.stuff:
        builder = var.stuff[i]
        imports.extend(builder.required_imports)
        if builder.location == "override":
            if builder.insert:
                if len(builder.inserts) > 0:
                    insert_insert = ", ".join(builder.inserts)
                    insert = [builder.insert % insert_insert]
                else:
                    insert = [builder.insert]
            else:
                insert = builder.inserts

            overrides.extend(insert)
        elif builder.location == "attribute":
            if len(builder.inserts) > 0:
                insert_insert = ", ".join(builder.inserts)
                insert = builder.insert % insert_insert
            else:
                insert = builder.insert
            attribute_string += insert
        elif builder.location == "after":
            if len(builder.inserts) > 0:
                insert_insert = ", ".join(builder.inserts)
                insert = builder.insert % insert_insert
            else:
                insert = builder.insert
            after += insert
        elif builder.location == "before":
            if len(builder.inserts) > 0:
                insert_insert = ", ".join(builder.inserts)
                insert = builder.insert % insert_insert
            else:
                insert = builder.insert
            before += insert
        else:
            log(FATAL, "Unknown location '%s' in %s" % (builder.location, i))
        extra_code_before += builder.extra_code_before
        extra_code_after += builder.extra_code_after

    final_overrides = "".join(
        "\n\t@Override\n\t%s" % override for override in overrides
    )

    imports = list(set(imports))
    final_import = ""
    for i in imports:
        final_import += "\nimport %s;" % i

    return (
        attribute_string,
        final_overrides,
        final_import,
        extra_code_before,
        extra_code_after,
        after,
        before,
    )


class TransFunctionValues:
    # You can't even escape the trans when coding
    def __init__(self) -> None:
        self.stuff: dict[str, AttributeBuilder] = {}

    def __repr__(self) -> str:
        result = ""
        for i in self.stuff:
            result += "\n%s:" % i
            result += "\n\t%s:" % self.stuff[i]
        return result


class AttributeBuilder:
    def __init__(self) -> None:
        self.location: str = ""
        self.insert: str = ""
        self.inserts: list[str] = []
        self.insert_divider: str = ""
        self.required_imports: list[str] = []
        self.extra_code_after: str = ""
        self.extra_code_before: str = ""

    def __repr__(self) -> str:
        return "<%s> (%s -> '%s') in %s %s" % (
            self.insert,
            self.inserts,
            self.insert_divider,
            self.location,
            self.required_imports,
        )

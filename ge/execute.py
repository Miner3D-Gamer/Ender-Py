from .check import input_error, is_number, simplify_number
import random, math, re
from typing import NoReturn


class Generator:
    def __init__(
        self,
        actions: list,
        custom_functions: dict = {},
        blacklisted_functions: list[str] = [],
    ):
        self.custom_functions = {}
        self.variables = {}
        self.actions = actions
        self.reset_builtin_functions(custom_functions, blacklisted_functions)

    def reset_builtin_functions(
        self, custom_functions: dict, blacklisted_functions: list[str]
    ):

        def choice_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return random.choice(resolved[0]["value"])

        def range_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)

            return {
                "type": "list",
                "value": [
                    {"type": "string", "value": simplify_number(i)}
                    for i in range(
                        int(resolved[0]["value"]), int(resolved[1]["value"]) + 1
                    )
                ],
            }

        def number_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)

            return {
                "type": "string",
                "value": simplify_number(
                    random.randint(
                        int(resolved[0]["value"]), int(resolved[1]["value"])
                    ),
                ),
            }

        def repeat_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            return_list = []
            amount = self.resolve_input(inputs[0])

            for i in range(int(amount["value"])):
                to_repeat = self.resolve_input(inputs[1], True)
                if to_repeat["type"] == "string":
                    if to_repeat["value"] == "&RETURN":
                        break
                input_error([amount, to_repeat], function_info, function)
                return_list.append(to_repeat)
            return {
                "type": "list",
                "value": return_list,
            }

        def loop_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            return_list = []

            while True:
                to_repeat = self.resolve_input(inputs[0], True)
                if to_repeat["type"] == "string":
                    if to_repeat["value"] == "&RETURN":
                        break
                input_error([to_repeat], function_info, function)
                return_list.append(to_repeat)
            return {
                "type": "list",
                "value": return_list,
            }

        def join_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            revolved = [self.resolve_input(x) for x in inputs]
            input_error(revolved, function_info, function)
            string = revolved[1]
            repeat_list = revolved[0]

            final = self.to_string(repeat_list["value"][0])
            for i in repeat_list["value"][1:]:
                # input_error([string, i], function_info, function)
                final += string["value"]
                final += self.to_string(i)
            return {
                "type": "string",
                "value": final,
            }

        def is_condition_true(condition) -> bool:
            if is_number(condition):
                return simplify_number(condition["value"]) != "0"
            elif condition["type"] == "string":
                return condition["value"] != ""
            elif condition["type"] == "list":
                return len(condition["value"]) > 0

            raise Exception(
                "Invalid condition type %s (%s)" % (condition["type"], condition)
            )

        def if_else_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)

            if is_condition_true(resolved[0]):
                return resolved[1]
            else:
                return resolved[2]

        def equal_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": ("1" if resolved[0]["value"] == resolved[1]["value"] else "0"),
            }

        def add_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    float(resolved[0]["value"]) + float(resolved[1]["value"])
                ),
            }

        def subtract_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    float(resolved[0]["value"]) - float(resolved[1]["value"])
                ),
            }

        def multiply_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    float(resolved[0]["value"]) * float(resolved[1]["value"])
                ),
            }

        def divide_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            if resolved[1]["value"] == 0:
                return {"type": "string", "value": "&ERROR_DIVIDE_BY_ZERO"}
            return {
                "type": "string",
                "value": simplify_number(
                    float(resolved[0]["value"]) / float(resolved[1]["value"])
                ),
            }

        def find_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": resolved[0]["value"][float(resolved[1]["value"])],
            }

        def length_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(len(resolved[0]["value"])),
            }

        def split_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "list",
                "value": [
                    {"type": "string", "value": x}
                    for x in resolved[0]["value"].split(resolved[1]["value"])
                ],
            }

        def get_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            if len(resolved[0]["value"]) >= float(resolved[1]["value"]):
                return {"type": "string", "value": "&ERROR_INDEX_OUT_OF_BOUNDS"}
            return {
                "type": "string",
                "value": resolved[0]["value"][float(resolved[1]["value"])],
            }

        def shuffle_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "list",
                "value": random.sample(resolved[0]["value"], len(resolved[0]["value"])),
            }

        def reverse_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            type = resolved[0]["type"]
            if type == "string":
                return {
                    "type": "string",
                    "value": resolved[0]["value"][::-1],
                }
            elif type == "list":
                return {
                    "type": "list",
                    "value": resolved[0]["value"][::-1],
                }
            else:
                raise Exception("Unknown type %s" % type)

        def concat_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            type = resolved[0]["type"]
            if type == "string":
                return {
                    "type": "string",
                    "value": resolved[0]["value"] + resolved[1]["value"],
                }
            elif type == "list":
                return {
                    "type": "list",
                    "value": resolved[0]["value"] + resolved[1]["value"],
                }
            else:
                raise Exception("Unknown type %s" % type)

        def clamp_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            type = resolved[0]["type"]
            if is_number(resolved[0]):

                def clamp(min, max, value):
                    if value < min:
                        return min
                    elif value > max:
                        return max
                    else:
                        return value

                return {
                    "type": "string",
                    "value": simplify_number(
                        clamp(
                            float(resolved[1]["value"]),
                            float(resolved[2]["value"]),
                            float(resolved[0]["value"]),
                        )
                    ),
                }
            if type == "string":
                return {
                    "type": "string",
                    "value": resolved[0]["value"][
                        float(resolved[1]["value"]) : float(resolved[2]["value"])
                    ],
                }
            elif type == "list":
                return {
                    "type": "list",
                    "value": resolved[0]["value"][
                        float(resolved[1]["value"]) : float(resolved[2]["value"])
                    ],
                }
            else:
                raise Exception("Unknown type %s" % type)

        def upper_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": resolved[0]["value"].upper(),
            }

        def lower_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": resolved[0]["value"].lower(),
            }

        def capitalize_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": resolved[0]["value"].capitalize(),
            }

        def title_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": resolved[0]["value"].title(),
            }

        def strip_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": resolved[0]["value"].strip(),
            }

        def lstrip_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": resolved[0]["value"].lstrip(),
            }

        def rstrip_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": resolved[0]["value"].rstrip(),
            }

        def replace_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": resolved[0]["value"].replace(
                    resolved[1]["value"], resolved[2]["value"]
                ),
            }

        def mod_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    float(resolved[0]["value"]) % float(resolved[1]["value"])
                ),
            }

        def abs_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(abs(float(resolved[0]["value"]))),
            }

        def floor_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(math.floor(float(resolved[0]["value"]))),
            }

        def ceil_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(math.ceil(float(resolved[0]["value"]))),
            }

        def round_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(round(float(resolved[0]["value"]))),
            }

        def min_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    min(float(resolved[0]["value"]), float(resolved[1]["value"]))
                ),
            }

        def max_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    max(float(resolved[0]["value"]), float(resolved[1]["value"]))
                ),
            }

        def contains_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(resolved[0]["value"] in resolved[1]["value"]),
            }

        def startswith_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    resolved[0]["value"].startswith(resolved[1]["value"])
                ),
            }

        def endswith_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    resolved[0]["value"].endswith(resolved[1]["value"])
                ),
            }

        def sort_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "list",
                "value": sorted(resolved[0]["value"]),
            }

        def unique_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "list",
                "value": list(set(resolved[0]["value"])),
            }

        def pow_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    float(resolved[0]["value"]) ** float(resolved[1]["value"])
                ),
            }

        def log_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    math.log(float(resolved[0]["value"]), float(resolved[1]["value"]))
                ),
            }

        def sqrt_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(math.sqrt(float(resolved[0]["value"]))),
            }

        def sin_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(math.sin(float(resolved[0]["value"]))),
            }

        def cos_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(math.cos(float(resolved[0]["value"]))),
            }

        def tan_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(math.tan(float(resolved[0]["value"]))),
            }

        def asin_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(math.asin(float(resolved[0]["value"]))),
            }

        def acos_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(math.acos(float(resolved[0]["value"]))),
            }

        def atan_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(math.atan(float(resolved[0]["value"]))),
            }

        def atan2_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    math.atan2(float(resolved[0]["value"]), float(resolved[1]["value"]))
                ),
            }

        def count_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    resolved[0]["value"].count(resolved[1]["value"])
                ),
            }

        def ljust_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    resolved[0]["value"].ljust(float(resolved[1]["value"]))
                ),
            }

        def rjust_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    resolved[0]["value"].rjust(float(resolved[1]["value"]))
                ),
            }

        def mjust_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    resolved[0]["value"].center(float(resolved[1]["value"]))
                ),
            }

        def and_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    1
                    if (
                        is_condition_true(resolved[0])
                        and is_condition_true(resolved[1])
                    )
                    else 0
                ),
            }

        def or_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    1
                    if (
                        is_condition_true(resolved[0]) or is_condition_true(resolved[1])
                    )
                    else 0
                ),
            }

        def not_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(0 if is_condition_true(resolved[0]) else 1),
            }

        def greater_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    float(resolved[0]["value"]) > float(resolved[1]["value"])
                ),
            }

        def less_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    float(resolved[0]["value"]) < float(resolved[1]["value"])
                ),
            }

        def greater_or_equal_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    float(resolved[0]["value"]) >= float(resolved[1]["value"])
                ),
            }

        def less_or_equal_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    float(resolved[0]["value"]) <= float(resolved[1]["value"])
                ),
            }

        def exp_func(inputs: list[dict[str, str]], function_info: dict, function: str):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(math.exp(float(resolved[0]["value"]))),
            }

        def greatest_common_divisor_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    math.gcd(int(resolved[0]["value"]), int(resolved[1]["value"]))
                ),
            }

        def common_multiple_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    math.lcm(int(resolved[0]["value"]), int(resolved[1]["value"]))
                ),
            }

        def set_var_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            self.variables[resolved[0]["value"]] = resolved[1]
            return {"type": "string", "value": ""}

        def get_var_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            got = self.variables.get(
                resolved[0]["value"],
                {"type": "string", "value": "&ERROR_VARIABLE_NOT_FOUND"},
            )
            return got

        def set_func_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            # input_error(resolved, function_info, function)
            self.custom_functions[self.resolve_input(inputs[0])["value"]] = inputs[1]
            return {"type": "string", "value": ""}

        def get_func_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            got = self.custom_functions.get(
                resolved[0]["value"],
                {"type": "string", "value": "&ERROR_FUNCTION_NOT_FOUND"},
            )
            return self.resolve_input(got, True)

        def is_error_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    1 if resolved[0]["type"].startswith("&ERROR") else 0
                ),
            }

        def does_native_function_exist_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    1 if resolved[0]["value"] in self.functions else 0
                ),
            }

        def match_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": simplify_number(
                    1 if re.match(resolved[0]["value"], resolved[1]["value"]) else 0
                ),
            }

        def replaceall_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "string",
                "value": re.sub(
                    resolved[0]["value"], resolved[1]["value"], resolved[2]["value"]
                ),
            }

        def by_group_func(
            inputs: list[dict[str, str]], function_info: dict, function: str
        ):
            resolved = [self.resolve_input(x) for x in inputs]
            input_error(resolved, function_info, function)
            return {
                "type": "list",
                "value": [
                    {"type": "string", "value": x}
                    for x in re.findall(resolved[0]["value"], resolved[1]["value"])
                ],
            }

        self.functions = {
            # Condition
            "if_else": {
                "inputs": [{"type": "string"}, {"type": "any"}, {"type": "any"}],
                "func": if_else_func,
            },
            "equals": {
                "inputs": [{"type": "any"}, {"type": "any"}],
                "func": equal_func,
            },
            "and": {
                "inputs": [{"type": "any"}, {"type": "any"}],
                "func": and_func,
            },
            "or": {
                "inputs": [{"type": "any"}, {"type": "any"}],
                "func": or_func,
            },
            "not": {
                "inputs": [{"type": "any"}],
                "func": not_func,
            },
            "greater": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": greater_func,
            },
            "less": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": less_func,
            },
            "greater_or_equal": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": greater_or_equal_func,
            },
            "less_or_equal": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": less_or_equal_func,
            },
            # Math - Basic
            "add": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": add_func,
            },
            "subtract": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": subtract_func,
            },
            "multiply": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": multiply_func,
            },
            "divide": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": divide_func,
            },
            # Math - Advanced
            "mod": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": mod_func,
            },
            "abs": {
                "inputs": [{"type": "int"}],
                "func": abs_func,
            },
            "floor": {
                "inputs": [{"type": "int"}],
                "func": floor_func,
            },
            "ceil": {
                "inputs": [{"type": "int"}],
                "func": ceil_func,
            },
            "min": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": min_func,
            },
            "max": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": max_func,
            },
            "pow": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": pow_func,
            },
            "round": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": round_func,
            },
            # Math - Really Advanced
            "sqrt": {"inputs": [{"type": "int"}], "func": sqrt_func},
            "log": {"inputs": [{"type": "int"}, {"type": "int"}], "func": log_func},
            "sin": {"inputs": [{"type": "int"}], "func": sin_func},
            "cos": {"inputs": [{"type": "int"}], "func": cos_func},
            "tan": {"inputs": [{"type": "int"}], "func": tan_func},
            "asin": {"inputs": [{"type": "int"}], "func": asin_func},
            "acos": {"inputs": [{"type": "int"}], "func": acos_func},
            "atan": {"inputs": [{"type": "int"}], "func": atan_func},
            "atan2": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": atan2_func,
            },
            # Math - Weird
            "exp": {"inputs": [{"type": "int"}], "func": exp_func},
            "gcd": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": greatest_common_divisor_func,
            },
            "lcm": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": common_multiple_func,
            },
            # Math - idk
            "range": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": range_func,
            },
            "randint": {
                "inputs": [{"type": "int"}, {"type": "int"}],
                "func": number_func,
            },
            # List/String stuff
            "find": {
                "inputs": [{"type": ["list", "string"]}, {"type": "str"}],
                "func": find_func,
            },
            "get": {
                "inputs": [{"type": ["list", "string"]}, {"type": "int"}],
                "func": get_func,
            },
            "len": {
                "inputs": [{"type": ["list", "string"]}],
                "func": length_func,
            },
            "reverse": {
                "inputs": [{"type": ["list", "string"]}],
                "func": reverse_func,
            },
            "clamp": {
                "inputs": [
                    {"type": ["list", "string"]},
                    {"type": "int"},
                    {"type": "int"},
                ],
                "func": clamp_func,
            },
            "concatenate": {
                "inputs": [{"type": ["list", "string"]}, {"type": ["list", "string"]}],
                "func": concat_func,
            },
            "count": {
                "inputs": [{"type": ["list", "string"]}, {"type": "string"}],
                "func": count_func,
            },
            "contains": {
                "inputs": [{"type": ["list", "string"]}, {"type": "any"}],
                "func": contains_func,
            },
            "choice": {
                "inputs": [{"type": ["list", "string"]}],
                "func": choice_func,
            },
            # String stuff
            "split": {
                "inputs": [{"type": ["list", "string"]}, {"type": "string"}],
                "func": split_func,
            },
            "replace": {
                "inputs": [
                    {"type": ["string"]},
                    {"type": "string"},
                    {"type": "string"},
                ],
                "func": replace_func,
            },
            "upper": {"inputs": [{"type": "string"}], "func": upper_func},
            "lower": {"inputs": [{"type": "string"}], "func": lower_func},
            "title": {"inputs": [{"type": "string"}], "func": title_func},
            "strip": {"inputs": [{"type": "string"}], "func": strip_func},
            "lstrip": {"inputs": [{"type": "string"}], "func": lstrip_func},
            "rstrip": {"inputs": [{"type": "string"}], "func": rstrip_func},
            "capitalize": {"inputs": [{"type": "string"}], "func": capitalize_func},
            "startswith": {
                "inputs": [{"type": "string"}, {"type": "string"}],
                "func": startswith_func,
            },
            "endswith": {
                "inputs": [{"type": "string"}, {"type": "string"}],
                "func": endswith_func,
            },
            "ljust": {
                "inputs": [{"type": "string"}, {"type": "int"}, {"type": "string"}],
                "func": ljust_func,
            },
            "rjust": {
                "inputs": [{"type": "string"}, {"type": "int"}, {"type": "string"}],
                "func": rjust_func,
            },
            "cjust": {
                "inputs": [{"type": "string"}, {"type": "int"}, {"type": "string"}],
                "func": mjust_func,
            },
            # List stuff
            "shuffle": {
                "inputs": [{"type": ["list"]}],
                "func": shuffle_func,
            },
            "sort": {
                "inputs": [{"type": ["list"]}],
                "func": sort_func,
            },
            "unique": {
                "inputs": [{"type": ["list"]}],
                "func": unique_func,
            },
            "join": {
                "inputs": [{"type": "list"}, {"type": "string"}],
                "func": join_func,
            },
            # Regex stuff
            "match": {
                "inputs": [{"type": "string"}, {"type": "string"}],
                "func": match_func,
            },
            "replace_all": {
                "inputs": [{"type": "string"}, {"type": "string"}, {"type": "string"}],
                "func": replaceall_func,
            },
            "find_all": {
                "inputs": [{"type": "string"}, {"type": "string"}],
                "func": by_group_func,
            },
            # Misc - Store stuff
            "set_var": {
                "inputs": [{"type": "string"}, {"type": "any"}],
                "func": set_var_func,
            },
            "get_var": {
                "inputs": [{"type": "string"}],
                "func": get_var_func,
            },
            "create_function": {
                "inputs": [{"type": "string"}, {"type": "any"}],
                "func": set_func_func,
            },
            "call_function": {
                "inputs": [{"type": "string"}],
                "func": get_func_func,
            },
            # Misc - Do that again
            "return": {
                "inputs": [],
                "func": lambda x, y, z: {"type": "string", "value": "&RETURN"},
            },
            "loop": {
                "inputs": [{"type": "any"}],
                "func": loop_func,
            },
            "repeat": {
                "inputs": [{"type": "int"}, {"type": "any"}],
                "func": repeat_func,
            },
            # Misc - Control flow
            "is_error": {
                "inputs": [{"type": "any"}],
                "func": is_error_func,
            },
            "does_native_function_exist": {
                "inputs": [{"type": "string"}],
                "func": does_native_function_exist_func,
            },
        }
        self.functions.update(custom_functions)
        for b in blacklisted_functions:
            self.functions.pop(b, None)

    def generate(self) -> str:

        final = ""

        for action in self.actions:
            final += self.to_string(action)

        return final
    
    def get_every_function(self):
        return self.functions

    def resolve_input(self, input, inside_recursion: bool = False):
        if input["type"] in ["list", "string"]:
            return input
        elif input["type"] == "function":
            return self.handle_function(input["name"], input["inputs"])
        else:
            raise Exception("Unknown type %s" % input["type"])

    def handle_function(self, function: str, inputs: list[dict]) -> dict:

        function_info = self.functions.get(function)
        if function_info is None:
            raise Exception(
                "Unknown function '%s' (Action list: %s)" % (function, self.actions)
            )

        resolved = inputs

        # input_error(resolved, function_info, function)

        return function_info["func"](inputs, function_info, function)

        raise Exception(
            "Unknown function %s (with inputs resolved to %s, original inputs %s)"
            % (function, resolved, inputs)
        )

    def to_string(self, action: dict) -> str | NoReturn:
        type = action["type"]
        if type == "string":
            return action["value"]
        elif type in ["function", "multi_function"]:
            return self.to_string(
                self.handle_function(action["name"], action["inputs"])
            )
        elif type == "list":
            return "[" + ", ".join([self.to_string(i) for i in action["value"]]) + "]"

        raise Exception("Unknown type %s" % type)


__all__ = ["Generator"]

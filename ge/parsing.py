from typing import NoReturn
from string import ascii_letters

quotes = ["'", '"']


def expect_next_action(
    string: str, plus: str, inp_idx: int, end: str = ""
) -> tuple[str, int] | NoReturn:
    if string == "":
        return "", inp_idx
    idx = -1
    for char in string:
        idx += 1
        if char == " ":
            continue
        else:
            if plus and not char == "[":
                if char == plus:
                    return expect_next_action(string[idx + 1 :], "", inp_idx + idx)
                if char == end:
                    return string[idx + 1 :], inp_idx + idx
                raise Exception(
                    "Expected %s but got %s in %s (Did you close one too many brackets?) at character %s"
                    % (plus, char, string, inp_idx + idx)
                )
            else:
                return string[idx:], inp_idx + idx

    raise Exception("Expected action got '%s' at character %s" % string, inp_idx + idx)


def skip_until_outside(string: str, idx: int) -> NoReturn | tuple[str, str, int]:
    table = {
        "(": ")",
        "{": "}",
        "[": "]",
    }
    inverse_value = [v for k, v in table.items()]
    depth = 0
    outside_indicator = table[string[0]]
    total = ""
    for idx, char in enumerate(string):
        if char in table:
            depth += 1
            continue
        elif char in inverse_value:
            depth -= 1
            if depth == 0:
                if char != outside_indicator:
                    raise Exception(
                        "Expected %s instead of %s to exit" % (outside_indicator, char)
                    )
                return string[1:idx], string[idx + 1 :], idx
            continue
        total += char

    raise Exception("%s brackets have not been closed at character %s" % (depth, idx))
    # raise Exception("Something went wrong while parsing, gathered: '%s' from '%s'" % (total, string))


def separate_action(
    string: str, separator: str, first: bool, idx: int, end: str = ""
) -> tuple[dict, str]:
    if not first:
        string, idx = expect_next_action(string, separator, idx, end)
    if not string:
        return {}, ""
    if string[0] in quotes:
        full = ""
        inside_string = string[0]
        string = string[1:]
        escaping = False
        for char_idx, char in enumerate(string):
            if char == inside_string:
                if escaping:
                    full += char
                    escaping = False
                    continue
                return {
                    "type": "string",
                    "value": full,
                }, string[char_idx + 1 :]
            if char == "\\":
                escaping = True
                continue
            if escaping:
                raise Exception(
                    "Expected string end after escape character (%s) but got %s"
                    % (inside_string, char)
                )

            full += char

    if string[0] in "[":
        return {
            "type": "list",
            "value": wrapper(string[1:], ",", "]", idx),
        }, ""

    function = ""

    for idx, char in enumerate(string):
        if char in ascii_letters + "_":
            function += char
        elif char == "(":
            inputs, next, idx = skip_until_outside(string[idx:], idx)
            next = next.lstrip()
            # if next and (next[0] in ascii_letters or next[0] == "("):
            #     all_inputs = wrapper(inputs, ",", "", idx)
            #     # Multifunction!
            #     while True:
            #         if next == "":
            #             break
            #         if next[0] == " ":
            #             next = next[1:]
            #             continue
            #         if next[0] == "(":
            #             next_inputs, next, idx = skip_until_outside(next, idx)
            #             all_inputs.extend(wrapper(next_inputs, ",", "", idx))
            #             continue
            #         if next[0] in ascii_letters:
            #             next_multi_function_part, next = separate_action(
            #                 next, "+", True, idx, ""
            #             )
            #             function += "_" + next_multi_function_part["name"]
            #             all_inputs.extend(next_multi_function_part["inputs"])
            #             continue
            #         raise Exception(next)

            #     return {
            #         "type": "multi_function",
            #         "name": function,
            #         "inputs": all_inputs,
            #     }, next

            return {
                "type": "function",
                "name": function,
                "inputs": wrapper(inputs, ",", "", idx),
            }, next

    raise Exception(
        "Expected next action but got invalid characters '%s' (Did you forget to quote them?)"
        % string
    )


def wrapper(string: str, plus: str, end: str, idx: int) -> list[dict]:
    all_actions = []
    action, further = separate_action(string, plus, True, idx, end)
    if action != {}:
        all_actions.append(action)
    while True:
        action, further = separate_action(further, plus, False, idx, end)
        if action != {}:
            all_actions.append(action)
        if not further:
            break
    # return_list = []
    # for idx in range(len(all_actions) - 1):
    #     last = (idx % (len(all_actions) - 1)) == 0
    #     now = all_actions[idx]
    #     future = all_actions[idx + 1]
    #     if now["type"] == future["type"] == "function":
    #         print("HERE")
    #         if future["name"].startswith("_"):
    #             return_list.append(
    #                 {
    #                     "type": "function",
    #                     "name": now["name"] + future["name"],
    #                     "inputs": now["inputs"] + future["inputs"],
    #                 }
    #             )
    #         else:
    #             return_list.append(now)
    #             if last:
    #                 return_list.append(future)
    #     else:
    #         print(now["type"], future["type"])
    #         return_list.append(now)
    #         if last:
    #             return_list.append(future)

    return all_actions


def split_genex_into_actions(string):
    # 3(.5) Modes:
    # Expecting next action
    # Extracting string/function
    # Skipping subcode

    return wrapper(string, "+", "", 0)


__all__ = ["split_genex_into_actions"]

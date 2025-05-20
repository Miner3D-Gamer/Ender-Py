def isfloat(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_number(x):
    if x["type"] == "string":
        return isfloat(x["value"])
    return False


def simplify_number(x: str | int | float):
    new = str(x).rstrip("0")
    if len(new) == 0:
        return "0"
    if new[-1] == ".":
        new = new[:-1]
    return new


def input_error(all_inputs: list[dict], rules: dict, function: str):
    return
    inputs = rules["inputs"]
    expected = len(inputs)
    gotten = len(all_inputs)
    if gotten != expected:
        raise Exception(
            "Expected %s inputs but got %s for %s, given %s"
            % (expected, gotten, function, all_inputs)
        )
    for idx in range(expected):
        given_input = all_inputs[idx]
        expected_input = inputs[idx]

        expected_type_pre = expected_input["type"]
        if isinstance(expected_type_pre, str):
            expected_type_pre = [expected_type_pre]

        for expected_type in expected_type_pre:
            if expected_type == "any":
                break
            elif expected_type == "int":
                if is_number(given_input):
                    break
            else:
                if given_input["type"] == expected_type:
                    break
        else:
            raise Exception(
                "Expected input %s to be of type %s but got type %s for %s, given %s"
                % (
                    idx,
                    expected_input["type"],
                    given_input["type"],
                    function,
                    all_inputs,
                )
            )

    # got = len(all_inputs)
    # if got != expected:
    #     raise Exception(
    #         "Expected %s inputs but got %s for %s, given %s"
    #         % (expected, got, function, all_inputs)
    #    )


__all__ = ["is_number", "simplify_number", "input_error"]

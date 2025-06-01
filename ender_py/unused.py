def remove_brackets(string: str):
    if string.startswith("[") and string.endswith("]"):
        return string[1:-1]
    return string

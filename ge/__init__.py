"""The opposite of RregEx; GenEx instead of validating/parsing strings, it generates them. I have not yet tested it extensively."""

from .parsing import split_genex_into_actions
from .execute import Generator


def GenEx(string: str, custom_functions: dict = {}, blacklisted_functions: list[str] = []):
    return Generator(
        split_genex_into_actions(string), custom_functions, blacklisted_functions
    ).generate()


__all__ = ["GenEx"]
# string = r"'You\\'re a '+choice(['idiot','fool','coward']) + ' for gambling, here is todays number: ' + join(repeat('6', choice(range('1', '6'))), '')"

# string = r"if (equals('2', choice(range('1', '3')))) ('You won') else ('You lost')"
# string = "repeat('10', if_else (randint('0','3'), 'hi', return()))"


# print(GenEx(string))

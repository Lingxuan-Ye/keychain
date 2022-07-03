from enum import Enum


class Help(Enum):
    """
    'argparse.ArgumentParser' will remove leading and trailing whitespace,
    including newline. Therefore docstrings are recommended to assign members.

    Note that help info will NOT display in the terminal as what it looks like
    in the docstring.
    """

    DESCRIPTION = """
        pass
    """

    EPILOG = """
        pass
    """

    FILE = """

    """
    
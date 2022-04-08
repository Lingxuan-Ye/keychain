from functools import wraps
import secrets
import string
import typing
from type_check import *

PRESET = {
    "classic": 0x08040400,
    "uniform": 0x04040404,
    "all-lower": 0x10000000,
    "all-upper": 0x00100000,
    "all-digit": 0x00001000,
    "all-punctuation": 0x00000010
}
DEFAULT_MODE = PRESET["uniform"]


def _raise(func):

    class InvalidArgument(Exception):
        pass

    @wraps(func)
    def wrapper(*args, **kwargs):
        result: dict = func(*args, **kwargs)
        if not isinstance(result, dict):
            return result
        error_info = result.get("error_info", None)
        if error_info is not None:
            raise InvalidArgument(error_info)
        return result

    return wrapper


class PasswordGenerator:
    """
    Generate a random password string.

    It takes one optional argument while instantiating, which should be:
        - a 4-element tuple, in which the elements are integers
          greater than or equal to 0x00 and less than or equal to 0xff, or
        - an integer or integer-like string, which is
          greater than 0x00000000 and less than or equal to 0xffffffff.

    If the argument given is a tuple, the elements respectively represent
    the numbers of characters of lowercase, uppercase, digits and punctuation.

    If the argument given is an integer or integer-like string, it will
    be formatted to an 8-digit hexadecimal string, every 2 digits
    respectively represent the numbers(hexadecimal) of characters of
    lowercase, uppercase, digits and punctuation, and further converted to
    a tuple.
    """

    def __init__(self, mode: typing.Union[tuple, int, str] = DEFAULT_MODE):
        self.__lowercase = string.ascii_lowercase
        self.__uppercase = string.ascii_uppercase
        self.__digits = string.digits
        self.__punctuation = string.punctuation
        self.__mode = self.__mode_format(mode)["mode_formatted"]

    def set_mode(self, mode: typing.Union[tuple, int, str]):
        """
        Set mode.
        """
        self.__mode = self.__mode_format(mode)["mode_formatted"]

    @staticmethod
    @_raise
    def __mode_format(mode: typing.Union[tuple, int, str]) -> dict:
        """
        If the argument 'mode' is a tuple, check whether it is valid.

        If the argument 'mode' is an integer or integer-like string,
        convert the given argument to a 4-tuple,
        in which the elements are integers greater than or equal to 0x00,
        and less than or equal to 0xff.

        String starting with "0b" should be considered as binary first,
        even if it can be interpreted as hexadecimal successfully.

        Hexadecimal string without "0x" prefix is deprecated.
        """
        type_check(mode, (tuple, int, str), "mode", False)
        result = {"error_info": None, "mode_formatted": None}
        if isinstance(mode, tuple):
            length = len(mode)
            if length != 4:
                error_info = "the length of the argument must be exactly 4, " \
                           + f"not '{length}', if a 'tuple' is given"
                result["error_info"] = error_info
                return result
            element_type_check(mode, int, "mode", False, True)
            for index, element in enumerate(mode):
                if not (0x00 <= element <= 0xff):
                    error_info = f"argument 'mode[{index}]' must be " \
                               + "greater than or equal to 0x00 and " \
                               + "less than or equal to 0xff, " \
                               + "if a 'tuple' is given"
                    result["error_info"] = error_info
                    return result
            if sum(mode) == 0:
                error_info = "there must be at least one element " \
                           + "greater than 0 in the argument, " \
                           + "if a 'tuple' is given"
                result["error_info"] = error_info
                return result
            result["mode_formatted"] = mode
            return result
        elif isinstance(mode, int):
            mode_int = mode
        else:  # isinstance(mode, str) == True
            mode_str = mode.strip()
            for base in (10, 2, 8, 16):
                try:
                    mode_int = int(mode_str, base)
                    break
                except ValueError:
                    pass
            else:
                error_info = "argument must be integer-like, " \
                           + "if a 'str' is given"
                result["error_info"] = error_info
                return result
        if not (0x00000000 < mode_int <= 0xffffffff):
            error_info = "argument must be " \
                       + "greater than 0x00000000 and " \
                       + "less than or equal to 0xffffffff, " \
                       + "if an 'int' or integer-like 'str' is given"
            result["error_info"] = error_info
            return result
        mode_hex = f"{mode_int:08x}"
        # 8-digit hexadecimal string without "0x" prefix
        result["mode_formatted"] = (
            int(mode_hex[0:2], 16),
            int(mode_hex[2:4], 16),
            int(mode_hex[4:6], 16),
            int(mode_hex[6:8], 16)
        )
        return result

    def generate(self):
        """
        Generate a random password string.
        """
        mode = self.__mode
        char_tuple = (self.__lowercase, self.__uppercase, self.__digits,
                      self.__punctuation)
        chosen_char = []
        for (index, length) in enumerate(mode):
            for _ in range(length):
                chosen_char.append(secrets.choice(char_tuple[index]))
        self.__shuffle(chosen_char)
        password = "".join(chosen_char)
        return password

    @staticmethod
    def __shuffle(x):
        """
        The same algorithm as method random.Random.shuffle,
        with the function secrets.randbelow instead.
        """
        for i in reversed(range(1, len(x))):
            # pick an element in x[:i+1] with which to exchange x[i]
            j = secrets.randbelow(i + 1)
            x[i], x[j] = x[j], x[i]


if __name__ == "__main__":
    while True:
        try:
            arg = eval(input("mode: "))
            generator = PasswordGenerator(arg)
            print(generator.generate(), "\n")
        except Exception as e:
            print(e.args)

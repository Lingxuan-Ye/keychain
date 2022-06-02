from enum import Enum
import string


class Char(Enum):

    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    PUNCTUATION = string.punctuation

    SPACE = " "
    DELIMITER = ","
    TAB = "\t"
    CR = "\r"
    LF = "\n"
    CRLF = CR + LF

    INDENT = SPACE * 4
    NEWLINE = LF

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


TAB_: str = Char.NEWLINE.value + Char.INDENT.value
SEP_: str = Char.DELIMITER.value + TAB_
TAB__: str = Char.NEWLINE.value + Char.INDENT.value * 2
SEP__: str = Char.DELIMITER.value + TAB__

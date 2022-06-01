from ..utils import Char

NoneType = type(None)

TAB_: str = Char.NEWLINE.value + Char.INDENT.value
SEP_: str = Char.DELIMITER.value + TAB_
TAB__: str = Char.NEWLINE.value + Char.INDENT.value * 2
SEP__: str = Char.DELIMITER.value + TAB__

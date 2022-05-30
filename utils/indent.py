from typing import List
from .char import Char


def indent(lines: str, level: int = 1, firstline_indent: bool = False) -> str:
    list_: List[str] = lines.splitlines(keepends=True)
    for _index, _line in enumerate(list_):
        if _index == 0 and not firstline_indent:
            continue
        if level >= 0:
            list_[_index] = Char.INDENT.value * level + _line
        else:
            for _ in range(abs(level)):
                if _line.startswith(Char.INDENT.value):
                    _line = _line[1:]
            list_[_index] = _line
    return "".join(list_)

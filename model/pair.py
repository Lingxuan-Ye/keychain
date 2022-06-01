from typing import Any, Hashable, NamedTuple


class Pair(NamedTuple):
    key: Hashable
    value: Any

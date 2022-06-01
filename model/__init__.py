"""
This package defines 'User', 'Key' 'Group' and "KeyChain'.

Conventions
-----------
valid
    An object is valid if and only if its property 'valid' is True.

    If an object is invalid, it will:
    -   Have lower priority to be kept in a higher-level container.
        In other words, if multiple instances of a class with SAME NAME
        are passed, only the LAST VALID one or the LAST one (if no one is
        valid) will remain.
    -   Not appear in container's string representation.
    -   Not appear in the result of container's 'export' method unless
        explicitly call method with 'valid_only' set to False.

temp_ | list_ | dict_
    Identifiers for temporary variables.
    'list_' means it is a Sequence and molst likely a list.
    'dict_' means it is a Mapping and molst likely a dict.

for-loop variable
    If the type of a for-loop variable is discussed in the loop, this variable
    should be named as 'i', 'j', etc.
    Otherwise, it should be named with a leading '_'.
    Sometimes there may be a confusing statement, for example:
        >   for i in self.values():
        >       _key: Key = i
    This kind of statement is of no use but a hint for 'mypy'.
"""
from .group import Group
from .key import Key
from .keychain import KeyChain
from .user import User

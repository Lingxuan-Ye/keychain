from bisect import insort
from collections import UserDict
from copy import deepcopy
from typing import Callable, Dict, List, Optional, Union

from ..utils import indent
from ._constants import SEP_, TAB_
from .key import Key
from .pair import Pair


class Group(UserDict):
    """
    Filter arguments but not raise exception when initiate.

    If 'force' is False, only 'Key' instances with attribute 'group'
    being None or equal to 'self.groupname' will be accepted, otherwise
    attribute 'group' of 'Key' instances will be set to 'self.groupname'.

    Warning:
        - attribute 'data' of 'Group' instance is not recommended to
          access from outer scope.
    """
    def __init__(self, groupname: str, *keys: Key, force: bool = False) -> None:
        self.data: Dict[str, Key] = {}
        self.__groupname: str = groupname
        for i in keys:
            if isinstance(i, Key):
                if i.group is None:
                    i.group = self.__groupname
                if i.group != self.__groupname:
                    if force:
                        i.group = self.__groupname
                    else:
                        continue
                if i.valid:
                    pass
                elif i.keyname not in self.data:
                    pass
                elif self.data[i.keyname].valid:
                    continue
                self.data[i.keyname] = i
        self.__deleted: bool = False

    def __setattr__(
        self,
        __name: str,
        __value: Union[Dict[str, Key], str, bool]
    ) -> None:
        CLASSNAME = self.__class__.__name__
        if __name == "data":
            if not isinstance(__value, dict):
                raise TypeError
            for i, j in __value.items():
                if not isinstance(i, str):
                    raise TypeError
                if not isinstance(j, Key):
                    raise TypeError
                if i != j.keyname:
                    raise ValueError
                if j.group is None:
                    j.group = self.__groupname
                if j.group != self.__groupname:
                    raise ValueError
        elif __name == f"_{CLASSNAME}__groupname":
            if not isinstance(__value, str):
                raise TypeError
        elif __name == f"_{CLASSNAME}__deleted":
            if not isinstance(__value, bool):
                raise TypeError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    def __setitem__(self, __key: str, __item: Key) -> None:
        if not isinstance(__key, str):
            raise TypeError
        if not isinstance(__item, Key):
            raise TypeError
        if __key != __item.keyname:
            raise ValueError
        if __item.group is None:
            __item.group = self.__groupname
        if __item.group != self.__groupname:
            raise ValueError
        if __item.valid:
            pass
        elif __key not in self.data:
            pass
        elif self.data[__key].valid:
            return
        return super().__setitem__(__key, __item)

    def __lt__(self, __o: "Group") -> bool:
        """For 'bisect.insort' only."""
        if not isinstance(__o, Group):
            raise TypeError
        return True if self.__groupname < __o.groupname else False

    def __get_groupname(self):
        return self.__groupname

    def __set_groupname(self, groupname: str):
        self.__groupname = groupname
        for i in self.values():
            _key: Key = i
            _key.group = groupname

    groupname = property(fget=__get_groupname, fset=__set_groupname)

    @property
    def valid(self) -> bool:
        return not self.__deleted

    @property
    def valid_keys(self) -> List[Key]:
        list_: List[Key] = []
        for i in self.values():
            _key: Key = i
            if _key.valid:
                insort(list_, _key)
        return list_

    def add_key(self, *keys: Key, force: bool = False) -> "Group":
        for _key in keys:
            if force:
                _key.group = self.__groupname
            self[_key.keyname] = _key
        return self

    def delete(self) -> "Group":
        self.__deleted = True
        return self

    def recover(self) -> "Group":
        self.__deleted = False
        return self

    def outcast(self) -> List[Key]:
        list_: List[Key] = []
        for i, j in deepcopy(self).items():
            _keyname: str = i
            _key: Key = j
            if _key.group is None:
                _key.group = self.__groupname
                continue
            if _key.group != self.__groupname:
                list_.append(self.data.pop(_keyname))
                # 'UserDict' does not have method 'pop'.
        return list_

    def aspair(self, *, valid_only: bool = True) -> Optional[Pair]:
        if self.__deleted and valid_only:
            return None
        else:
            dict_ = {}
            list_: List[Key] = []
            for i in self.values():
                _key: Key = i
                insort(list_, _key)
            for _key in list_:
                _pair = _key.aspair(valid_only=valid_only)
                if _pair is not None:
                    dict_[_pair.key] = _pair.value
            return Pair(self.__groupname, dict_)

    export: Callable = aspair

    def __repr__(self) -> str:
        if self.__deleted:
            return f"{self.groupname}(__deleted__)"
        else:
            valid_keys = self.valid_keys
            if not valid_keys:
                repr_ = (f"{self.groupname}()")
            elif len(valid_keys) <= 4:
                repr_ = (
                    f"{self.groupname}("
                    f"{TAB_}"
                    f"{SEP_.join(indent(repr(i)) for i in valid_keys)}\n)"
                )
            else:
                repr_ = (
                    f"{self.groupname}("
                    f"{TAB_}{indent(repr(valid_keys[0]))}"
                    f"{SEP_}{indent(repr(valid_keys[1]))}"
                    f"{SEP_}..."
                    f"{SEP_}{indent(repr(valid_keys[-1]))}\n)"
                )
            return repr_

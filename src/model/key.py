from bisect import insort
from collections import UserDict, UserList
from typing import Callable, Dict, Iterable, List, Optional, Union

from ..utils import indent
from ._constants import SEP_, SEP__, TAB_, TAB__, NoneType
from .pair import Pair
from .user import User

__all__ = ["Key"]


class _URLList(UserList):
    """
    Filter arguments but not raise exception when initiate or call
    method 'insort'.

    Warning:
        - attribute 'data' of '_URLList' instance is not recommended to
          access from outer scope.
    """
    def __init__(self, *urls: str) -> None:
        self.data: List[str] = []
        for i in urls:
            if isinstance(i, str):
                insort(self.data, i.rstrip("/"))

    def __setattr__(self, __name: str, __value: List[str]) -> None:
        if __name == "data":
            list_: List[str] = []
            if not isinstance(__value, list):
                raise TypeError
            for i in __value:
                if not isinstance(i, str):
                    raise TypeError
                insort(list_, i.rstrip("/"))
        else:
            raise AttributeError
        return super().__setattr__(__name, list_)

    def insort(self, url: str) -> None:
        if isinstance(url, str) and url not in self.data:
            insort(self.data, url.rstrip("/"))

    insert: Callable = insort

    def append(self, url: str) -> None:
        """Drprecated."""
        if isinstance(url, str) and url not in self.data:
            return super().append(url.rstrip("/"))

    def extend(self, other: Iterable[str]) -> None:
        """Drprecated."""
        list_: List[str] = []
        for i in other:
            if isinstance(i, str) and i not in self.data:
                list_.append(i.rstrip("/"))
        return super().extend(list_)


class _UserDict(UserDict):
    """
    Filter arguments but not raise exception when initiate.

    Warning:
        - attribute 'data' of '_UserDict' instance is not recommended to
          access from outer scope.
    """
    def __init__(self, *users: User) -> None:
        self.data: Dict[str, User] = {}
        for i in users:
            if isinstance(i, User):
                if i.valid:
                    pass
                elif i.username not in self.data:
                    pass
                elif self.data[i.username].valid:
                    continue
                self.data[i.username] = i

    def __setattr__(self, __name: str, __value: Dict[str, User]) -> None:
        if __name == "data":
            if not isinstance(__value, dict):
                raise TypeError
            for i, j in __value.items():
                if not isinstance(i, str):
                    raise TypeError
                if not isinstance(j, User):
                    raise TypeError
                if i != j.username:
                    raise ValueError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    def __getitem__(self, key: str) -> User:
        return super().__getitem__(key)

    def __setitem__(self, __key: str, __item: User) -> None:
        if not isinstance(__key, str):
            raise TypeError
        if not isinstance(__item, User):
            raise TypeError
        if __key != __item.username:
            raise ValueError
        if __item.valid:
            pass
        elif __key not in self.data:
            pass
        elif self.data[__key].valid:
            return
        return super().__setitem__(__key, __item)


class Key:

    def __init__(
        self,
        keyname: str,
        user: Optional[User] = None,
        *,
        group: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        url_list: Optional[Iterable[str]] = None,
        user_list: Optional[Iterable[User]] = None
    ) -> None:
        self.keyname: str = keyname
        self.group: Optional[str] = group
        self.description: Optional[str] = description
        list_: list = []
        if url is not None:
            list_.append(url)
        if url_list is not None:
            list_.extend(url_list)
        self.url_list: _URLList = _URLList(*list_)
        list_.clear()
        if user is not None:
            list_.append(user)
        if user_list is not None:
            list_.extend(user_list)
        self.user_dict: _UserDict = _UserDict(*list_)
        self.__deleted: bool = False

    def __setattr__(
        self,
        __name: str,
        __value: Union[str, _URLList, _UserDict, bool, NoneType]
    ) -> None:
        CLASSNAME = self.__class__.__name__
        if __name == "keyname":
            if not isinstance(__value, str):
                raise TypeError
        elif __name in ("group", "description"):
            if __value is not None and not isinstance(__value, str):
                raise TypeError
        elif __name == "url_list":
            if not isinstance(__value, _URLList):
                raise TypeError
        elif __name == "user_dict":
            if not isinstance(__value, _UserDict):
                raise TypeError
        elif __name == f"_{CLASSNAME}__deleted":
            if not isinstance(__value, bool):
                raise TypeError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    def __lt__(self, __o: "Key") -> bool:
        """For 'bisect.insort' only."""
        if not isinstance(__o, Key):
            raise TypeError
        return True if self.keyname < __o.keyname else False

    @property
    def valid(self) -> bool:
        return not self.__deleted

    @property
    def valid_users(self) -> List[User]:
        list_: List[User] = []
        for i in self.user_dict.values():
            _user: User = i
            if _user.valid:
                insort(list_, _user)
        return list_

    def add_user(self, *users: User) -> "Key":
        for _user in users:
            self.user_dict[_user.username] = _user
        return self


    def delete(self) -> "Key":
        self.__deleted = True
        return self

    def recover(self) -> "Key":
        self.__deleted = False
        return self

    def aspair(self, *, valid_only: bool = True) -> Optional[Pair]:
        if self.__deleted and valid_only:
            return None
        else:
            self.url_list.sort()
            list_: List[dict] = []
            for i in self.user_dict.values():
                _user: User = i
                _export = _user.asdict(valid_only=valid_only)
                if _export is not None:
                    list_.append(_export)
            list_.sort(key=lambda x: x["username"])
            dict_ = {
                "description": self.description,
                "url": [*self.url_list],
                "userlist": list_
            }
            return Pair(self.keyname, dict_)

    export: Callable = aspair

    def __repr__(self) -> str:
        CLASSNAME = self.__class__.__name__
        if self.__deleted:
            return f"{CLASSNAME}(__deleted__)"
        else:
            valid_users = self.valid_users
            if not valid_users:
                repr_ = (
                    f"{CLASSNAME}("
                    f"{TAB_}keyname: '{self.keyname}'"
                    f"{SEP_}userlist: []\n)"
                )
            elif len(valid_users) <= 4:
                repr_ = (
                    f"{CLASSNAME}("
                    f"{TAB_}keyname: '{self.keyname}'"
                    f"{SEP_}userlist: ["
                    f"{TAB__}"
                    f"{SEP__.join(indent(repr(i), 2) for i in valid_users)}"
                    f"{TAB_}]\n)"
                )
            else:
                repr_ = (
                    f"{CLASSNAME}("
                    f"{TAB_}keyname: '{self.keyname}'"
                    f"{SEP_}userlist: ["
                    f"{TAB__}{indent(repr(valid_users[0]), 2)}"
                    f"{SEP__}{indent(repr(valid_users[1]), 2)}"
                    f"{SEP__}..."
                    f"{SEP__}{indent(repr(valid_users[-1]), 2)}"
                    f"{TAB_}]\n)"
                )
            return repr_

from typing import Callable, Optional, Union

from ..utils import SEP_, TAB_, timestamp

NoneType = type(None)


class User:

    def __init__(
        self,
        username: str,
        password: str,
        notes: Optional[str] = None
    ) -> None:
        self.username: str = username
        self.password: str = password
        self.notes: Optional[str] = notes
        self.timestamp: Union[float, int] = timestamp()
        self.__deleted: bool = False

    def __setattr__(
        self,
        __name: str,
        __value: Union[str, float, int, bool, NoneType]
    ) -> None:
        CLASSNAME = self.__class__.__name__
        if __name in ("username", "password"):
            if not isinstance(__value, str):
                raise TypeError
            super().__setattr__("timestamp", timestamp())
        elif __name == "notes":
            if __value is not None and not isinstance(__value, str):
                raise TypeError
        elif __name == "timestamp":
            if not isinstance(__value, (float, int)):
                raise TypeError
        elif __name == f"_{CLASSNAME}__deleted":
            if not isinstance(__value, bool):
                raise TypeError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    def __lt__(self, __o: "User") -> bool:
        """For 'bisect.insort' only."""
        if not isinstance(__o, User):
            raise TypeError
        return True if self.username < __o.username else False

    @property
    def valid(self) -> bool:
        return not self.__deleted

    def delete(self) -> "User":
        self.__deleted = True
        return self

    def recover(self) -> "User":
        self.__deleted = False
        return self

    def asdict(self, *, valid_only: bool = True) -> Optional[dict]:
        if self.__deleted and valid_only:
            return None
        else:
            dict_ = {
                "username": self.username,
                "password": self.password,
                "notes": self.notes,
                "timestamp": self.timestamp
            }
            return dict_

    export: Callable = asdict

    def __repr__(self) -> str:
        CLASSNAME = self.__class__.__name__
        if self.__deleted:
            return f"{CLASSNAME}(__deleted__)"
        else:
            repr_ = (
                f"{CLASSNAME}("
                f"{TAB_}username: '{self.username}'"
                f"{SEP_}password: '{self.password}'"
                f"{SEP_}timestamp: {self.timestamp}\n)"
            )
            return repr_

from enum import Enum


class Status(Enum):

    SUCCESS = "success."
    GENERATE_SUCCESS = "success: '{password}' has been copied to the clipboard."
    FORMAT_ERROR = "error: unknown format."
    PASSWORD_ERROR = "error: incorrect username or password."
    VALUE_ERROR = "error: invalid argument."

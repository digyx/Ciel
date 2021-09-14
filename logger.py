import json
from datetime import datetime

class Logger:
    def __init__(self, ident: str):
        self.__id = str(round(datetime.now().timestamp() * 1000))
        self.__ident = ident

    def log(self, level: int, obj: dict):
        obj["logger_id"]    = self.__id
        obj["logger_ident"] = self.__ident

        match level:
            case 1:
                obj["logger_level"] = "critical"
            case 2:
                obj["logger_level"] = "error"
            case 3:
                obj["logger_level"] = "warning"
            case 4:
                obj["logger_level"] = "debug"
            case 5:
                obj["logger_level"] = "info"
            case _:
                obj["logger_level"] = "other"

        print(json.dumps(obj))

    def critical(self, obj: dict):
        self.log(1, obj)

    def error(self, obj: dict):
        self.log(2, obj)

    def warning(self, obj: dict):
        self.log(3, obj)

    def debug(self, obj: dict):
        self.log(4, obj)

    def info(self, obj: dict):
        self.log(5, obj)


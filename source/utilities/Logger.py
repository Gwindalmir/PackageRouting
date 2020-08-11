from enum import IntEnum


class Logger:
    """Logger method, for debugging"""
    class LogLevel(IntEnum):
        NONE = 0
        ERROR = 1
        WARNING = 2
        INFORMATION = 3
        VERBOSE = 4
        DEBUG = 5

        def __str__(self):
            return str(self.name)[0:1]

    class __Logger:
        def __init__(self, arg):
            super().__init__()
            self.level = arg

        def __str__(self):
            return repr(self) + self.level

        def log(self, level, message):
            if self.level >= level:
                # VS adds an extra newline in the debug window with default, manually print newline
                print(str(level) + ": " + message + "\n", end='')

        def __dump(self, obj):
            for a in dir(obj):
                val = getattr(obj, a)
                if isinstance(val, (int, float, str, list, dict, set)):
                    print(a, "=", val, "\n", end='')
                else:
                    self.__dump(val)

        def dump(self, level, obj):
            if self.level >= level:
                self.log(level, "Object dump: " + repr(obj))
                self.__dump(obj)

    # This is a class method wrapper around the instance, for readability
    @classmethod
    def log(cls, level, message):
        """Log a message at a specific level"""
        cls.instance().log(level, message)

    # This is a class method wrapper around the instance, for readability
    @classmethod
    def dump(cls, level, obj):
        """Log a message at a specific level"""
        cls.instance().dump(level, obj)

    @classmethod
    def instance(cls):
        try:
            return cls._instance
        except AttributeError:
            cls._instance = cls.__Logger(cls.LogLevel.INFORMATION)
            return cls._instance

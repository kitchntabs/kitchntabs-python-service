class Args:
    def __init__(self):
        self.keys = {}

    def set_key(self, key, value):
        self.keys[key] = value

    def get_args(self):
        return ArgsWrapper(self.keys)

class ArgsWrapper:
    def __init__(self, args_dict):
        self.__dict__.update(args_dict)

args = Args()
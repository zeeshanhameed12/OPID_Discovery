class Transition:
    def __init__(self, name, label, silent=True, properties=None):
        self.name = name
        self.label = label
        self.silent = silent
        self.properties = properties or {}
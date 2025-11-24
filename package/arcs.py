class Arc:
    def __init__(self, source, target, weight="1.0", variable=False, inscription="", properties=None, bidirectional=False):
        self.source = source
        self.target = target
        self.weight = weight
        self.variable = variable
        self.inscription = inscription
        self.properties = properties or {}
        self.bidirectional = bidirectional
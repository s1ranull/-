import copy

class Prototype:
    def clone(self, **overrides):
        obj = copy.deepcopy(self)
        for k, v in overrides.items():
            setattr(obj, k, v)
        return obj




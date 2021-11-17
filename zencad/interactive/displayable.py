class Displayable:
    def bind_to_scene(self, scene):
        raise NotImplementedError()

    def set_name(self, name):
        self._name = name
        return self

    def name(self):
        return self._name

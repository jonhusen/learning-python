"""Classes: Model for aircraft flights."""


class Flight:
    def __init__(self, number):
        self._number = number
        # Underscore avoids name clash with method of same name
        # convention - implementation details not intended for
        # consumption or manipulation prefixed by "_"

    def number(self):
        return self._number

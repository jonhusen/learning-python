"""Classes: Model for aircraft flights."""


class Flight:
    def __init__(self, number):
        if not number[:2].isalpha():
            raise ValueError(f"No airline code in '{number}'")

        if not number[:2].isupper():
            raise ValueError(f"Invalid airline code '{number}'")

        if not (number[2:].isdigit() and int(number[2:]) <= 9999):
            raise ValueError(f"Invalid route number '{number}'")

        self._number = number
        # Underscore avoids name clash with method of same name
        # convention - implementation details not intended for
        # consumption or manipulation prefixed by "_"

    def number(self):
        return self._number

    def airline(self):
        return self._number[:2]

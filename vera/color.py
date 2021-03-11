
class Color:
    @staticmethod
    def parse(s):
        if len(s) not in [6, 8, 10]:
            raise RuntimeError("Could not parse color %s" % s)
        if s[:6] != "000000":
            return RGB(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        if len(s) > 6:
            if s[6:8] != "00":
                return Warm(int(s[6:8], 16))
        if len(s) == 10:
            if s[8:10] != "00":
                return Daylight(int(s[8:10], 16))

        # All zeroes.
        return RGB(0, 0, 0)

class Daylight:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "D" + str(self.value)
    def to_hex(self):
        return "00000000%02x" % self.value

class Warm:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "W" + str(self.value)
    def to_hex(self):
        return "000000%02x00" % self.value

class RGB:
    def __init__(self, r, g, b):
        self.value = (r, g, b)
    def __str__(self):
        return "R%d,G%d,B%d" % (self.value)
    def to_hex(self):
        return "%02x%02x%02x0000" % self.value

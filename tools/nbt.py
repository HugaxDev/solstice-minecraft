"""Lecture/écriture NBT (Java, big-endian, gzip) minimale — pour éditer level.dat."""
import gzip
import struct

END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BYTE_ARRAY, STRING, LIST, COMPOUND, INT_ARRAY, LONG_ARRAY = range(13)


class Tag:
    __slots__ = ("type", "value", "list_type")

    def __init__(self, t, v, list_type=END):
        self.type, self.value, self.list_type = t, v, list_type

    def __repr__(self):
        return f"Tag({self.type}, {self.value!r})"


class Reader:
    def __init__(self, data):
        self.d, self.i = data, 0

    def take(self, n):
        b = self.d[self.i:self.i + n]
        self.i += n
        return b

    def unpack(self, fmt):
        size = struct.calcsize(fmt)
        return struct.unpack(">" + fmt, self.take(size))[0]

    def string(self):
        n = self.unpack("H")
        return self.take(n).decode("utf-8", "surrogatepass")

    def tag(self, t):
        v = self.payload(t)
        return Tag(LIST, v[0], v[1]) if t == LIST else Tag(t, v)

    def payload(self, t):
        if t == BYTE: return self.unpack("b")
        if t == SHORT: return self.unpack("h")
        if t == INT: return self.unpack("i")
        if t == LONG: return self.unpack("q")
        if t == FLOAT: return self.unpack("f")
        if t == DOUBLE: return self.unpack("d")
        if t == BYTE_ARRAY:
            n = self.unpack("i"); return bytearray(self.take(n))
        if t == STRING: return self.string()
        if t == LIST:
            lt = self.unpack("b"); n = self.unpack("i")
            return [self.tag(lt) for _ in range(n)], lt
        if t == COMPOUND:
            out = {}
            while True:
                ct = self.unpack("b")
                if ct == END:
                    return out
                name = self.string()
                out[name] = self.tag(ct)
        if t == INT_ARRAY:
            n = self.unpack("i"); return list(struct.unpack(f">{n}i", self.take(4 * n)))
        if t == LONG_ARRAY:
            n = self.unpack("i"); return list(struct.unpack(f">{n}q", self.take(8 * n)))
        raise ValueError(f"type NBT inconnu {t}")


def _w_payload(out, tag):
    t, v = tag.type, tag.value
    if t == BYTE: out += struct.pack(">b", v)
    elif t == SHORT: out += struct.pack(">h", v)
    elif t == INT: out += struct.pack(">i", v)
    elif t == LONG: out += struct.pack(">q", v)
    elif t == FLOAT: out += struct.pack(">f", v)
    elif t == DOUBLE: out += struct.pack(">d", v)
    elif t == BYTE_ARRAY: out += struct.pack(">i", len(v)) + bytes(v)
    elif t == STRING:
        b = v.encode("utf-8", "surrogatepass"); out += struct.pack(">H", len(b)) + b
    elif t == LIST:
        lt = v[0].type if v else tag.list_type
        out += struct.pack(">bi", lt, len(v))
        for item in v:
            _w_payload(out, item)
    elif t == COMPOUND:
        for name, child in v.items():
            b = name.encode("utf-8")
            out += struct.pack(">bH", child.type, len(b)) + b
            _w_payload(out, child)
        out += b"\x00"
    elif t == INT_ARRAY: out += struct.pack(f">i{len(v)}i", len(v), *v)
    elif t == LONG_ARRAY: out += struct.pack(f">i{len(v)}q", len(v), *v)


def load(path):
    with gzip.open(path, "rb") as f:
        r = Reader(f.read())
    t = r.unpack("b")
    assert t == COMPOUND
    name = r.string()
    return name, Tag(COMPOUND, r.payload(COMPOUND))


def save(path, name, root):
    out = bytearray(struct.pack(">b", COMPOUND))
    b = name.encode("utf-8")
    out += struct.pack(">H", len(b)) + b
    _w_payload(out, root)
    with gzip.open(path, "wb") as f:
        f.write(bytes(out))

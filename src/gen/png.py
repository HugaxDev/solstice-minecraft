"""Écriture de PNG RGBA en Python pur (zlib + struct), sans Pillow."""
import struct
import zlib


def write_png(path, pixels):
    """pixels : liste de lignes, chaque pixel (r, g, b, a)."""
    h = len(pixels)
    w = len(pixels[0])
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in pixels)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def read_png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", "PNG invalide"
    return struct.unpack(">II", head[16:24])


def read_png(path):
    """Lecture d’un PNG non entrelacé (niveaux de gris, RGB, palette, avec ou sans alpha ; 1 à 8 bits)
    → Canvas RGBA."""
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path} : PNG invalide"
    p, idat, plte, trns = 8, b"", None, None
    while p < len(data):
        (n,) = struct.unpack(">I", data[p:p + 4])
        tag, body = data[p + 4:p + 8], data[p + 8:p + 8 + n]
        p += 12 + n
        if tag == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif tag == b"PLTE":
            plte = body
        elif tag == b"tRNS":
            trns = body
        elif tag == b"IDAT":
            idat += body
    assert interlace == 0, f"{path} : PNG entrelacé non pris en charge"
    assert depth <= 8, f"{path} : profondeur {depth} bits non prise en charge"
    chans = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    bpp = max(1, chans * depth // 8)
    stride = (w * chans * depth + 7) // 8
    raw = zlib.decompress(idat)
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        ftype, line = raw[i], bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if ftype == 1:
                line[x] = (line[x] + a) & 255
            elif ftype == 2:
                line[x] = (line[x] + b) & 255
            elif ftype == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif ftype == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    cv = Canvas(w, h)
    for y, line in enumerate(rows):
        if depth < 8:
            per = 8 // depth
            vals = [(line[k // per] >> (8 - depth * (k % per + 1))) & ((1 << depth) - 1) for k in range(w)]
        else:
            vals = line
        for x in range(w):
            if ctype == 3:
                k = vals[x]
                alpha = trns[k] if trns and k < len(trns) else 255
                cv.px[y][x] = (plte[3 * k], plte[3 * k + 1], plte[3 * k + 2], alpha)
            elif ctype == 6:
                cv.px[y][x] = tuple(vals[4 * x:4 * x + 4])
            elif ctype == 2:
                cv.px[y][x] = (*vals[3 * x:3 * x + 3], 255)
            elif ctype == 4:
                g, alpha = vals[2 * x:2 * x + 2]
                cv.px[y][x] = (g, g, g, alpha)
            else:
                g = vals[x] * 255 // ((1 << depth) - 1)
                cv.px[y][x] = (g, g, g, 255)
    return cv


class Canvas:
    def __init__(self, w, h, bg=(0, 0, 0, 0)):
        self.w, self.h = w, h
        self.px = [[bg for _ in range(w)] for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def get(self, x, y):
        return self.px[y][x]

    def polygon(self, pts, c):
        for y in range(self.h):
            for x in range(self.w):
                if _inside(x + 0.5, y + 0.5, pts):
                    self.px[y][x] = c

    def outline(self, c):
        """Contour 1 px autour des pixels opaques."""
        mask = [[self.px[y][x][3] > 0 for x in range(self.w)] for y in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                if mask[y][x]:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if not (0 <= nx < self.w and 0 <= ny < self.h) or not mask[ny][nx]:
                            self.px[y][x] = c
                            break

    def save(self, path):
        write_png(path, self.px)


def _inside(x, y, pts):
    n, inside = len(pts), False
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def shade(c, f):
    r, g, b, a = c
    if f >= 1:
        return (min(255, int(r + (255 - r) * (f - 1))), min(255, int(g + (255 - g) * (f - 1))),
                min(255, int(b + (255 - b) * (f - 1))), a)
    return (int(r * f), int(g * f), int(b * f), a)

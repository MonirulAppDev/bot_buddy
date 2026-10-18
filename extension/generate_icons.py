import struct
import zlib
import os

def create_png(width, height, color):
    # color: (R, G, B, A)
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0) # filter type none
        for x in range(width):
            # draw simple rounded robot border
            cx, cy = width / 2, height / 2
            dist = ((x - cx)**2 + (y - cy)**2)**0.5
            if dist < width / 2:
                raw_data.extend(color)
            else:
                raw_data.extend((0, 0, 0, 0))
    
    def chunk(tag, data):
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data))

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw_data)
    
    return header + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")

os.makedirs("icons", exist_ok=True)
# Indigo color (79, 70, 229, 255)
for size in [16, 48, 128]:
    with open(f"icons/icon{size}.png", "wb") as f:
        f.write(create_png(size, size, (79, 70, 229, 255)))
print("Icons created successfully!")

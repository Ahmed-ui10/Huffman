import struct
from huffman_compression import OTHERS_SYMBOL

class BitReader:
    def __init__(self, file_handle):
        self.f = file_handle
        self.buffer = 0
        self.count = 0

    def read_bit(self):
        if self.count == 0:
            data = self.f.read(1)
            if not data:
                return None
            self.buffer = data[0]
            self.count = 8
        self.count -= 1
        return (self.buffer >> self.count) & 1

    def read_int(self, num_bits):
        value = 0
        for _ in range(num_bits):
            b = self.read_bit()
            if b is None:
                raise EOFError("Unexpected end of bitstream")
            value = (value << 1) | b
        return value


def decompress_file(input_path, output_path):
    with open(input_path, "rb") as f:
        magic = f.read(4)
        if magic != b"MHUF":
            raise ValueError("Not a Modified Huffman file (bad magic)")

        original_len = struct.unpack("<I", f.read(4))[0]
        threshold = struct.unpack("<f", f.read(4))[0]
        num_syms = struct.unpack("<I", f.read(4))[0]

        if original_len == 0:
            with open(output_path, "w", encoding="utf-8") as out:
                out.write("")
            return [], ""

        code_table = {}
        for _ in range(num_syms):
            sym_code = struct.unpack("<I", f.read(4))[0]
            code_len = struct.unpack("<B", f.read(1))[0]
            code = f.read(code_len).decode('ascii')
            if sym_code == 0xFFFFFFFF:
                symbol = OTHERS_SYMBOL
            else:
                symbol = chr(sym_code)
            code_table[code] = symbol

        num_others = struct.unpack("<I", f.read(4))[0]
        others_symbols = []
        for _ in range(num_others):
            c = struct.unpack("<I", f.read(4))[0]
            others_symbols.append(chr(c))

        br = BitReader(f)
        result = []
        max_code_len = max(len(c) for c in code_table.keys())
        current = ""
        while len(result) < original_len:
            bit = br.read_bit()
            if bit is None:
                break
            current += '1' if bit else '0'

            if current in code_table:
                sym = code_table[current]
                if sym == OTHERS_SYMBOL:
                    ascii_val = br.read_int(8)
                    result.append(chr(ascii_val))
                else:
                    result.append(sym)
                current = ""

            if len(current) > max_code_len:
                raise ValueError(f"Invalid bitstream: code too long ({current})")

    text = "".join(result)
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(text)

    tags = [(code, sym) for code, sym in code_table.items()]
    return tags, text
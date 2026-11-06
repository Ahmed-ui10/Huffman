import struct
from collections import Counter
import heapq

class BitWriter:
    def __init__(self, file_handle):
        self.f = file_handle
        self.buffer = 0
        self.count = 0

    def write_bit(self, bit):
        self.buffer = (self.buffer << 1) | (bit & 1)
        self.count += 1
        if self.count == 8:
            self.f.write(bytes([self.buffer]))
            self.buffer = 0
            self.count = 0

    def write_bits(self, bits_str):
        for ch in bits_str:
            self.write_bit(int(ch))

    def write_int(self, value, num_bits):
        for i in range(num_bits - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    def flush(self):
        if self.count > 0:
            self.buffer = self.buffer << (8 - self.count)
            self.f.write(bytes([self.buffer]))
            self.buffer = 0
            self.count = 0


class Node:
    def __init__(self, symbol=None, freq=0, left=None, right=None):
        self.symbol = symbol
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other):
        if self.freq == other.freq:
            return (self.symbol or '') < (other.symbol or '')
        return self.freq < other.freq


def _build_huffman_tree(freq_map):
    heap = []
    for sym, freq in freq_map.items():
        heapq.heappush(heap, Node(symbol=sym, freq=freq))

    if len(heap) == 1:
        only = heapq.heappop(heap)
        return Node(symbol=None, freq=only.freq, left=only, right=None)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(symbol=None,
                      freq=left.freq + right.freq,
                      left=left, right=right)
        heapq.heappush(heap, merged)

    return heap[0]


def _generate_codes(node, prefix="", code_map=None):
    if code_map is None:
        code_map = {}

    if node is None:
        return code_map

    if node.left is None and node.right is None:
        if prefix == "":
            prefix = "0"
        code_map[node.symbol] = prefix
        return code_map

    if node.left is not None:
        _generate_codes(node.left, prefix + "0", code_map)
    if node.right is not None:
        _generate_codes(node.right, prefix + "1", code_map)

    return code_map


OTHERS_SYMBOL = "\x00OTHERS\x00"

def _build_modified_huffman(original_freq, threshold, total):
    freq_map = {}
    others_symbols = []

    for sym, count in original_freq.items():
        prob = count / total
        if prob <= threshold:
            others_symbols.append(sym)
        else:
            freq_map[sym] = count

    if others_symbols:
        others_count = sum(original_freq[s] for s in others_symbols)
        freq_map[OTHERS_SYMBOL] = others_count

    if not freq_map:
        raise ValueError("Threshold too high: no symbols left to code")

    root = _build_huffman_tree(freq_map)
    huffman_codes = _generate_codes(root)

    return huffman_codes, others_symbols, root

def _generate_tree_gui_data(node, total):
    if node is None:
        return None
    
    prob = node.freq / total if total > 0 else 0
    
    data = {
        "freq": node.freq,
        "prob": prob, 
        "symbol": node.symbol if node.symbol != OTHERS_SYMBOL else "<Others>",
        "children": []
    }
    
    if node.left:
        data["children"].append(("0", _generate_tree_gui_data(node.left, total)))
    if node.right:
        data["children"].append(("1", _generate_tree_gui_data(node.right, total)))
        
    return data


def compress_file(input_path, output_path, threshold=0.05):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    if not text:
        with open(output_path, "wb") as out:
            out.write(b"MHUF")
            out.write(struct.pack("<I", 0))
            out.write(struct.pack("<f", threshold))
            out.write(struct.pack("<I", 0))
            out.write(struct.pack("<I", 0))
        return {}, [], 0, None

    total = len(text)
    freq = Counter(text)

    huffman_codes, others_symbols, root = _build_modified_huffman(
        freq, threshold, total
    )
    
    tree_data = _generate_tree_gui_data(root, total)
    
    others_set = set(others_symbols)
    others_code = huffman_codes.get(OTHERS_SYMBOL, None)

    with open(output_path, "wb") as out:
        out.write(b"MHUF")
        out.write(struct.pack("<I", total))
        out.write(struct.pack("<f", threshold))

        huff_syms = list(huffman_codes.keys())
        out.write(struct.pack("<I", len(huff_syms)))

        for sym in huff_syms:
            code = huffman_codes[sym]
            if sym == OTHERS_SYMBOL:
                sym_code = 0xFFFFFFFF
            else:
                sym_code = ord(sym)
            out.write(struct.pack("<I", sym_code))
            out.write(struct.pack("<B", len(code)))
            out.write(code.encode('ascii'))

        out.write(struct.pack("<I", len(others_symbols)))
        for sym in others_symbols:
            out.write(struct.pack("<I", ord(sym)))

        bw = BitWriter(out)
        for ch in text:
            if ch in others_set:
                bw.write_bits(others_code)
                bw.write_int(ord(ch), 8)
            else:
                bw.write_bits(huffman_codes[ch])
        bw.flush()

    return huffman_codes, others_symbols, total, tree_data
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox, scrolledtext
import os
import math
from collections import Counter

from huffman_compression import compress_file
from huffman_decompression import decompress_file

BG_MAIN      = "#1e1e1e"
BG_PANEL     = "#252526"
BG_TEXT      = "#1a1a1a"
FG_TEXT      = "#d4d4d4"
FG_ACCENT    = "#4ec9b0"
FG_LABEL     = "#cccccc"

BTN_COMPRESS   = "#0e7c66"
BTN_DECOMPRESS = "#0e5a8a"
BTN_CLEAR      = "#8a2c2c"
BTN_FG         = "#ffffff"


class HuffmanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Modified Huffman Compression System")
        self.root.geometry("1200x700")
        self.root.configure(bg=BG_MAIN)

        self.compressed_file = None
        self.codes = []

        top = tk.Frame(root, pady=10, bg=BG_MAIN)
        top.pack(fill="x")

        tk.Label(top, text="Threshold (Min Probability):",
                 bg=BG_MAIN, fg=FG_LABEL,
                 font=("Arial", 11, "bold")).pack(side="left", padx=(10, 5))

        self.threshold_var = tk.StringVar(value="0.05")
        tk.Entry(top, textvariable=self.threshold_var,
                 width=8, font=("Consolas", 11),
                 bg=BG_TEXT, fg=FG_ACCENT,
                 insertbackground=FG_ACCENT,
                 relief="flat").pack(side="left", padx=5)

        tk.Button(top, text="🗜️ Compress",
                  width=18, command=self.do_compress,
                  bg=BTN_COMPRESS, fg=BTN_FG,
                  activebackground="#0a5c4c",
                  activeforeground="#ffffff",
                  font=("Arial", 11, "bold"),
                  relief="flat", cursor="hand2",
                  borderwidth=0).pack(side="left", padx=5)

        tk.Button(top, text="📤 Decompress",
                  width=18, command=self.do_decompress,
                  bg=BTN_DECOMPRESS, fg=BTN_FG,
                  activebackground="#0a4066",
                  activeforeground="#ffffff",
                  font=("Arial", 11, "bold"),
                  relief="flat", cursor="hand2",
                  borderwidth=0).pack(side="left", padx=5)

        tk.Button(top, text="🧹 Clear",
                  width=12, command=self.clear_all,
                  bg=BTN_CLEAR, fg=BTN_FG,
                  activebackground="#661f1f",
                  activeforeground="#ffffff",
                  font=("Arial", 11, "bold"),
                  relief="flat", cursor="hand2",
                  borderwidth=0).pack(side="left", padx=5)

        mid = tk.Frame(root, bg=BG_MAIN)
        mid.pack(fill="both", expand=True, padx=10, pady=5)
        mid.columnconfigure(0, weight=1)
        mid.columnconfigure(1, weight=1)
        mid.rowconfigure(0, weight=1)

        left = tk.Frame(mid, bg=BG_PANEL, bd=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        tk.Label(left, text="  Huffman Data:",
                 anchor="w", bg=BG_PANEL, fg=FG_LABEL,
                 font=("Arial", 12, "bold"),
                 pady=6).pack(fill="x")

        self.notebook = ttk.Notebook(left)
        self.notebook.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        tab_codes = tk.Frame(self.notebook, bg=BG_TEXT)
        self.codes_area = scrolledtext.ScrolledText(
            tab_codes, height=20,
            font=("Consolas", 10),
            bg=BG_TEXT, fg=FG_TEXT,
            insertbackground=FG_ACCENT,
            selectbackground="#264f78",
            relief="flat", borderwidth=0,
            padx=8, pady=8)
        self.codes_area.pack(fill="both", expand=True)
        self.notebook.add(tab_codes, text="Code Table")

        tab_tree = tk.Frame(self.notebook, bg=BG_TEXT)
        self.tree_canvas = tk.Canvas(
            tab_tree, bg=BG_TEXT, highlightthickness=0
        )
        self.tree_canvas.pack(fill="both", expand=True)
        self.notebook.add(tab_tree, text="Huffman Tree")

        right = tk.Frame(mid, bg=BG_PANEL, bd=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        tk.Label(right, text="  Statistics:",
                 anchor="w", bg=BG_PANEL, fg=FG_LABEL,
                 font=("Arial", 12, "bold"),
                 pady=6).pack(fill="x")

        self.stats_area = scrolledtext.ScrolledText(
            right, height=20,
            font=("Consolas", 10),
            bg=BG_TEXT, fg=FG_ACCENT,
            insertbackground=FG_ACCENT,
            selectbackground="#264f78",
            relief="flat", borderwidth=0,
            padx=8, pady=8)
        self.stats_area.pack(fill="both", expand=True, padx=4, pady=(0, 4))

    def _entropy(self, text):
        if not text:
            return 0.0
        total = len(text)
        counts = Counter(text)
        H = 0.0
        for c in counts.values():
            p = c / total
            H -= p * math.log2(p)
        return H

    def draw_tree(self, tree_data):
        self.tree_canvas.delete("all")
        if not tree_data:
            return

        def get_depth(node):
            if not node: return 0
            if not node["children"]: return 1
            return 1 + max(get_depth(c[1]) for c in node["children"])
        
        depth = get_depth(tree_data)
        
        self.tree_canvas.update_idletasks()
        W = self.tree_canvas.winfo_width()
        H = self.tree_canvas.winfo_height()
        if W < 100: W = 600
        if H < 100: H = 500

        level_height = H / (depth + 1) 
        node_radius = max(12, min(25, 150 // (2**max(0, depth-2)))) 

        def draw_node(node, x, y, width, depth_level):
            self.tree_canvas.create_oval(
                x - node_radius, y - node_radius,
                x + node_radius, y + node_radius,
                fill="#2d2d2d", outline=FG_ACCENT, width=2
            )
            
            label = ""
            if node["symbol"]:
                sym = node["symbol"]
                if len(sym) > 6: sym = sym[:4] + ".."
                label = f"{sym}\n({node['freq']})"
            else:
                label = f"{node['freq']}"
                
            self.tree_canvas.create_text(
                x, y, text=label, fill=FG_LABEL, 
                font=("Arial", max(7, int(node_radius/1.5)), "bold"),
                justify="center"
            )

            if node["children"]:
                num_children = len(node["children"])
                if num_children == 1:
                    child_x = x
                    child_y = y + level_height
                    self.tree_canvas.create_line(x, y + node_radius, child_x, child_y - node_radius, fill="#888888", width=2)
                    draw_node(node["children"][0][1], child_x, child_y, width/2, depth_level+1)
                else:
                    for i, (edge_label, child) in enumerate(node["children"]):
                        cx = x - width/4 if i == 0 else x + width/4
                        cy = y + level_height
                        
                        self.tree_canvas.create_line(
                            x, y + node_radius, cx, cy - node_radius,
                            fill="#888888", width=2
                        )
                        
                        mid_x = (x + cx) / 2
                        mid_y = (y + cy) / 2
                        self.tree_canvas.create_text(
                            mid_x, mid_y, text=edge_label, fill="#ff5c5c",
                            font=("Arial", 10, "bold")
                        )
                        
                        draw_node(child, cx, cy, width/2, depth_level+1)

        draw_node(tree_data, W/2, level_height/2 + 30, W, 0)

    def do_compress(self):
        try:
            threshold = float(self.threshold_var.get())
            if not (0 < threshold < 1):
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Threshold", "Enter a number between 0 and 1.")
            return

        input_path = filedialog.askopenfilename(
            title="Select a text file to compress",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not input_path:
            return

        default_name = os.path.splitext(os.path.basename(input_path))[0] + ".mh"
        save_path = filedialog.asksaveasfilename(
            title="Save compressed file",
            defaultextension=".mh",
            initialfile=default_name,
            filetypes=[("Modified Huffman files", "*.mh"), ("All files", "*.*")]
        )
        if not save_path:
            return

        try:
            codes, others, total, tree_data = compress_file(input_path, save_path, threshold)
        except Exception as e:
            messagebox.showerror("Error", f"Compression failed:\n{e}")
            return

        self.compressed_file = save_path
        self.codes = codes

        self.codes_area.delete("1.0", tk.END)
        for sym, code in codes.items():
            if sym.startswith("\x00OTHERS"):
                display = "<OTHERS>"
            else:
                display = f"'{sym}'"
            self.codes_area.insert(tk.END, f"{display:>10}  →  {code}\n")

        if others:
            self.codes_area.insert(tk.END, "\n--- Symbols in 'Others' ---\n")
            for s in others:
                self.codes_area.insert(tk.END, f"'{s}' ")

        self.draw_tree(tree_data)

        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()

        original_bits = len(text) * 8
        compressed_bits = os.path.getsize(save_path) * 8
        H = self._entropy(text)

        if compressed_bits > 0:
            ratio = original_bits / compressed_bits
            saving = (1 - compressed_bits / original_bits) * 100
        else:
            ratio = 0
            saving = 0

        stats = (
            "=======================================\n"
            "     Modified Huffman Statistics\n"
            "=======================================\n"
            f"Original Size       : {original_bits} bits\n"
            f"Compressed Size     : {compressed_bits} bits\n"
            f"Original Chars      : {len(text)}\n"
            f"Threshold           : {threshold}\n"
            f"Entropy             : {H:.4f} bits/symbol\n"
            f"Compression Ratio   : {ratio:.3f}:1\n"
            f"Space Saving        : {saving:.2f}%\n"
            f"Huffman Codes       : {len(codes)}\n"
            f"Symbols in Others   : {len(others)}\n\n"
            f"✅ Compressed file saved at:\n{save_path}\n"
        )
        self.stats_area.delete("1.0", tk.END)
        self.stats_area.insert(tk.END, stats)

        messagebox.showinfo("Success", "Compression completed successfully ✅")

    def do_decompress(self):
        path = filedialog.askopenfilename(
            title="Select a .mh file to decompress",
            filetypes=[("Modified Huffman files", "*.mh"), ("All files", "*.*")]
        )
        if not path:
            return

        save_path = filedialog.asksaveasfilename(
            title="Save decompressed file",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not save_path:
            return

        try:
            tags, text = decompress_file(path, save_path)
        except Exception as e:
            messagebox.showerror("Error", f"Decompression failed:\n{e}")
            return

        self.codes_area.delete("1.0", tk.END)
        for code, sym in tags:
            if sym.startswith("\x00OTHERS"):
                display = "<OTHERS>"
            else:
                display = f"'{sym}'"
            self.codes_area.insert(tk.END, f"{display:>10}  →  {code}\n")

        self.tree_canvas.delete("all")

        self.stats_area.delete("1.0", tk.END)
        self.stats_area.insert(
            tk.END,
            "=======================================\n"
            "    Decompression Statistics\n"
            "=======================================\n"
            f"Number of Codes     : {len(tags)}\n"
            f"Original Text Size  : {len(text)} chars\n\n"
            f"✅ Decompressed file saved at:\n{save_path}\n"
        )
        messagebox.showinfo("Success", "Decompression completed successfully ✅")

    def clear_all(self):
        self.compressed_file = None
        self.codes = []
        self.codes_area.delete("1.0", tk.END)
        self.stats_area.delete("1.0", tk.END)
        self.tree_canvas.delete("all")


def main():
    root = tk.Tk()
    HuffmanGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
"""
W3 Remastered Bundle Extractor
Author: Open Source Community
License: MIT
Description: Standalone extractor for The Witcher 3 (POTATO70 format),
specifically supporting Remastered (v5) and classic (v3) archives.
"""

import os
import sys
import struct
import zlib
import threading

class BundleEntry:
    def __init__(self):
        self.file_name = ""
        self.hash_bytes = b""
        self.offset = 0
        self.uncompressed_size = 0
        self.compressed_size = 0
        self.crc32 = 0
        self.compression_method = 0

def parse_bundle(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    actual_file_size = os.path.getsize(file_path)
    if actual_file_size < 32:
        raise ValueError("Invalid bundle: file size is less than 32-byte header.")
        
    with open(file_path, "rb") as f:
        header = f.read(32)
        sig = header[:8]
        if sig != b"POTATO70":
            raise ValueError(f"Invalid signature: expected 'POTATO70', got {sig!r}")
            
        something0 = struct.unpack("<I", header[20:24])[0]
        is_remastered = (something0 != 0x10003)
        
        entries = []
        if not is_remastered:
            # Classic format (v3)
            file_size, data_size, meta_size, s0, s1, s2 = struct.unpack("<IIIIII", header[8:32])
            entry_size = 320
            if meta_size % entry_size != 0:
                raise ValueError(f"Corrupt metadata size: {meta_size} not divisible by 320.")
            count = meta_size // entry_size
            f.seek(32)
            for _ in range(count):
                raw = f.read(entry_size)
                if len(raw) < entry_size:
                    raise ValueError("Truncated bundle: reached EOF while reading metadata.")
                e = BundleEntry()
                e.file_name = raw[:256].split(b"\x00")[0].decode("utf-8", errors="replace")
                e.hash_bytes = raw[256:272]
                e.uncompressed_size = struct.unpack("<I", raw[276:280])[0]
                e.compressed_size = struct.unpack("<I", raw[280:284])[0]
                e.offset = struct.unpack("<I", raw[284:288])[0]
                e.crc32 = struct.unpack("<I", raw[312:316])[0]
                e.compression_method = struct.unpack("<I", raw[316:320])[0]
                entries.append(e)
        else:
            # Remastered format (v5)
            file_size = struct.unpack("<Q", header[8:16])[0]
            meta_size = struct.unpack("<I", header[16:20])[0]
            entry_size = 304
            if meta_size % entry_size != 0:
                raise ValueError(f"Corrupt metadata size: {meta_size} not divisible by 304.")
            count = meta_size // entry_size
            f.seek(32)
            for _ in range(count):
                raw = f.read(entry_size)
                if len(raw) < entry_size:
                    raise ValueError("Truncated bundle: reached EOF while reading metadata.")
                e = BundleEntry()
                e.file_name = raw[:256].split(b"\x00")[0].decode("utf-8", errors="replace")
                e.hash_bytes = raw[256:272]
                e.offset = struct.unpack("<Q", raw[272:280])[0]
                e.uncompressed_size = struct.unpack("<I", raw[280:284])[0]
                e.compressed_size = struct.unpack("<I", raw[284:288])[0]
                e.crc32 = struct.unpack("<I", raw[288:292])[0]
                e.compression_method = struct.unpack("<I", raw[292:296])[0]
                entries.append(e)
                
    return is_remastered, actual_file_size, entries

def extract_bundle(bundle_path, output_dir, progress_callback=None, log_callback=None):
    if log_callback is None:
        log_callback = lambda msg: None
    if progress_callback is None:
        progress_callback = lambda current, total: None
        
    is_remastered, file_size, entries = parse_bundle(bundle_path)
    fmt_str = "POTATO70 v5 (Remastered, 64-bit offsets)" if is_remastered else "POTATO70 v3 (Classic)"
    log_callback(f"Format: {fmt_str}")
    log_callback(f"Bundle size: {file_size:,} bytes")
    log_callback(f"Detected files: {len(entries)}")
    
    os.makedirs(output_dir, exist_ok=True)
    abs_out_dir = os.path.abspath(output_dir)
    
    success_count = 0
    error_count = 0
    total_entries = len(entries)
    
    with open(bundle_path, "rb") as f:
        for idx, entry in enumerate(entries, 1):
            clean_name = entry.file_name.replace("/", os.sep).replace("\\", os.sep)
            # Path traversal prevention
            clean_name = os.path.normpath(clean_name).lstrip(os.sep)
            if clean_name.startswith(".."):
                log_callback(f"[ERROR] Path traversal detected: {entry.file_name}")
                error_count += 1
                progress_callback(idx, total_entries)
                continue
                
            target_path = os.path.abspath(os.path.join(abs_out_dir, clean_name))
            if not target_path.startswith(abs_out_dir):
                log_callback(f"[ERROR] Target path outside destination: {clean_name}")
                error_count += 1
                progress_callback(idx, total_entries)
                continue
                
            # Boundary validation
            if entry.offset + entry.compressed_size > file_size:
                log_callback(f"[ERROR] Offset out of bounds for {clean_name} (offset: {entry.offset:,}, size: {entry.compressed_size:,})")
                error_count += 1
                progress_callback(idx, total_entries)
                continue
                
            f.seek(entry.offset)
            raw_data = f.read(entry.compressed_size)
            if len(raw_data) != entry.compressed_size:
                log_callback(f"[ERROR] Truncated read for {clean_name}")
                error_count += 1
                progress_callback(idx, total_entries)
                continue
                
            # Decompression
            try:
                if entry.compression_method == 0:
                    uncompressed_data = raw_data
                elif entry.compression_method == 1:
                    uncompressed_data = zlib.decompress(raw_data)
                else:
                    log_callback(f"[ERROR] Unknown compression method {entry.compression_method} on {clean_name}")
                    error_count += 1
                    progress_callback(idx, total_entries)
                    continue
            except zlib.error as ze:
                log_callback(f"[ERROR] Corrupt zlib stream on {clean_name}: {ze}")
                error_count += 1
                progress_callback(idx, total_entries)
                continue
                
            if len(uncompressed_data) != entry.uncompressed_size:
                log_callback(f"[ERROR] Decompressed size mismatch on {clean_name} ({len(uncompressed_data)} != {entry.uncompressed_size})")
                error_count += 1
                progress_callback(idx, total_entries)
                continue
                
            # CRC32 verification
            calc_crc = zlib.crc32(uncompressed_data)
            if calc_crc != entry.crc32:
                log_callback(f"[ERROR] CRC32 mismatch on {clean_name} (expected 0x{entry.crc32:08x}, got 0x{calc_crc:08x})")
                error_count += 1
                progress_callback(idx, total_entries)
                continue
                
            # Write out file preserving directory structure
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "wb") as out_f:
                out_f.write(uncompressed_data)
                
            success_count += 1
            if idx <= 5 or idx % 25 == 0 or idx == total_entries:
                log_callback(f"[{idx}/{total_entries}] Extracted: {clean_name} ({entry.uncompressed_size:,} bytes, CRC: 0x{entry.crc32:08x}) OK")
                
            progress_callback(idx, total_entries)
            
    log_callback("----------------------------------------")
    log_callback(f"Extraction completed. Success: {success_count} | Errors: {error_count}")
    return success_count, error_count

def run_cli(bundle_file, output_dir):
    print(f"=== W3 Remastered Bundle Extractor ===")
    print(f"Input bundle: {bundle_file}")
    print(f"Output folder: {output_dir}")
    try:
        success, errors = extract_bundle(
            bundle_file, 
            output_dir,
            progress_callback=lambda c, t: print(f"Progress: {c}/{t} ({(c/t)*100:.1f}%)", end="\r"),
            log_callback=print
        )
        print()
        if errors > 0:
            print(f"Completed with {errors} error(s).")
            return 1
        print("Success: All files extracted and verified.")
        return 0
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        return 1

def run_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from tkinter.scrolledtext import ScrolledText
    
    root = tk.Tk()
    root.title("W3 Remastered Bundle Extractor")
    root.geometry("740x560")
    root.minsize(640, 480)
    
    bundle_path_var = tk.StringVar()
    output_dir_var = tk.StringVar()
    status_var = tk.StringVar(value="Ready. Select a bundle file and destination folder.")
    info_var = tk.StringVar(value="No bundle loaded.")
    
    # Header frame
    header_frame = ttk.Frame(root, padding="10 10 10 5")
    header_frame.pack(fill=tk.X)
    
    title_label = ttk.Label(header_frame, text="W3 Remastered Bundle Extractor", font=("Segoe UI", 14, "bold"))
    title_label.pack(anchor=tk.W)
    sub_label = ttk.Label(header_frame, text="Standalone unpacker for The Witcher 3 (POTATO70 Remastered & Classic)", font=("Segoe UI", 9))
    sub_label.pack(anchor=tk.W)
    
    # Input selection frame
    files_frame = ttk.LabelFrame(root, text="Configuration", padding="10")
    files_frame.pack(fill=tk.X, padx=10, pady=5)
    
    # Bundle row
    ttk.Label(files_frame, text="Bundle File:").grid(row=0, column=0, sticky=tk.W, pady=4)
    bundle_entry = ttk.Entry(files_frame, textvariable=bundle_path_var, width=58)
    bundle_entry.grid(row=0, column=1, padx=5, pady=4, sticky=tk.EW)
    
    def on_browse_bundle():
        file_selected = filedialog.askopenfilename(
            title="Open Witcher 3 Bundle File",
            filetypes=[
                ("Witcher 3 Bundles (*.bundle;*.bundle.txt)", "*.bundle;*.bundle.txt"),
                ("All Files (*.*)", "*.*")
            ]
        )
        if file_selected:
            bundle_path_var.set(file_selected)
            if not output_dir_var.get():
                default_out = os.path.join(os.path.dirname(file_selected), "extracted_" + os.path.splitext(os.path.basename(file_selected))[0])
                output_dir_var.set(default_out)
            update_bundle_info(file_selected)

    ttk.Button(files_frame, text="Open Bundle...", command=on_browse_bundle).grid(row=0, column=2, padx=5, pady=4)
    
    # Output row
    ttk.Label(files_frame, text="Output Folder:").grid(row=1, column=0, sticky=tk.W, pady=4)
    out_entry = ttk.Entry(files_frame, textvariable=output_dir_var, width=58)
    out_entry.grid(row=1, column=1, padx=5, pady=4, sticky=tk.EW)
    
    def on_browse_output():
        folder_selected = filedialog.askdirectory(title="Select Destination Folder")
        if folder_selected:
            output_dir_var.set(folder_selected)
            
    ttk.Button(files_frame, text="Browse...", command=on_browse_output).grid(row=1, column=2, padx=5, pady=4)
    files_frame.columnconfigure(1, weight=1)
    
    # Info badge
    info_frame = ttk.Frame(root, padding="10 2 10 5")
    info_frame.pack(fill=tk.X)
    info_lbl = ttk.Label(info_frame, textvariable=info_var, font=("Segoe UI", 9, "italic"), foreground="#0055aa")
    info_lbl.pack(anchor=tk.W)
    
    # Action buttons and progress
    action_frame = ttk.Frame(root, padding="10 5")
    action_frame.pack(fill=tk.X)
    
    progress_bar = ttk.Progressbar(action_frame, orient=tk.HORIZONTAL, mode='determinate')
    progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    
    extract_btn = ttk.Button(action_frame, text="Extract All")
    extract_btn.pack(side=tk.RIGHT)
    
    # Log area
    log_frame = ttk.LabelFrame(root, text="Log Console", padding="5")
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    log_box = ScrolledText(log_frame, wrap=tk.WORD, font=("Consolas", 9), height=14)
    log_box.pack(fill=tk.BOTH, expand=True)
    
    # Status bar
    status_bar = ttk.Label(root, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W, padding="5 2")
    status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def append_log(msg):
        log_box.insert(tk.END, msg + "\n")
        log_box.see(tk.END)
        
    def update_bundle_info(path):
        try:
            is_remastered, file_size, entries = parse_bundle(path)
            fmt = "Remastered (v5, 304B entries, 64-bit offsets)" if is_remastered else "Classic (v3, 320B entries)"
            info_var.set(f"Detected: {fmt} | {len(entries)} files | Archive size: {file_size:,} bytes")
            append_log(f"[INFO] Analyzed {os.path.basename(path)}: {fmt}, {len(entries)} files found.")
        except Exception as e:
            info_var.set(f"Error inspecting bundle: {e}")
            append_log(f"[ERROR] {e}")
            
    def do_extract():
        bundle_file = bundle_path_var.get().strip()
        out_dir = output_dir_var.get().strip()
        if not bundle_file or not os.path.isfile(bundle_file):
            messagebox.showerror("Error", "Please select a valid .bundle file.")
            return
        if not out_dir:
            messagebox.showerror("Error", "Please specify an output folder.")
            return
            
        extract_btn.config(state=tk.DISABLED)
        progress_bar['value'] = 0
        status_var.set("Extracting...")
        append_log(f"\n--- Starting extraction from: {bundle_file} ---")
        
        def worker():
            def prog_cb(c, t):
                root.after(0, lambda: progress_bar.configure(maximum=t, value=c))
                root.after(0, lambda: status_var.set(f"Extracting {c}/{t} files ({(c/t)*100:.1f}%)..."))
                
            def log_cb(msg):
                root.after(0, lambda: append_log(msg))
                
            try:
                success, errors = extract_bundle(bundle_file, out_dir, progress_callback=prog_cb, log_callback=log_cb)
                if errors == 0:
                    root.after(0, lambda: status_var.set(f"Success! {success} files extracted with verified CRC32."))
                    root.after(0, lambda: messagebox.showinfo("Success", f"Successfully extracted all {success} files!\n\nAll CRC32 checks passed."))
                else:
                    root.after(0, lambda: status_var.set(f"Finished with {errors} error(s). {success} succeeded."))
                    root.after(0, lambda: messagebox.showwarning("Warning", f"Extraction finished with {errors} error(s).\nCheck the log for details."))
            except Exception as ex:
                root.after(0, lambda: append_log(f"[FATAL ERROR] {ex}"))
                root.after(0, lambda: status_var.set("Extraction failed."))
                root.after(0, lambda: messagebox.showerror("Fatal Error", str(ex)))
            finally:
                root.after(0, lambda: extract_btn.config(state=tk.NORMAL))
                
        threading.Thread(target=worker, daemon=True).start()
        
    extract_btn.config(command=do_extract)
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        import ctypes
        ctypes.windll.kernel32.AttachConsole(-1)
        if sys.argv[1] in ("-h", "--help"):
            print("\nUsage:")
            print("  W3RemasteredBundleExtractor.exe [bundle_path] [output_dir]")
            print("  If no arguments are provided, the graphical user interface (GUI) will launch.")
            sys.exit(0)
        elif len(sys.argv) >= 3:
            code = run_cli(sys.argv[1], sys.argv[2])
            sys.exit(code)
        else:
            print("\nInvalid arguments. Use --help for usage or run without arguments for GUI.")
            sys.exit(1)
    else:
        run_gui()

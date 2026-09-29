# W3 Remastered Bundle Extractor

Standalone unpacker and GUI extractor for **The Witcher 3: Wild Hunt — Remastered** (Next-Gen) and classic `.bundle` archive files (`POTATO70` format).

---

## Features

- **POTATO70 v5 (Remastered / Next-Gen) Support**: Fully compatible with modern 64-bit offsets, 304-byte metadata entries, and 16-byte alignment.
- **POTATO70 v3 (Classic) Backward Compatibility**: Supports older 32-bit offset bundles (320-byte entries) — Experimental / Unverified: Compatibility code is included, but this format has not yet been validated against a known classic bundle.
- **Integrity Verification**: Automatic CRC-32 checksum calculation and verification for every extracted file.
- **Safety Validations**:
  - Signature validation (`POTATO70`)
  - Bounds and truncated file checking
  - Path traversal protection (directory escape prevention)
  - Zlib stream error handling and corruption detection
  - Unsupported compression method alerts
- **Intuitive GUI**: Easy-to-use graphical interface with progress bar, log console, and archive inspector.
- **CLI Mode**: Fully automatable via command line for scripts and batch processing.
- **Zero Dependencies**: Standalone `.exe` requires no Python installation.

---

## Usage

### 1. Graphical Interface (GUI)

Double-click `W3RemasteredBundleExtractor.exe`:

1. Click **Open Bundle...** and select your target `.bundle` file (e.g., `xml.bundle`).
2. The extractor will automatically inspect the bundle, show the format version, archive size, and total file count.
3. Click **Browse...** to choose an output directory.
4. Click **Extract All** to unpack all assets while preserving the original directory structure.

---

### 2. Command Line Interface (CLI)

```bash
W3RemasteredBundleExtractor.exe <path_to_bundle> <output_directory>
```

#### Example:
```bash
W3RemasteredBundleExtractor.exe "C:\Games\The Witcher 3\content\content0\bundles\xml.bundle" "C:\Extracted_XML"
```

---

## Building from Source

If you wish to build the standalone executable yourself:

```bash
pip install -r requirements.txt
pyinstaller --onefile --noconsole --name W3RemasteredBundleExtractor main.py
```

---

## License

This project is licensed under the [MIT License](LICENSE).

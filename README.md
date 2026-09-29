# W3 Remastered Bundle Extractor

Standalone unpacker and GUI extractor for **The Witcher 3: Wild Hunt — Remastered / Next-Gen** `.bundle` archive files (`POTATO70` format), with experimental support for Classic bundles.

---

## Downloads

- **Nexus Mods:** https://www.nexusmods.com/witcher3/mods/13054
- **GitHub Releases:** https://github.com/doc-haz/W3RemasteredBundleExtractor/releases

---

## Features

- **POTATO70 v5 (Remastered / Next-Gen) Support**: Fully compatible with modern 64-bit offsets, 304-byte metadata entries, and 16-byte alignment.
- **POTATO70 v3 (Classic) Backward Compatibility**: Support for older 32-bit offset bundles (320-byte entries) is included, but is currently **experimental / unverified** and has not yet been validated against a known Classic bundle.
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
2. The extractor will automatically inspect the bundle and display the detected format version, archive size, and total file count.
3. Click **Browse...** to choose an output directory.
4. Click **Extract All** to unpack all files while preserving the original directory structure.
5. CRC-32 checks are automatically performed during extraction to verify file integrity.

---

### 2. Command Line Interface (CLI)

```bash
W3RemasteredBundleExtractor.exe <path_to_bundle> <output_directory>
```

#### Example

```bash
W3RemasteredBundleExtractor.exe "C:\Games\The Witcher 3\content\content0\bundles\xml.bundle" "C:\Extracted_XML"
```

---

## Tested

POTATO70 v5 (Remastered / Next-Gen) has been successfully tested against a real `xml.bundle` archive from **The Witcher 3: Wild Hunt — Remastered / Next-Gen**.

Test results:

- **224 files detected**
- **224 files extracted**
- **224 CRC-32 checks passed**
- **0 extraction errors**

> **Note:** POTATO70 v3 Classic support is currently **experimental / unverified**. Compatibility code is included, but the format has not yet been validated against a known Classic bundle.

---

## Building from Source

If you wish to build the standalone executable yourself:

```bash
pip install -r requirements.txt
pyinstaller --onefile --noconsole --name W3RemasteredBundleExtractor main.py
```

The generated executable will be available in the `dist` directory.

---

## Source Code

The complete source code is available in this repository.

Bug reports, compatibility reports, and testing feedback are welcome, particularly from users with **POTATO70 v3 Classic** bundles.

---

## License

This project is licensed under the [MIT License](LICENSE).

No game files or copyrighted CD Projekt RED assets are included with this project.

---

## Author

**DocHaz**

- GitHub: https://github.com/doc-haz
- Nexus Mods: https://www.nexusmods.com/witcher3/mods/13054

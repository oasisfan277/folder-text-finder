# Folder Text Finder

Folder Text Finder is an NVDA add-on for searching files containing text in the folder currently open in Windows File Explorer.

The add-on is designed for precise local searching. It can search for exact fragments, whole words, punctuation, repeated spaces, tabs, and line breaks. Results are presented in an accessible dialog with file, line, column, preview text, and page number when reliable page information is available.

## Privacy

Folder Text Finder performs all searching locally on the user's computer.

- No file contents are uploaded.
- No search queries are transmitted over the Internet.
- No cloud services or online APIs are used.
- No telemetry or usage statistics are collected.
- No document contents are stored after the search completes.

All text extraction and searching is performed on the local machine.

## Default Gesture

The default gesture is:

`NVDA+Alt+F`

The gesture can be changed from NVDA's Input Gestures dialog.

## Supported Files

The first version targets files with extractable text, including:

- TXT, LOG, MD, CSV, INI
- JSON, XML, HTML, HTM
- CSS, JavaScript, Python
- DOCX
- RTF
- ODT
- Text-based PDF files when a local PDF text extraction library is available

Image-only or scanned PDFs are not OCR'd.

## Search Modes

- Exact fragment search
- Whole-word search
- Case-sensitive or case-insensitive search
- Include subfolders
- File type filtering

Exact fragment search matches the query literally, including punctuation, symbols, spaces, repeated spaces, tabs, line breaks, blank lines, partial words, and parts of file paths.

## Search Statistics

After each search, the results dialog offers a Search Statistics report. It lists the search folder, search mode, duration, number of matches, number of searched files, unsupported files, unreadable files, and files without extractable text.

## Project Status

This repository contains the initial add-on scaffold and core local search engine. It is not yet ready for NVDA Add-on Store submission.


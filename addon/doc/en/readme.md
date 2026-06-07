# Folder Text Finder

Folder Text Finder searches files containing text in the folder currently open in Windows File Explorer.

## Privacy and Security

All searches are conducted locally on your computer. No files, search terms, document contents, file names, or statistics are uploaded or processed online. The add-on does not use cloud services, online APIs, telemetry, or analytics.

The Search Statistics report is generated locally and remains available only until another search is started or the add-on is closed.

## Command

Press `NVDA+Alt+F` to open Folder Text Finder from File Explorer. The command can be changed in NVDA's Input Gestures dialog.

## Searching

The search field accepts ordinary text. Exact fragment search matches what you enter literally, including punctuation, repeated spaces, tabs, and line breaks.

By default, the search field uses standard keyboard navigation:

- Space inserts a space.
- Tab moves to the next control.
- Shift+Tab moves to the previous control.
- Enter starts the search.

An advanced setting will allow direct entry of tabs and line breaks in the search field.

## Results

Results include the file name, full path, line number, column number, matching text preview, and page number when reliable page information is available.

Page numbers are reported when available. The add-on does not estimate or invent page numbers.

## Supported Files

Folder Text Finder searches common files with extractable text, including plain text, source code, markup files, DOCX, RTF, ODT, and text-based PDF documents when local PDF text extraction support is available.

Image-only or scanned PDFs are not OCR'd.

## Search Statistics

After a search, use Search Statistics to review what was searched, skipped, unsupported, unreadable, or found to contain no extractable text.


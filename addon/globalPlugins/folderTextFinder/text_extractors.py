from __future__ import annotations

import html
import re
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree


PLAIN_TEXT_EXTENSIONS = {
	".txt",
	".log",
	".md",
	".csv",
	".ini",
	".json",
	".xml",
	".css",
	".js",
	".py",
}


@dataclass(frozen=True)
class ExtractedText:
	text: str
	page_offsets: tuple[tuple[int, int], ...] = ()

	def page_for_offset(self, offset: int) -> int | None:
		for page, page_offset in reversed(self.page_offsets):
			if offset >= page_offset:
				return page
		return None


class TextExtractionError(Exception):
	def __init__(self, reason: str, message: str):
		super().__init__(message)
		self.reason = reason
		self.message = message


def extract_text(path: Path) -> ExtractedText:
	extension = path.suffix.lower()
	if extension in PLAIN_TEXT_EXTENSIONS:
		return extract_plain_text(path)
	if extension in {".html", ".htm"}:
		return ExtractedText(visible_html_text(read_text_file(path)))
	if extension == ".docx":
		return extract_docx(path)
	if extension == ".rtf":
		return ExtractedText(rtf_to_text(read_text_file(path)))
	if extension == ".odt":
		return extract_odt(path)
	if extension == ".pdf":
		return extract_pdf(path)
	raise TextExtractionError("unsupported", "Unsupported file type.")


def extract_plain_text(path: Path) -> ExtractedText:
	return ExtractedText(read_text_file(path))


def read_text_file(path: Path) -> str:
	for encoding in ("utf-8-sig", "utf-16", "cp1252"):
		try:
			text = path.read_text(encoding=encoding)
			if text:
				return text
		except UnicodeError:
			continue
	if path.stat().st_size == 0:
		raise TextExtractionError("empty", "File is empty.")
	return path.read_text(encoding="utf-8", errors="replace")


def extract_docx(path: Path) -> ExtractedText:
	try:
		with zipfile.ZipFile(path) as archive:
			xml = archive.read("word/document.xml")
	except KeyError as exc:
		raise TextExtractionError("empty", "DOCX document text was not found.") from exc
	except zipfile.BadZipFile as exc:
		raise TextExtractionError("unreadable", "DOCX file is not a valid zip document.") from exc
	root = ElementTree.fromstring(xml)
	namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
	paragraphs = []
	for paragraph in root.findall(".//w:p", namespace):
		parts = []
		for node in paragraph.iter():
			tag = node.tag.rsplit("}", 1)[-1]
			if tag == "t" and node.text:
				parts.append(node.text)
			elif tag == "tab":
				parts.append("\t")
			elif tag == "br":
				parts.append("\n")
		paragraphs.append("".join(parts))
	text = "\n".join(paragraphs)
	if not text.strip():
		raise TextExtractionError("empty", "No extractable text found.")
	return ExtractedText(text)


def extract_odt(path: Path) -> ExtractedText:
	try:
		with zipfile.ZipFile(path) as archive:
			xml = archive.read("content.xml")
	except KeyError as exc:
		raise TextExtractionError("empty", "ODT document text was not found.") from exc
	except zipfile.BadZipFile as exc:
		raise TextExtractionError("unreadable", "ODT file is not a valid zip document.") from exc
	root = ElementTree.fromstring(xml)
	paragraphs = []
	for element in root.iter():
		if element.text:
			paragraphs.append(element.text)
	text = "\n".join(part.strip() for part in paragraphs if part.strip())
	if not text:
		raise TextExtractionError("empty", "No extractable text found.")
	return ExtractedText(text)


def extract_pdf(path: Path) -> ExtractedText:
	try:
		from pypdf import PdfReader
	except Exception as exc:
		raise TextExtractionError("unsupported", "PDF text extraction is not available in this installation.") from exc
	try:
		reader = PdfReader(str(path))
		parts = []
		page_offsets = []
		for index, page in enumerate(reader.pages, start=1):
			page_offsets.append((index, sum(len(part) for part in parts)))
			parts.append(page.extract_text() or "")
			parts.append("\n")
	except Exception as exc:
		raise TextExtractionError("unreadable", f"PDF could not be read: {exc}") from exc
	text = "".join(parts)
	if not text.strip():
		raise TextExtractionError("empty", "No extractable text found.")
	return ExtractedText(text, tuple(page_offsets))


class VisibleTextHTMLParser(HTMLParser):
	def __init__(self):
		super().__init__()
		self.parts: list[str] = []
		self.skip_depth = 0

	def handle_starttag(self, tag, attrs):
		if tag in {"script", "style"}:
			self.skip_depth += 1
		if tag in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
			self.parts.append("\n")

	def handle_endtag(self, tag):
		if tag in {"script", "style"} and self.skip_depth:
			self.skip_depth -= 1
		if tag in {"p", "div", "li", "tr"}:
			self.parts.append("\n")

	def handle_data(self, data):
		if not self.skip_depth:
			self.parts.append(data)

	def text(self):
		return html.unescape("".join(self.parts))


def visible_html_text(source: str) -> str:
	parser = VisibleTextHTMLParser()
	parser.feed(source)
	text = parser.text()
	if not text.strip():
		raise TextExtractionError("empty", "No visible text found.")
	return text


def rtf_to_text(source: str) -> str:
	source = re.sub(r"\\par[d]?", "\n", source)
	source = re.sub(r"\\tab", "\t", source)
	source = re.sub(r"\\'[0-9a-fA-F]{2}", "", source)
	source = re.sub(r"\\[a-zA-Z]+\d* ?", "", source)
	source = source.replace("{", "").replace("}", "")
	text = source.strip()
	if not text:
		raise TextExtractionError("empty", "No extractable text found.")
	return text


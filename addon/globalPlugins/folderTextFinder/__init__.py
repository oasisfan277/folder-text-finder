import os
import subprocess
import threading
from pathlib import Path

try:
	import globalPluginHandler
	import gui
	import scriptHandler
	import ui
	import wx
except ModuleNotFoundError:
	class _BaseGlobalPlugin:
		pass

	class _GlobalPluginHandler:
		GlobalPlugin = _BaseGlobalPlugin

	class _ScriptHandler:
		@staticmethod
		def script(**kwargs):
			def decorator(func):
				return func
			return decorator

	class _UI:
		@staticmethod
		def message(text):
			return None

	class _Dialog:
		pass

	class _WX:
		Dialog = _Dialog

	globalPluginHandler = _GlobalPluginHandler()
	gui = None
	scriptHandler = _ScriptHandler()
	ui = _UI()
	wx = _WX()

from .search_engine import SearchOptions, Searcher


try:
	_
except NameError:
	_ = lambda text: text


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Folder Text Finder")

	@scriptHandler.script(
		description=_("Search files containing text in the current File Explorer folder"),
		gesture="kb:NVDA+alt+f",
	)
	def script_openFolderTextFinder(self, gesture):
		folder = get_current_explorer_folder()
		if not folder:
			ui.message(_("Open a folder in File Explorer before using Folder Text Finder."))
			return
		wx.CallAfter(FolderTextFinderDialog, gui.mainFrame, folder)


def get_current_explorer_folder():
	try:
		import api

		obj = api.getForegroundObject()
		location = getattr(obj, "location", None)
		if location and os.path.isdir(location):
			return location
		name = getattr(obj, "name", None)
		if name and os.path.isdir(name):
			return name
	except Exception:
		pass
	return None


class FolderTextFinderDialog(wx.Dialog):
	def __init__(self, parent, folder):
		super().__init__(parent, title=_("Folder Text Finder"))
		self.folder = folder
		self.results = []
		self.statistics = None
		self._build()
		self.CentreOnScreen()
		self.Show()

	def _build(self):
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		mainSizer.Add(wx.StaticText(self, label=_("Folder: {folder}").format(folder=self.folder)), 0, wx.ALL, 8)

		mainSizer.Add(wx.StaticText(self, label=_("&Search text:")), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		self.queryCtrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
		mainSizer.Add(self.queryCtrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		self.wholeWordCtrl = wx.CheckBox(self, label=_("&Whole word search"))
		self.caseCtrl = wx.CheckBox(self, label=_("&Case sensitive"))
		self.subfoldersCtrl = wx.CheckBox(self, label=_("Include &subfolders"))
		self.filterCtrl = wx.TextCtrl(self, value="*.txt;*.md;*.log;*.ini;*.csv;*.json;*.xml;*.html;*.htm;*.css;*.js;*.py;*.docx;*.rtf;*.odt;*.pdf")

		mainSizer.Add(self.wholeWordCtrl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		mainSizer.Add(self.caseCtrl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		mainSizer.Add(self.subfoldersCtrl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		mainSizer.Add(wx.StaticText(self, label=_("File name &filters:")), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
		mainSizer.Add(self.filterCtrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		self.resultsCtrl = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
		for index, label in enumerate((_("File"), _("Location"), _("Preview"))):
			self.resultsCtrl.InsertColumn(index, label)
		mainSizer.Add(self.resultsCtrl, 1, wx.EXPAND | wx.ALL, 8)

		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.searchButton = wx.Button(self, label=_("&Search"))
		self.openButton = wx.Button(self, label=_("&Open Result"))
		self.statsButton = wx.Button(self, label=_("Search &Statistics"))
		self.closeButton = wx.Button(self, wx.ID_CLOSE)
		for button in (self.searchButton, self.openButton, self.statsButton, self.closeButton):
			buttonSizer.Add(button, 0, wx.ALL, 4)
		mainSizer.Add(buttonSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

		self.SetSizer(mainSizer)
		self.SetSize((900, 650))

		self.searchButton.Bind(wx.EVT_BUTTON, self.on_search)
		self.openButton.Bind(wx.EVT_BUTTON, self.on_open_result)
		self.statsButton.Bind(wx.EVT_BUTTON, self.on_statistics)
		self.closeButton.Bind(wx.EVT_BUTTON, lambda evt: self.Destroy())
		self.resultsCtrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_open_result)

	def on_search(self, evt):
		query = self.queryCtrl.GetValue()
		if not query:
			ui.message(_("Enter text to search for."))
			return
		self.searchButton.Disable()
		self.resultsCtrl.DeleteAllItems()
		ui.message(_("Searching."))
		options = SearchOptions(
			query=query,
			whole_word=self.wholeWordCtrl.GetValue(),
			case_sensitive=self.caseCtrl.GetValue(),
			include_subfolders=self.subfoldersCtrl.GetValue(),
			file_patterns=tuple(pattern.strip() for pattern in self.filterCtrl.GetValue().split(";") if pattern.strip()),
		)
		thread = threading.Thread(target=self._run_search, args=(options,), daemon=True)
		thread.start()

	def _run_search(self, options):
		searcher = Searcher(Path(self.folder), options)
		results, statistics = searcher.search()
		wx.CallAfter(self._finish_search, results, statistics)

	def _finish_search(self, results, statistics):
		self.results = results
		self.statistics = statistics
		for result in results:
			index = self.resultsCtrl.InsertItem(self.resultsCtrl.GetItemCount(), result.path.name)
			location = result.format_location()
			self.resultsCtrl.SetItem(index, 1, location)
			self.resultsCtrl.SetItem(index, 2, result.preview)
		for column in range(3):
			self.resultsCtrl.SetColumnWidth(column, wx.LIST_AUTOSIZE_USEHEADER)
		self.searchButton.Enable()
		ui.message(statistics.summary_message())

	def on_open_result(self, evt):
		index = self.resultsCtrl.GetFirstSelected()
		if index < 0 or index >= len(self.results):
			ui.message(_("Select a result first."))
			return
		path = self.results[index].path
		try:
			os.startfile(str(path))
		except Exception:
			subprocess.Popen(["explorer.exe", "/select,", str(path)])

	def on_statistics(self, evt):
		if not self.statistics:
			ui.message(_("No search statistics are available yet."))
			return
		StatisticsDialog(self, self.statistics.to_report()).Show()


class StatisticsDialog(wx.Dialog):
	def __init__(self, parent, report):
		super().__init__(parent, title=_("Search Statistics"))
		self.report = report
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.reportCtrl = wx.TextCtrl(self, value=report, style=wx.TE_MULTILINE | wx.TE_READONLY)
		sizer.Add(self.reportCtrl, 1, wx.EXPAND | wx.ALL, 8)
		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		copyButton = wx.Button(self, label=_("&Copy Statistics to Clipboard"))
		closeButton = wx.Button(self, wx.ID_CLOSE)
		buttonSizer.Add(copyButton, 0, wx.ALL, 4)
		buttonSizer.Add(closeButton, 0, wx.ALL, 4)
		sizer.Add(buttonSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
		self.SetSizer(sizer)
		self.SetSize((750, 500))
		copyButton.Bind(wx.EVT_BUTTON, self.on_copy)
		closeButton.Bind(wx.EVT_BUTTON, lambda evt: self.Destroy())

	def on_copy(self, evt):
		if wx.TheClipboard.Open():
			wx.TheClipboard.SetData(wx.TextDataObject(self.report))
			wx.TheClipboard.Close()
			ui.message(_("Search statistics copied to clipboard."))

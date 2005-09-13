import os.path
import xml.sax


class EpiphanyFormatBookmarksParser(xml.sax.ContentHandler):
	def __init__(self, index):
		xml.sax.ContentHandler.__init__(self)
		self.chars = ""
		self.title = None
		self.href = None
		
		self.bookmarks = set()
		self.index = index


	def startElement(self, name, attrs):
		self.chars = ""
		if name == "item":
			self.title = None
			self.href = None


	def endElement(self, name):
		if name == "title":
			self.title = self.chars
		elif name == "link":
			if self.href == None:
				self.href = self.chars
		elif name == "ephy:smartlink":
			self.href = self.chars
		elif name == "item":
			# We don't want bookmarks that are themselves queries
			# such as "Search for %s"
			if (not self.href.startswith("javascript:")) and (self.href.find("%s") == -1):
				self.bookmarks.add((self.title, self.href))


	def characters(self, chars):
		self.chars = self.chars + chars

	
	def endDocument(self):
		self.bookmarks = list(self.bookmarks)
		# sort by titles (element 0 of the title,href tuple)
		self.bookmarks.sort(lambda x, y: cmp(x[0].lower(), y[0].lower()))
		for b in self.bookmarks:
			self.index.add(b[0], b)


def add_to_index(index):
	bookmarks_file_name = os.path.expanduser("~/.gnome2/epiphany/bookmarks.rdf")
	if os.path.exists(bookmarks_file_name):
		parser = xml.sax.make_parser()
		parser.setContentHandler(EpiphanyFormatBookmarksParser(index))
		parser.parse(bookmarks_file_name)

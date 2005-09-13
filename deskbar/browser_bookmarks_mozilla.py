import HTMLParser
import os
import os.path
import re


class MozillaFormatBookmarksParser(HTMLParser.HTMLParser):
	def __init__(self, index):
		HTMLParser.HTMLParser.__init__(self)
		self.chars = ""
		self.href = None
		self.bookmarks = set()
		self.index = index

	def handle_starttag(self, tag, attrs):
		tag = tag.lower()
		if tag == "a":
			self.chars = ""
			for tag, value in attrs:
				if tag.lower() == 'href':
					self.href = value

	def handle_endtag(self, tag):
		tag = tag.lower()
		if tag == "a":
			# We don't want bookmarks that are themselves queries
			# such as "Search for %s"
			if (not self.href.startswith("javascript:")) and (self.href.find("%s") == -1):
				self.bookmarks.add((self.chars, self.href))

	def handle_data(self, chars):
		self.chars = self.chars + chars
	
	
	def close(self):
		HTMLParser.HTMLParser.close(self)
		self.bookmarks = list(self.bookmarks)
		# sort by titles (element 0 of the title,href tuple)
		self.bookmarks.sort(lambda x, y: cmp(x[0].lower(), y[0].lower()))
		for b in self.bookmarks:
			self.index.add(b[0], b)


def get_firefox_bookmarks_file_name():
	try:
		firefox_dir = os.path.expanduser("~/.mozilla/firefox/")
		path_pattern = re.compile("^Path=(.*)")
		for line in file(firefox_dir + "profiles.ini"):
			match_obj = path_pattern.search(line)
			if match_obj:
				if match_obj.group(1).startswith("/"):
					return match_obj.group(1) + "/bookmarks.html"
				else:
					return firefox_dir + match_obj.group(1) + "/bookmarks.html"
	except IOError:
		pass
	return None


def get_mozilla_bookmarks_file_name():
	default_profile_dir = os.path.expanduser("~/.mozilla/default")
	if os.path.exists(default_profile_dir):
		for d in os.listdir(default_profile_dir):
			fn = os.path.join(default_profile_dir, d, "bookmarks.html")
			if os.path.exists(fn):
				return fn
	return None


def add_to_index(index, firefox_or_mozilla):
	if firefox_or_mozilla == "firefox":
		bookmarks_file_name = get_firefox_bookmarks_file_name()
	elif firefox_or_mozilla == "mozilla":
		bookmarks_file_name = get_mozilla_bookmarks_file_name()
	else:
		bookmarks_file_name = None
	
	if bookmarks_file_name and os.path.exists(bookmarks_file_name):
		p = MozillaFormatBookmarksParser(index)
		p.feed(file(bookmarks_file_name).read())
		p.close()

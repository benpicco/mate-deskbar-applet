import os, cgi, os.path, deskbar, deskbar.Match, deskbar.Handler
import gnomevfs, gtk

from gettext import gettext as _
import xml.dom.minidom, urllib

GCONF_DELICIOUS_USER  = deskbar.GCONF_DIR+"/desklicious/user"

DEFAULT_QUERY_TAG = 'http://del.icio.us/rss/%s/%s'
QUERY_DELAY = 1

def _check_requirements():
	#We need user and password
	if not deskbar.GCONF_CLIENT.get_string(GCONF_DELICIOUS_USER):
		return (deskbar.Handler.HANDLER_HAS_REQUIREMENTS, _("You need to configure your deli.icio.us account."), _on_config_account)
	else:
		return (deskbar.Handler.HANDLER_IS_CONFIGURABLE, _("You can modify your deli.icio.us account."), _on_config_account)

HANDLERS = {
	"DeliciousHandler" : {
		"name": _("del.icio.us Bookmarks"),
		"description": _("Search your del.icio.us bookmarks by tag name"),
		"requirements" : _check_requirements
	}
}

def _on_config_account(dialog):
	dialog = gtk.Dialog(_("del.icio.us Account"), dialog,
				gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
				(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
				gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
	
	table = gtk.Table(rows=2, columns=2)
	
	table.attach(gtk.Label(_("Enter your deli.icio.us username and password below")), 0, 2, 0, 1)

	user_entry = gtk.Entry()
	user_entry.set_text(deskbar.GCONF_CLIENT.get_string(GCONF_DELICIOUS_USER))
	table.attach(gtk.Label(_("Username: ")), 0, 1, 1, 2)
	table.attach(user_entry, 1, 2, 1, 2)
	
	table.show_all()
	dialog.vbox.add(table)
	
	response = dialog.run()
	dialog.destroy()
	
	if response == gtk.RESPONSE_ACCEPT and user_entry.get_text() != "":
		deskbar.GCONF_CLIENT.set_string(GCONF_DELICIOUS_USER, user_entry.get_text())

class DeliciousMatch(deskbar.Match.Match):	
	def __init__(self, handler, url=None, tags=None, author=None, **args):
		deskbar.Match.Match.__init__ (self, handler, **args)
		self.url = url
		self.tags = tags
		self.author = author
		
	def get_verb(self):
		return "<b>%(name)s</b>\n<span size='small' foreground='grey'>%(tags)s</span>"
	
	def get_name(self, text=None):
		return {
			"name": cgi.escape(self.name),
			"tags": cgi.escape(' '.join(self.tags)),
		}
		
	def action(self, text=None):
		gnomevfs.url_show(self.url)

	def get_category(self):
		return "web"

	def get_hash(self, text=None):
		return self.url
		
class DeliciousHandler(deskbar.Handler.AsyncHandler):
	def __init__(self):
		deskbar.Handler.AsyncHandler.__init__ (self, "delicious.png")
		self._delicious = DeliciousTagQueryEngine(self)

	def query(self, tag):
		#Hey man, calm down and query once a time :P
		self.check_query_changed (timeout=QUERY_DELAY)
		
		# Yes, the google and yahoo search might take a long time
		# and of course deliciuos too !!! ... better check if we're still valid	
		self.check_query_changed ()
		
		#The queryyyyYyyYy :)
		print "Asking del.icio.us tags for %s" % tag
		posts = self._delicious.get_posts_by_tag(tag)

		self.check_query_changed (timeout=QUERY_DELAY)
		print 'Returning del.icio.us result', posts
		
		return posts

class DeliciousTagQueryEngine:	
	def __init__(self, handler):
		"""We need use the globals DELICIOUS_USER and DELICIOUS_PASS"""
		self.handler = handler
		
		self._user = deskbar.GCONF_CLIENT.get_string(GCONF_DELICIOUS_USER)
			
		deskbar.GCONF_CLIENT.notify_add(GCONF_DELICIOUS_USER, lambda x, y, z, a: self.on_username_change(z.value))
		
	def on_username_change(self, value):
		if value != None and value.type == gconf.VALUE_STRING:
			self._user = value.get_string()
			
	def get_posts_by_tag(self, tag):
		#Get the info from del.icio.us and parse
		url = DEFAULT_QUERY_TAG % (urllib.quote_plus(self._user), urllib.quote_plus(tag))

		stream = urllib.urlopen(url)
		dom = xml.dom.minidom.parse(stream)
		stream.close()
		
		#And return the results
		posts=[]
		for item in dom.getElementsByTagName("item"):
			posts.append(
				DeliciousMatch(self.handler,
					name=item.getElementsByTagName("title")[0].firstChild.nodeValue,
					url=item.getElementsByTagName("link")[0].firstChild.nodeValue,
					tags=item.getElementsByTagName("dc:subject")[0].firstChild.nodeValue.split(" "),
					author=item.getElementsByTagName("dc:creator")[0].firstChild.nodeValue))
		
		return posts


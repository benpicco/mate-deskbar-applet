import deskbar
import handler_address_book
import handler_browser_bookmarks
import handler_file_system
import handler_gtk_bookmarks
import handler_prefix
import handler_web_site
import os
import shutil


default_handler = None
handlers = []
configurable_handlers = []
handler_names_to_handlers = {}

# the file system handler is treated specially, since it "swallows" anything
# starting with "/" and "~" -- other handlers do not get to see them.
file_system_handler = handler_file_system.Handler()


def add_handler(handler):
	handlers.append(handler)
	handler_names_to_handlers[handler.name()] = handler

	
def load_handlers():
	default_handler = None
	handlers[:] = []
	configurable_handlers[:] = []
	handler_names_to_handlers.clear()
	handler_names_to_handlers[file_system_handler.name()] = file_system_handler
	
	add_handler(handler_web_site.Handler())
	add_handler(handler_address_book.Handler())
	add_handler(handler_browser_bookmarks.Handler())
	add_handler(handler_gtk_bookmarks.Handler())
	add_handler(handler_prefix.Handler("?", "Search your computer (using Beagle)|Search your computer for %s (using Beagle)", "best --show-window|best --show-window \"%s\"", "beagle"))
	add_handler(handler_prefix.Handler("\\", "Search for files by name|Search for files named %s", "gnome-search-tool|gnome-search-tool --named=\"%s\" --start", "gnome-searchtool"))
	
	# set up the default config files, if they don't already exist
	try:
		if not os.path.exists(deskbar.USER_DIR + "engines.txt"):
			shutil.copyfile(deskbar.SHARED_DATA_DIR + "default-engines.txt", deskbar.USER_DIR + "engines.txt")
			shutil.copyfile(deskbar.SHARED_DATA_DIR + "default-engine-prefix.txt", deskbar.USER_DIR + "default-engine.txt")
	except IOError:
		pass
	
	# load the list of handlers out of the config file
	load_configurable_handlers(deskbar.USER_DIR + "engines.txt")
	
	# set default prefix handler
	try:
		for line in file(deskbar.USER_DIR + "default-engine.txt"):
			line = line.strip()
			if len(line) > 0:
				set_default_handler_by_prefix(line)
				break
	except IOError:
		pass


def load_configurable_handlers(filename):
	abbreviation = None
	description = None
	try:
		for line in file(filename):
			line = line.strip()
			if len(line) > 0:
				if abbreviation == None:
					abbreviation = line
				elif description == None:
					description = line
				else:
					command = line
					h = handler_prefix.Handler(abbreviation, description, command)
					configurable_handlers.append(h)
					add_handler(h)
					abbreviation = None
					description = None
	except IOError:
		pass


def set_default_handler_by_prefix(prefix):
	for h in handlers:
		try:
			if h.prefix == prefix:
				global default_handler
				default_handler = h
				return
		except AttributeError:
			# some Handlers don't have a "prefix"
			pass
	default_handler = None


def add_to_completions(text, completions, icon_container):
	text = text.strip()
	if len(text) == 0:
		icon_container.set_icon(deskbar.DESKBAR_IMAGE)
	else:
		handler_icon = None
		if file_system_handler.can_handle(text):
			handler_icon = file_system_handler.add_to_completions(text, completions, handler_icon)
		else:
			for h in handlers:
				handler_icon = h.add_to_completions(text, completions, handler_icon)
			if default_handler != None:
				handler_icon = default_handler.add_to_completions(
					text, completions, handler_icon, False)
		if handler_icon == None:
			handler_icon = deskbar.DESKBAR_IMAGE
		icon_container.set_icon(handler_icon)


def handle(text):
	if file_system_handler.can_handle(text):
		file_system_handler.handle(text)
	else:
		for h in handlers:
			if h.can_handle(text):
				h.handle(text)
				return
		if default_handler != None:
			default_handler.handle(text)


def handle_with_specific_handler(text, handler_name):
	if handler_name.startswith(deskbar.NO_CHECK_CAN_HANDLE):
		check_can_handle = False
		handler_name = handler_name[len(deskbar.NO_CHECK_CAN_HANDLE):]
	else:
		check_can_handle = True
	
	handler = handler_names_to_handlers[handler_name]
	if handler != None:
		handler.handle(text, check_can_handle)
	

load_handlers()

import deskbar
import deskbar.indexer


address_book_index = deskbar.indexer.Index()


def add_to_index(address):
	at_index = address.find("@")
	if at_index != -1:
		key = address[:at_index]
	else:
		key = address
	address_book_index.add(key, address)


def load_address_book():
	address_book_index.clear()
	# Dummy data, since we can't read the real address book, since we don't
	# have Python bindings for evolution-data-server (as at September 2005).
	#add_to_index("William Gates III <billg@microsoft.com>")
	#add_to_index("Steve Ballmer <steve@microsoft.com>")
	#add_to_index("Bill Joy <bjoy@sun.com>")


class Handler:
	def add_to_completions(self, text, completions, handler_icon, check_can_handle=True):
		handler_name = self.name()
		for address in address_book_index.look_up(text):
			d = "E-mail <b>%s</b>" %  deskbar.escape_markup(address)
			completions.append([d, handler_name, address, deskbar.MAIL_IMAGE.get_pixbuf()])
		return handler_icon


	def name(self):
		return "Handler_Address_Book"


	def can_handle(self, text):
		return False


	def handle(self, text, check_can_handle=True):
		# TODO - actually e-mail the address
		deskbar.run_command("zenity --info --text \"E-mailing <b>%s</b> from the Wonderbar does not work yet.\"",
			deskbar.escape_markup(text))


load_address_book()

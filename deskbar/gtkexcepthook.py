import sys
import gtk, pango
from gettext import gettext as _
from cStringIO import *
import traceback

_exception_in_progress = 0

def _info(type, value, tb):
	global _exception_in_progress
	if _exception_in_progress:
		# Exceptions have piled up, so we use the default exception
		# handler for such exceptions
		_excepthook_save(type, value, tb)
		return
	_exception_in_progress = 1
	dialog = gtk.MessageDialog(parent=None,
				   flags=0,
				   type=gtk.MESSAGE_WARNING,
				   buttons=gtk.BUTTONS_CLOSE,
				   message_format=_("A programming error has been detected"))
	dialog.format_secondary_text(_("It probably isn't fatal, but should be reported"
								   " to the developers nonetheless. The program may behave erratically from now on."))
	dialog.set_title(_("Bug Detected"))
	dialog.set_default_response(gtk.RESPONSE_CLOSE)
	#dialog.set_border_width(12)
	#dialog.vbox.get_children()[0].set_spacing(12)

	# Details
	textview = gtk.TextView(); textview.show()
	textview.set_editable(False)
	textview.modify_font(pango.FontDescription("Monospace"))
	sw = gtk.ScrolledWindow(); sw.show()
	sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
	sw.add(textview)
	frame = gtk.Frame()
	frame.set_shadow_type(gtk.SHADOW_IN)
	frame.add(sw)
	frame.set_border_width(6)
	textbuffer = textview.get_buffer()
	trace = StringIO()
	traceback.print_exception(type, value, tb, None, trace)
	textbuffer.set_text(trace.getvalue())
	textview.set_size_request(gtk.gdk.screen_width()/2, gtk.gdk.screen_height()/3)
	frame.show()
	expander = gtk.Expander("Details")
	expander.add(frame)
	expander.show()
	dialog.vbox.add(expander)
	
	dialog.set_position(gtk.WIN_POS_CENTER)
	dialog.set_gravity(gtk.gdk.GRAVITY_CENTER)
	
	dialog.run()
	dialog.destroy()
	_exception_in_progress = 0
	
if not sys.stderr.isatty():
	print 'Using GTK exception handler'
	_excepthook_save = sys.excepthook
	sys.excepthook = _info

if __name__ == '__main__':
	_excepthook_save = sys.excepthook
	sys.excepthook = _info
	print x + 1

	

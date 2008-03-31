import sys
from gettext import gettext as _
from cStringIO import *
import traceback
import tempfile
import os
import logging
import threading
from os.path import basename

LOGGER = logging.getLogger(__name__)

# We don't want that errors in 3rd-party
# handlers land in bugzilla

# List of modules that will be reported
# by bug buddy if an exception occurs
BUG_BUDDY_MODULES_WHITELIST = set(
    ["beagle-live.py",
     "beagle-static.py",
     "desklicious.py",
     "epiphany.py",
     "evolution.py",
     "files.py",
     "gdmactions.py",
     "history.py",
     "iswitch-window.py",
     "mozilla.py",
     "programs.py",
     "recent.py",
     "templates.py",
     "tomboy.py",
     "web_address.py",
     "yahoo.py",]
)
    
def bug_buddy_exception(type, value, tb):
    # Shamelessly stolen from /gnome-python/examples/bug-buddy-integration.py
    # Original credit to Fernando Herrera
    msg = "".join(traceback.format_exception(type, value, tb))
    fd, name = tempfile.mkstemp()
    try:
        os.write(fd,msg)
        os.system("bug-buddy --include=\"%s\" --appname=\"%s\"" % (name, "deskbar-applet"))
    finally:
        os.unlink(name)

_exception_in_progress = 0
def _info(type, value, tb):
    global _exception_in_progress
    if _exception_in_progress:
        # Exceptions have piled up, so we use the default exception
        # handler for such exceptions
        _excepthook_save(type, value, tb)
        return
    _exception_in_progress = 1
   
    bug_buddy_exception(type, value, tb)
    
    _exception_in_progress = 0

def install_thread_excepthook():
    """
    Workaround for sys.excepthook thread bug
    (https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470).
    Call once from __main__ before creating any threads.
    If using psyco, call psyco.cannotcompile(threading.Thread.run)
    since this replaces a new-style class method.
    """
    run_old = threading.Thread.run
    def run(*args, **kwargs):
        try:
            run_old(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            type, value, tb = sys.exc_info()
            stack = traceback.extract_tb(tb)
            display_bug_buddy = True
            for (filename, line_number, function_name, text) in stack:
                # First of all, check whether the file where the exception
                # occured contains 'modules'
                if "modules" in filename:
                    # Now check whether the filename is in the whitelist
                    if not basename(filename) in BUG_BUDDY_MODULES_WHITELIST:
                        # Module is not in the whitelist
                        # just print normal stack trace and not bug buddy
                        display_bug_buddy = False
            if display_bug_buddy:
                # Display bug buddy
                sys.excepthook(type, value, tb)
            else:
                # Display normal stack trace
                _excepthook_save(type, value, tb)
    threading.Thread.run = run

if not sys.stderr.isatty():
    LOGGER.info('Using GTK exception handler')
    _excepthook_save = sys.excepthook
    sys.excepthook = _info
    install_thread_excepthook()

if __name__ == '__main__':
    _excepthook_save = sys.excepthook
    sys.excepthook = _info
    raise Exception

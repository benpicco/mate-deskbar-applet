deskbar_handlersdir = $(libdir)/deskbar-applet/handlers
deskbar_handlers_PYTHON = \
	beagle.py \
	email_address.py \
	epiphany.py \
	files.py \
	galago.py \
	galeon.py \
	gtkbookmarks.py \
	google-live.py \
	mozilla.py \
	programs.py \
	pathprograms.py \
	volumes.py \
	web_address.py

if ENABLE_BEAGLE
deskbar_handlers_PYTHON += beagle-live.py
endif

if ENABLE_EVOLUTION
deskbar_handlers_PYTHON += evolution.py
endif

EXTRA_DIST = \
	debug-blockinginit.py \
	debug-async_handler.py \
	debug-requirements.py \
	debug-signal_handler.py


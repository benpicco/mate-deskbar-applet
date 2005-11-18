deskbar_handlersdir = $(libdir)/deskbar-applet/handlers
deskbar_handlers_PYTHON = \
	beagle.py \
	email_address.py \
	epiphany.py \
	files.py \
	directories.py \
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

if ENABLE_BEAGLE
deskbar_handlers_PYTHON += evolution.py
endif

deskbar_handlers_DATA = \
	google-live-help.txt

EXTRA_DIST = \
	$(deskbar_handlers_DATA) \
	debug-blockinginit.py \
	debug-async_handler.py \
	debug-requirements.py \
	debug-signal_handler.py


from deskbar.defs import VERSION
from gettext import gettext as _
import deskbar.core.Indexer
import deskbar.core.Utils
import deskbar.interfaces.Action
import deskbar.interfaces.Match
import deskbar.interfaces.Module 
import gio
import gtk
import logging
import os
import os.path
import shutil
import subprocess

LOGGER = logging.getLogger(__name__)
HANDLERS = ["TemplateHandler"]

class TemplateFile(object):

    def __init__(self, uri):
        self.uri = uri

        basename = os.path.basename(uri)
        ext_index = basename.rfind(".")

        if ext_index >= 0:
            self.name = basename[:ext_index]
            self.extension = basename[ext_index:]
        else:
            self.name = basename
            self.extension = ""

class TemplateAction(deskbar.interfaces.Action):

    def __init__(self, template_file):
        self.template_file = template_file
        deskbar.interfaces.Action.__init__(self, template_file.name)

    def get_icon(self):
        return "gtk-new"

    def get_verb(self):
        return _("Create %s") % "<b>%(name)s</b>"

    def activate(self, text=None):
        dialog = gtk.Dialog(_("Create Document"),
                            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                       gtk.STOCK_OK, gtk.RESPONSE_OK))

        dialog.set_icon_name(gtk.STOCK_NEW)
        dialog.set_has_separator(False)
        dialog.set_default_response(gtk.RESPONSE_OK)

        table = gtk.Table(1, 2)
        table.set_border_width(5)
        table.set_row_spacings(6)
        table.set_col_spacings(12)

        filename_label = gtk.Label(_("Name:"))
        filename_label.set_alignment(0.0, 0.5)
        table.attach(filename_label, 0, 1, 0, 1, xoptions=gtk.FILL)

        filename_entry = gtk.Entry()
        table.attach(filename_entry, 1, 2, 0, 1)

        folder_label = gtk.Label(_("Folder:"))
        folder_label.set_alignment(0.0, 0.5)
        table.attach(folder_label, 0, 1, 1, 2, xoptions=gtk.FILL)

        folder_button = gtk.FileChooserButton(_("Choose Folder"))
        folder_button.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        table.attach(folder_button, 1, 2, 1, 2)

        dialog.vbox.pack_start(table)
        dialog.show_all()

        folder = deskbar.core.Utils.get_xdg_user_dir(deskbar.core.Utils.DIRECTORY_DOCUMENTS)

        if not folder:
            folder = "~"

        folder_button.set_filename(folder)

        filename = "%s%s" % (self.template_file.name, self.template_file.extension)

        if os.path.exists(os.path.join(folder, filename)):
            index = 1

            while True:
                filename = "%s (%s)%s" % (self.template_file.name, index,
                                          self.template_file.extension)
                
                if not os.path.exists(filename):
                    break
                else:
                    index += 1

        filename_entry.set_text(filename)

        selection_len = filename.rfind(".")
        if selection_len < 0:
            selection_len = len(filename)

        filename_entry.select_region(0, selection_len)

        def filename_entry_activate_cb(entry):
            dialog.response(gtk.RESPONSE_OK)

        def filename_entry_changed_cb(entry):
            dialog.set_response_sensitive(gtk.RESPONSE_OK,
                                          len(filename_entry.get_text().strip()) != 0)

        filename_entry.connect("activate", filename_entry_activate_cb)
        filename_entry.connect("changed", filename_entry_changed_cb)

        response = dialog.run()
        dialog.hide()

        if response == gtk.RESPONSE_OK:
            created_file = os.path.join(folder_button.get_filename(),
                                        filename_entry.get_text())

            if os.path.exists(created_file):
                msg_dialog = gtk.MessageDialog(flags=gtk.MESSAGE_QUESTION,
                        message_format=_("A file named \"%s\" already exists.  " \
                                         "Do you want to replace it?")
                                         % filename_entry.get_text())

                msg_dialog.format_secondary_text(_("The file already exists in \"%s\".  " \
                                                   "Replacing it will overwrite its contents.")
                                                   % os.path.basename(folder_button.get_filename()))

                msg_dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
                img = gtk.Image()
                img.set_from_stock(gtk.STOCK_SAVE_AS, gtk.ICON_SIZE_BUTTON)
                button = gtk.Button(_("Replace"))
                button.set_image(img)
                msg_dialog.add_action_widget(button, gtk.RESPONSE_ACCEPT)
                msg_dialog.set_default_response(gtk.RESPONSE_ACCEPT)       
                msg_dialog.show_all()

                response = msg_dialog.run()
                msg_dialog.destroy()

                if response != gtk.RESPONSE_ACCEPT:
                    return

            shutil.copyfile(self.template_file.uri, created_file)
            deskbar.core.Utils.url_show_file("file://%s" % created_file)

        dialog.destroy()

    def is_valid(self):
        return os.path.exists(self.template_file.uri)

class TemplateMatch(deskbar.interfaces.Match):

    def __init__(self, template_file):
        deskbar.interfaces.Match.__init__(self,
                                          name = template_file.name,
                                          category = "documents",
                                          icon = "gtk-new")
        self.template_file = template_file
        self.add_action(TemplateAction(template_file))

    def get_hash(self):
        return self.template_file.uri

class TemplateHandler(deskbar.interfaces.Module):

    INFOS = {"icon": deskbar.core.Utils.load_icon("text-x-generic-template"),
             "name": _("Templates"),
             "description": _("Create new files from your templates"),
             "version": VERSION}

    def __init__(self):
        deskbar.interfaces.Module.__init__(self)    
        self.indexer = deskbar.core.Indexer.Indexer()
        self.monitors = []

    def _add_template_file(self, path):
        template_file = TemplateFile(path)
        match = TemplateMatch(template_file)
        self.indexer.add(match.get_name(), match)
    
    def _templates_dir_monitor_cb(self, monitor, file, other_file, event_type):
        self._add_template_file(file.get_path())
 
    def _add_templates_dir(self, templates_dir):
        for f in os.listdir(templates_dir):
            # Skip backup files and hidden files
            if f.endswith("~") or f.startswith("."):
                continue
            file_path = os.path.join(templates_dir, f)
            if os.path.isdir(file_path):
                self._add_templates_dir(file_path)
            else:
                self._add_template_file(file_path)
 
    def initialize(self):
        templates_dir = deskbar.core.Utils.get_xdg_user_dir(deskbar.core.Utils.DIRECTORY_TEMPLATES)
        self._add_templates_dir(templates_dir)

        gfile = gio.File(path=templates_dir)
        try:
            filemonitor = gfile.monitor_directory()
            if filemonitor != None:
                filemonitor.connect ("changed", self._templates_dir_monitor_cb)
                self.monitors.append(filemonitor)
        except Exception, e:
            LOGGER.exception(e)

    def query(self, query):
        matches = self.indexer.look_up(query)
        self.set_priority_for_matches(matches)
        self._emit_query_ready(query, matches)

    def stop(self):
        for filemonitor in self.monitors:
            filemonitor.cancel()
            
    @staticmethod
    def has_requirements():
        # Work around bug #577649
        try:
            templates_dir = deskbar.core.Utils.get_xdg_user_dir(deskbar.core.Utils.DIRECTORY_TEMPLATES)
        except ValueError, e:
            LOGGER.exception(e)
            TemplateHandler.INSTRUCTIONS = _("Could not retrieve templates directory")
            return False

        if os.path.exists(templates_dir):
            return True
        else:
           TemplateHandler.INSTRUCTIONS = _("Templates directory %s does not exist") % templates_dir
           return False
    

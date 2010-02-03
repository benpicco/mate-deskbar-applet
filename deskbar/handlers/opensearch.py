#
#  opensearch.py : An OpenSearch module for the deskbar applet.
#
#  Copyright (C) 2008 by Arthur Perton
#  Copyright (C) 2009 by Sebastian Poelsterl
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# 
#  Authors: Arthur Perton <arthurperton at no_spam_me gmail.com>
#  1.0 : Initial release.

from deskbar.core.Utils import load_icon, get_proxy
from deskbar.defs import VERSION
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
from xml.dom import minidom
import cPickle
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import gtk
import logging
import os
import pango
import re
import urllib
import xml.parsers.expat

LOGGER = logging.getLogger(__name__)

HANDLERS = ["OpenSearchHandler"]

SETTINGS_FILE = os.path.join(deskbar.USER_DATA_DIR, "opensearch.pickle")

DEFAULT_VALUES = {'count': '15', 'startIndex': '0', 'startPage': '0'}

class OpenSearchViewResultAction(ShowUrlAction):
    def __init__(self, website, title, url):
        ShowUrlAction.__init__(self, website, url)
        self._title = title
        
    def get_name(self, text=None):
        return {
            "name": self._name,
            "title": self._title,
        }
    
    def get_verb(self):
        return "%(name)s: %(title)s"
    
    def get_tooltip(self, text=None):
        return self._title
       
class OpenSearchSearchAction(ShowUrlAction):
    def __init__(self, website, query, url):
        ShowUrlAction.__init__(self, website, url)
        self._query = query
        
    def get_name(self, text=None):
        return {"name": self._name,
                "text": self._query}
        
    def get_verb(self):
        return _("Search <b>%(name)s</b> for <i>%(text)s</i>")
    

class OpenSearchMatch(deskbar.interfaces.Match):
    def __init__(self, name=None, **args):
        deskbar.interfaces.Match.__init__(self, name=name, category="websearch", **args)

    def get_category(self):
        return "websearch"

    def get_verb(self):
        return _("Website: <b>%(name)s</b>")
                
class OpenSearchHandler(deskbar.interfaces.Module):
    
    INFOS = {
            "icon": deskbar.core.Utils.load_icon("web-search.png"),
            "name": _("OpenSearch"),
            "description": _("Searches any OpenSearch-compliant website"),
            "version": VERSION,
    }
    
    INSTRUCTIONS = _("You can configure the search engines you want to use.")
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        # 0: title
        # 1: url
        # 2: description
        # 3: url_template
        # 4: enabled?
        self.websites = []
            
    def query(self, query):
        self.load_websites()
        matches = []
        for website in self.websites:
            LOGGER.debug("Website: %s", website[0])
            
            if not website[4]:
                continue
            
            url_template = website[3]
            if url_template != None:
                LOGGER.debug("URL template: %s", url_template)
                
                url = url_template.replace("{searchTerms}", urllib.quote_plus(query))
                
                for key, val in DEFAULT_VALUES.items():
                    url = url.replace("{%s}" % key, val) # required param
                    url = url.replace("{%s?}" % key, val) # optional param
                
                # Remove unsupported parameters
                url = re.sub('&(\w+?)={[^}]*}', '', url)
                
                LOGGER.debug("URL: %s", url)
                
                try:    
                    xml_document = minidom.parse(urllib.urlopen(url, proxies=get_proxy()))
                    root_tag = xml_document.documentElement.tagName
                    
                    # atom:
                    if root_tag == "feed":
                        items = self._parse_atom(xml_document)
                    # rss:
                    elif root_tag == "rss":
                        items = self._parse_rss(xml_document)
                    else:
                        items = []
                        
                    num_results = len(items)
                    for i, (title, link) in enumerate(items):
                        # FIXME: Priority should depend on position of search engine, too
                        prio = self.get_priority() + num_results - i
                        match = OpenSearchMatch(name=website[0], priority=prio)
                        match.add_action(OpenSearchViewResultAction(website[0], title, link))
                        matches.append(match)
                    
                except Exception, e:
                    match = OpenSearchMatch(name=website[0], priority=self.get_priority())
                    match.add_action(OpenSearchSearchAction(website[0], query, url))
                    matches.append(match)
                    
        self._emit_query_ready(query, matches)
        
    def _parse_atom(self, xml_document):
        items = []
        item_nodes = xml_document.getElementsByTagName("entry")
        for item_node in item_nodes:
            title = item_node.getElementsByTagName("title")[0].firstChild.data
            link = item_node.getElementsByTagName("link")[0].getAttribute("href")
            title = xml_unescape(title)
            
            items.append((title, link,))
        
        return items
    
    def _parse_rss(self, xml_document):
        items = []
        item_nodes = xml_document.getElementsByTagName("item")
        for item_node in item_nodes:
            title = item_node.getElementsByTagName("title")[0].firstChild.data
            link = item_node.getElementsByTagName("link")[0].firstChild.data
            title = xml_unescape(title)
            
            items.append((title, link,))
        
        return items

    def has_config(self):
        return True
    
    def show_config(self, parent):
        dialog = OpenSearchSettingsDialog(parent)
        dialog.run()
        dialog.destroy()
        
    def load_websites(self):
        try:
            file = open(SETTINGS_FILE, 'rb')
        except IOError, e:
            LOGGER.exception(e)
            return
        
        try:
            try:
                self.websites = cPickle.load(file)
            except Exception, e:
                LOGGER.exception(e)
        finally:
            file.close()
    
class OpenSearchSettingsDialog(gtk.Dialog):
    
    def __init__(self, parent):
        gtk.Dialog.__init__(
                self, _("OpenSearch Settings"), parent,
                gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
                (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        
        self.set_default_size(480, 400)
        self.connect("destroy", self.on_destroy)
        
        label_instruction = gtk.Label(_("You can manage the list of websites used by the OpenSearch module here."))
        label_instruction.set_alignment(0, 0.5)
        label_instruction.set_line_wrap(True)
        self.vbox.pack_start(label_instruction, False, True)
        
        # add a hbox:        
        hbox = gtk.HBox(spacing=6)
        self.vbox.pack_start(hbox)
        
        # create a liststore for the treeview data:
        self.liststore = gtk.ListStore(str, str, str, str, bool)
        self.load_settings()

        # construct the treeview:
        self.treeview = gtk.TreeView(self.liststore)
        self.treeview.set_headers_visible(False)
        self.treeview.connect('row_activated', self.on_row_activated)
        self.treeview.get_selection().connect("changed", self.on_treeview_changed)

        self.treeview.set_rules_hint(True)

        self.cell0 = gtk.CellRendererToggle()
        self.cell0.set_property("activatable", True)
        self.cell0.connect('toggled', self.on_toggled, self.liststore)

        self.cell1 = gtk.CellRendererText()
        self.cell1.set_property("wrap-width", 300)
        self.cell1.set_property("wrap-mode", pango.WRAP_WORD)

        self.treeviewcolumn0 = gtk.TreeViewColumn('Enabled', self.cell0, active=4)
        self.treeviewcolumn1 = gtk.TreeViewColumn('Website', self.cell1)
        self.treeviewcolumn1.set_cell_data_func(self.cell1, self.set_website_text)

        self.treeview.append_column(self.treeviewcolumn0)
        self.treeview.append_column(self.treeviewcolumn1)

        # add a scrollwindow for the treeview:
        scrollwindow = gtk.ScrolledWindow()
        scrollwindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrollwindow.set_shadow_type(gtk.SHADOW_IN)
        scrollwindow.add(self.treeview)
        hbox.pack_start(scrollwindow)

        # add a vbuttonbox containing the buttons on the right:
        vbuttonbox = gtk.VButtonBox()
        vbuttonbox.set_spacing(6)
        vbuttonbox.set_layout(gtk.BUTTONBOX_START)
        hbox.pack_start(vbuttonbox, False, True)
    
        # add the buttons:
        self.add_button = gtk.Button(stock=gtk.STOCK_ADD)
        self.add_button.connect('clicked', self.on_add_button_clicked)
        vbuttonbox.pack_start(self.add_button)

        self.remove_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.remove_button.connect('clicked', self.on_remove_button_clicked)
        self.remove_button.set_sensitive(False)
        vbuttonbox.pack_start(self.remove_button)

        self.edit_button = gtk.Button(stock=gtk.STOCK_EDIT)
        self.edit_button.connect('clicked', self.on_edit_button_clicked)
        self.edit_button.set_sensitive(False)
        vbuttonbox.pack_start(self.edit_button)
        
        # show all:
        self.vbox.show_all()

    def set_website_text(self, column, cell, model, iter):
        cell.set_property('markup', "<b>%s</b>\n%s" % (model.get_value(iter, 0), model.get_value(iter, 2)))
        return

    def on_toggled(self, cell, path, model):
        iter = model.get_iter(path)
        model.set_value(iter, 4, not cell.get_active())
        return
        
    def save_settings(self):
        settings = []
        for row in self.liststore:
            setting = []
            for value in row:
                setting.append(value)
            settings.append(setting)
            
        try:
            file = open(SETTINGS_FILE, 'wb')
        except IOError, e:
            LOGGER.exception(e)
            return
        
        try: 
            try:
                cPickle.dump(settings, file)
            except Exception, e:
                LOGGER.exception(e)
        finally:
            file.close()
        
    def load_settings(self):
        if not os.path.isfile(SETTINGS_FILE):
            return False
        try:
            file = open(SETTINGS_FILE, 'rb')
        except IOError, e:
            LOGGER.exception(e)
            return False
        
        try: 
            try:
                settings = cPickle.load(file)
            except Exception, e:
                LOGGER.exception(e)
                return False
        finally:
            file.close()
        
        for setting in settings:
            self.liststore.append(setting)
        
        return True

    
    def add_website(self, info):
        self.liststore.append([info['name'], info['location'],
                               info['description'], info['url-template'],
                               True])

    def edit_website(self, info, iter = None):
        if iter == None:
            iter = self.get_selected()
        if iter != None:
            self.liststore.set(iter, 0, info['name'],
                               1, info['location'],
                               2, info['description'],
                               3, info['url-template'])

    def remove_website(self, iter):
        self.liststore.remove(iter)    

    def on_add_button_clicked(self, button):
        dialog = OpenSearchAddWebsiteDialog(self)
        if dialog.run() == gtk.RESPONSE_OK:
            self.add_website(dialog.get_info())
        dialog.destroy()
    
    def on_edit_button_clicked(self, button):
        aiter = self.get_selected()
        if aiter != None: 
            row = self.liststore[aiter]
            info = {'name': row[0],
                    'location': row[1],
                    'description': row[2],
                    'url-template': row[3]}
            dialog = OpenSearchEditWebsiteDialog(self, info)
            if dialog.run() == gtk.RESPONSE_OK:
                self.edit_website(dialog.get_info())
            dialog.destroy()
        
    def on_remove_button_clicked(self, button):
        iter = self.get_selected()
        if iter != None: 
            self.remove_website(iter)
            
    def on_row_activated(self, treeview, path, view_column):
        self.on_edit_button_clicked(None)    
    
    def on_treeview_changed(self, widget):
        sensitive = (self.get_selected() != None)
        self.remove_button.set_sensitive(sensitive)
        self.edit_button.set_sensitive(sensitive)
        return True
    
    def on_destroy(self, widget):
        self.save_settings()
        
    def get_selected(self):
        return self.treeview.get_selection().get_selected()[1]
            
class OpenSearchEditWebsiteDialog(gtk.Dialog):
    def __init__(self, parent, info):
        gtk.Dialog.__init__(
                self, self.get_title(), parent,
                gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                 gtk.STOCK_OK, gtk.RESPONSE_OK))
        
        self.info = info
        
        self.connect("response", self.on_response)

        self.set_default_size(500, -1)
        
        label_instruction = gtk.Label(_("Enter the location (URL) of the OpenSearch description document for this website. The name and description can be loaded automatically from this document or you can just enter your own values manually."))
        label_instruction.set_alignment(0, 0.5)
        label_instruction.set_line_wrap(True)
        self.vbox.pack_start(label_instruction, False, True)
        
        hbox = gtk.HBox()
        
        self.vbox.pack_start(child=hbox, padding=10)

        table = gtk.Table(rows=3, columns=3, homogeneous=False)
        table.set_col_spacings(7);
        table.set_row_spacings(7);
        hbox.pack_start(child=table, padding=10)
        
        self.entry_location = gtk.Entry()
        self.entry_location.connect('changed', self.on_entry_changed, 'location')
        
        label_location = gtk.Label(_("_Location (URL):"))
        label_location.set_use_underline(True)
        label_location.set_mnemonic_widget(self.entry_location)
        label_location.set_alignment(0, 0.5)
        
        refresh_button = gtk.Button(stock=gtk.STOCK_REFRESH)
        refresh_button.connect('clicked', self.on_refresh_button_clicked)

        table.attach(label_location, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        table.attach(self.entry_location, 1, 2, 0, 1, gtk.FILL | gtk.EXPAND, gtk.FILL)
        table.attach(refresh_button, 2, 3, 0, 1, gtk.FILL, gtk.FILL)
        
        self.entry_name = gtk.Entry()
        self.entry_name.connect('changed', self.on_entry_changed, 'name')
        
        label_name = gtk.Label(_("_Name:"))
        label_name.set_use_underline(True)
        label_name.set_mnemonic_widget(self.entry_name)
        label_name.set_alignment(0, 0.5)

        table.attach(label_name, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
        table.attach(self.entry_name, 1, 3, 1, 2, gtk.FILL | gtk.EXPAND, gtk.FILL)
        
        self.entry_description = gtk.Entry()
        self.entry_description.connect('changed', self.on_entry_changed, 'description')
        
        label_description = gtk.Label(_("_Description:"))
        label_description.set_use_underline(True)
        label_description.set_mnemonic_widget(self.entry_description)
        label_description.set_alignment(0, 0.5)
        
        table.attach(label_description, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        table.attach(self.entry_description, 1, 3, 2, 3, gtk.FILL | gtk.EXPAND, gtk.FILL)
        
        self.entry_name.set_text(self.info['name'])
        self.entry_location.set_text(self.info['location'])
        self.entry_description.set_text(self.info['description'])
        
         # show all:
        self.vbox.show_all()
            
    def get_title(self):
        return _("Edit OpenSearch Website")
    
    def get_info(self):
        return self.info

    def validate(self):
        if len(self.entry_location.get_text().strip()) < 1:
            show_message(self, _("Location missing"), _("Please enter a valid location (URL) for this website"))
            return False
        if len(self.entry_name.get_text().strip()) < 1:
            show_message(self, _("Name missing"), _("Please enter a name for this website"))
            return False
        if len(self.entry_description.get_text().strip()) < 1:
            show_message(self, _("Description missing"), _("Please enter a description for this website"))
            return False
        return True
    
    def on_entry_changed(self, entry, key):
        self.info[key] = entry.get_text()

    def on_response(self, widget, response_id):
        if response_id == gtk.RESPONSE_OK:
            if not self.validate():
                self.emit_stop_by_name("response")
    
    def get_description_document_info(self, url):
        xml_document = minidom.parse(urllib.urlopen(url, proxies=get_proxy()))
        
        self.info['name'] = xml_document.getElementsByTagName("ShortName")[0].firstChild.data
        self.info['description'] = xml_document.getElementsByTagName("Description")[0].firstChild.data
        
        url_elements = xml_document.getElementsByTagName("Url")
        url_element = None
        
        # try to find the Url for getting rss or atom results:
        for element in url_elements:
            type = element.getAttribute("type").strip()
            if type == 'application/rss+xml' or type == 'application/atom+xml':
                url_element = element
                break
        
        # if not found, pick the first Url as a default:
        if url_element == None:
            url_element = url_elements[0]
        url_template = url_element.getAttribute("template").strip()
        
        # cover for a common error in description documents:
        if url_template == '':
            url_template = url_element.firstChild.data.strip()
        if url_template != '':
            self.info['url-template'] = url_template

    def on_refresh_button_clicked(self, button):
        try:
            url = self.entry_location.get_text()
            self.get_description_document_info(url)
        except Exception, e:
            LOGGER.exception(e)
            show_message(
                    self,
                    _("Unable to load description document"),
                    _("Make sure the URL points to a valid OpenSearch description document."))
            return
           
        self.entry_name.set_text(self.info['name'])        
        self.entry_description.set_text(self.info['description'])

class OpenSearchAddWebsiteDialog(OpenSearchEditWebsiteDialog):
    
    def __init__(self, parent):
        OpenSearchEditWebsiteDialog.__init__(self, parent,
            {'name': '',
             'location': 'http://',
             'description': '',
             'url-template': None,})
    
    def get_title(self):
        return _("Add OpenSearch Website")

def show_message(parent, message, secondary_text = None):
    message_dialog = gtk.MessageDialog(
            parent, 
            gtk.DIALOG_MODAL |gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_ERROR, 
            gtk.BUTTONS_OK,
            message)
    if secondary_text != None:
        message_dialog.format_secondary_text(secondary_text)
    message_dialog.run()
    message_dialog.destroy()
    
def xml_unescape(s):
    want_unicode = False
    if isinstance(s, unicode):
        s = s.encode("utf-8")
        want_unicode = True

    # the rest of this assumes that "s" is UTF-8
    list = []

    # create and initialize a parser object
    p = xml.parsers.expat.ParserCreate("utf-8")
    p.buffer_text = True
    p.returns_unicode = want_unicode
    p.CharacterDataHandler = list.append

    # parse the data wrapped in a dummy element
    # (needed so the "document" is well-formed)
    p.Parse("<e>", 0)
    p.Parse(s, 0)
    p.Parse("</e>", 1)

    # join the extracted strings and return
    es = ""
    if want_unicode:
        es = u""
    return es.join(list)

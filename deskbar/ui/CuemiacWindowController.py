import glib
import gtk
import gtk.gdk
import logging
import deskbar
import deskbar.interfaces.Controller
import deskbar.core.Utils
from deskbar.ui.About import show_about
from deskbar.ui.preferences.DeskbarPreferences import DeskbarPreferences

LOGGER = logging.getLogger(__name__)

class CuemiacWindowController(deskbar.interfaces.Controller):
    """
    This class handels the input received from
    L{CuemiacWindowView<deskbar.ui.CuemiacWindowView.CuemiacWindowView>}
    """
    
    def __init__(self, model):
        super(CuemiacWindowController, self).__init__(model)
        self._model.connect("keybinding-activated", self.on_keybinding_activated)
        self._model.connect("initialized", self.on_core_initialized)
        self._clipboard = gtk.clipboard_get (selection="PRIMARY")
        self._focus_out = False
        
    def on_keybinding_activated(self, core, time, paste=True):
        """
        Toggle view if keybinding has been activated
        """
        # Check if we saw a focus-out-event recently
        # focus-out-event takes care of closing the window
        if not self._focus_out:
            if self._model.get_use_selection() and paste:
                text = self._clipboard.wait_for_text()
                if text != None:
                    self._view.get_entry().set_text(text)
            self._view.receive_focus(time)
        
    def on_quit(self, *args):
        if self._model.get_clear_entry():
            self._view.clear_all()
        window = self._view.get_toplevel()
        
        if self._model.get_ui_name() == deskbar.WINDOW_UI_NAME:
            x, y = window.get_position()
            self._model.set_window_x(x)
            self._model.set_window_y(y)
        
        if len(args) == 2:
            event = args[1]
            if hasattr(event, 'type'):
                if event.type == gtk.gdk.FOCUS_CHANGE:
                    # If the keybinding is pressed to close the window
                    # we receive a focus-out-event first. Now we close
                    # the window and the keybinding handler thinks it
                    # should show the window.
                    # Settings this flag will tell us
                    # that we saw a focus-out-event recently
                    self._focus_out = True
                    glib.timeout_add(250, self._reset_focus_out)
        
        window.hide()
        
        return True
    
    def _reset_focus_out(self):
        self._focus_out = False

    def on_show_about(self, sender):
        show_about(self._view.get_toplevel())
        
    def on_show_preferences(self, sender):
        prefs = DeskbarPreferences(self._model)
        prefs.show_run_hide(self._view.get_toplevel())
        
    def on_show_help(self, sender):
        deskbar.core.Utils.launch_default_for_uri_and_scheme("ghelp:deskbar")
        
    def on_query_entry_changed(self, entry):
        self._view.set_clear()
        self._model.stop_queries()
        # TODO: abort previous searches
        qstring = entry.get_text().strip()
        if (qstring != ""):
            self._view.show_results()
            self._model.query( qstring )
            
    def on_query_entry_key_press_event(self, entry, event):
        # For key UP to browse in history, we have either to be already in history mode, or have an empty text entry to trigger hist. mode
        up_history_condition = self._model.get_history().get_current() != None or (self._model.get_history().get_current() == None and entry.get_text() == "")
        # For key DOWN to browse history, we have to be already in history mode. Down cannot trigger history mode in that orient.
        down_history_condition = self._model.get_history().get_current() != None
        
        if event.keyval == gtk.keysyms.Up and up_history_condition:
            # Browse back history#
            item = self._model.get_history().up()
            if item != None:
                entry.set_history_item( item )
            return True
                
        if event.keyval == gtk.keysyms.Down and down_history_condition:
            # Browse back history
            entry.set_history_item( self._model.get_history().down() )
            return True
        
        # If the checks above fail and we come here, let's see if it's right to swallow up/down stroke
        # to avoid the entry losing focus.
        if (event.keyval == gtk.keysyms.Down or event.keyval == gtk.keysyms.Up) and entry.get_text() == "":
            return True

        return False
        
    def on_query_entry_activate(self, entry):
        path, column = self._view.cview.get_cursor ()
        model = self._view.cview.get_model()
        iter = None
        if path != None:
            iter = model.get_iter (path)

        # If we're on a history item right now and the user 
        # presses Enter, the search results for that history item
        # should be shown.
        if self._model.get_history().get_current() != None:
            # Start new query with the text from the history
            self.on_query_entry_changed(entry)
            self._model.get_history().reset()
            return
        
        if iter == None or model.iter_has_child(iter):
            # No selection, select top element
            # Only scroll to the item if the TreeView still
            # contains items after we activated the item
            self._view.cview.activate_first_item( not self._model.get_clear_entry() )
        else:
            # Activate selcted row
            self._view.cview.activate_row(iter)
        
    def on_treeview_cursor_changed(self, treeview):
        self._view.update_entry_icon ()
        
    def on_match_selected(self, treeview, text, match_obj, event):
        if len(match_obj.get_actions()) == 1:
            action = match_obj.get_actions()[0]
            self.on_action_selected(None, text, action, event)
        elif len(match_obj.get_actions()) > 1:
            self._view.display_actions(match_obj.get_actions(), text)
        else:
            raise Exception("Match has no action")
     
    def on_do_default_action(self, treeview, text, match_obj, event):
        action = match_obj.get_default_action()
        if action == None:
            action = match_obj.get_actions()[0]
        self.on_action_selected(treeview, text, action, event)
        
    def on_action_selected(self, treeview, text, action, event):
        if not action.is_valid():
            LOGGER.warning("Action is not valid anymore")
            return
        
        # Check if only the "Choose action" item is in history
        if len(self._model.get_history()) == 1:
            self._view.mark_history_empty(False)
            
        self._model.get_history().add(text, action)
        action.activate(text)
        if self._model.get_clear_entry():
            self._view.clear_all()
        if self._model.get_hide_after_action():
            self.on_quit()
        
    def on_clear_history(self, sender):
        history = self._model.get_history()
        history.clear()
        history.reset()
        history.save()
        self._view.mark_history_empty(True)
        
    def on_history_match_selected(self, history, text, action):
        action.activate(text)
        if self._model.get_hide_after_action():
            self.on_quit()
        
    def on_category_expanded(self, widget, iter, path, model):
        idx = model[iter][model.MATCHES].get_id ()
        collapsed_rows = self._model.get_collapsed_cat()
        if idx in collapsed_rows:
            collapsed_rows.remove (idx)
            self._model.set_collapsed_cat(collapsed_rows)
    
    def on_category_collapsed(self, widget, iter, path, model):
        idx = model[iter][model.MATCHES].get_id ()
        collapsed_rows = self._model.get_collapsed_cat()
        collapsed_rows.append (idx)
        self._model.set_collapsed_cat(collapsed_rows)
        
    def on_category_added (self, widget, cat, path):
        if cat.get_id() not in self._model.get_collapsed_cat():
            self._view.cview.expand_row (path, False)
            
    def on_core_initialized (self, core):
        self._view.mark_history_empty ( (len(core.get_history()) == 1) )

import gtk
import gtk.gdk
import deskbar.interfaces.Controller
import deskbar.core.Utils
from deskbar.ui.About import show_about
from deskbar.ui.preferences.DeskbarPreferences import DeskbarPreferences

class CuemiacWindowController(deskbar.interfaces.Controller):
    
    def __init__(self, model):
        super(CuemiacWindowController, self).__init__(model)
        self._model.connect("keybinding-activated", self.on_keybinding_activated)
        self._clipboard = gtk.clipboard_get (selection="PRIMARY")
        
    def on_keybinding_activated(self, core, time, paste=True):
        if self._model.get_use_selection() and paste:
            text = self._clipboard.wait_for_text()
            if text != None:
                self._view.get_entry().set_text(text)
        self._view.receive_focus(time)
        
    def on_quit(self, *args):
        self._view.get_toplevel().hide()
        return True

    def on_show_about(self, sender):
        show_about(self._view.get_toplevel())
        
    def on_toggle_history(self, sender):
        val = not self._view.is_history_visible()
        self._model.set_show_history( val )
        self._view.show_history( val )
        
    def on_show_preferences(self, sender):
        prefs = DeskbarPreferences(self._model)
        prefs.show_run_hide(self._view.get_toplevel())
        
    def on_query_entry_changed(self, entry):
        self._view.treeview_model.clear()
        self._model.stop_queries()
        # TODO: abort previous searches
        qstring = entry.get_text().strip()
        if (qstring != ""):
            self._model.query( qstring )
        else:
            self._view.treeview_model.clear()
            
    def on_query_entry_key_press_event(self, entry, event):
        # TODO: discard still running query threads
        if (event.keyval == gtk.keysyms.Escape):
            self._view.clear_all()
            return False
        
        # For key UP to browse in history, we have either to be already in history mode, or have an empty text entry to trigger hist. mode
        up_history_condition = self._model.get_history().get_current() != None or (self._model.get_history().get_current() == None and entry.get_text() == "")
        # For key DOWN to browse history, we have to be already in history mode. Down cannot trigger history mode in that orient.
        down_history_condition = self._model.get_history().get_current() != None

        if event.keyval == gtk.keysyms.Up and up_history_condition:
            # Browse back history
            entry.set_history_item( self._model.get_history().up() )
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
        
        if iter == None or model.iter_has_child(iter):
            # No selection, select top element
            iter = model.get_iter_first()
            
            while iter != None and (not (model.iter_has_child(iter) and self._view.cview.row_expanded(model.get_path(iter))) ):
                iter = model.iter_next(iter)
            if iter != None:
                iter = model.iter_children(iter)

        if iter is None:
            return
        # retrieve new path-col pair, since it might have been None to start out
        path = model.get_path (iter)
        
        column = self._view.cview.get_column (0)
        # This emits a match-selected from the cview
        self._view.cview.emit ("row-activated", path, column)
        
    def on_match_selected(self, treeview, text, match_obj, event):
        if len(match_obj.get_actions()) == 1:
            action = match_obj.get_actions()[0]
            self.on_action_selected(None, text, action, event)
        elif len(match_obj.get_actions()) > 1:
            self._view.display_actions(match_obj.get_actions(), text)
        else:
            raise Exception("Match has no action")
        
    def on_action_selected(self, treeview, text, action, event):
        self._model.get_history().add(text, action)
        
        action.activate(text)
        if self._model.get_hide_after_action():
        	self.on_quit()
        
    def on_clear_history(self, sender):
        self._model.get_history().clear()
        self._model.get_history().save()
        
    def on_history_match_selected(self, history, text, action):
        action.activate(text)
        
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
            
    def on_window_resized(self, window, event):
        self._model.set_window_width( window.allocation.width )
        self._model.set_window_height( window.allocation.height )
        
    def on_sidebar_width_changed(self, sidebar, value):
        self._model.set_sidebar_width( sidebar.get_position() )
        
    def on_resultsview_width_changed(self, results_hpaned, value):
    	self._model.set_resultsview_width( results_hpaned.get_position() )
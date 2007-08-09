import sys
import logging
import gobject
import deskbar
from deskbar.core.GconfStore import GconfStore
from deskbar.core.ModuleInstaller import ModuleInstaller
from deskbar.core.ModuleLoader import ModuleLoader
from deskbar.core.ModuleList import ModuleList, DisabledModuleList
from deskbar.core.Keybinder import Keybinder
from deskbar.core.DeskbarHistory import DeskbarHistory
from deskbar.core.ThreadPool import ThreadPool
import deskbar.interfaces

class CoreImpl(deskbar.interfaces.Core):
    
    DEFAULT_KEYBINDING = "<Alt>F3"
    
    def __init__(self, modules_dir):
        super(CoreImpl, self).__init__()
        
        self._loaded_modules = 0
        self._inited_modules = 0
        self._start_query_id = 0
        self._last_query = None
        self._stop_queries = True
        
        self._threadpool = ThreadPool(5)
        self._gconf = GconfStore.get_instance()
        self._history = DeskbarHistory.get_instance(self._gconf.get_max_history_items())
        self._gconf.connect("max-history-items-changed", lambda s, num: self._history.set_max_history_items(num))
        
        self._setup_module_loader(modules_dir)
        self._setup_module_list()
        
        self._disabled_module_list = DisabledModuleList()
        self._module_loader.connect ("module-not-initialized", self._disabled_module_list.add)
        
        self._module_installer = ModuleInstaller(self._module_loader)
        
    def run(self):
        # Ready to load modules
        self._module_loader.load_all_async()
        
        self._setup_keybinder()
        self._threadpool.start()
        
    def _setup_module_loader(self, modules_dir):
        self._module_loader = ModuleLoader( modules_dir )
        self._module_loader.connect ("modules-loaded", self.on_modules_loaded)
        self._module_loader.connect ("module-initialized", self.on_module_initialized)
    
    def _setup_module_list(self):
        self._module_list = ModuleList ()
        self._gconf.connect("enabled-modules-changed", self._on_enabled_modules_changed)
        self._module_loader.connect ("module-loaded", self._module_list.update_row_cb)
        self._module_loader.connect ("module-initialized", self._module_list.module_toggled_cb)
        self._module_loader.connect ("module-stopped", self._module_list.module_toggled_cb)
        
    def _setup_keybinder(self):
        self._keybinder = Keybinder()
        if (self.get_keybinding() == None):
            self.set_keybinding( DEFAULT_KEYBINDING )
        else:
            self.set_keybinding( self.get_keybinding() )
        self._keybinder.connect("activated", lambda k,t: self._emit_keybinding_activated(t))
    
    def get_old_modules(self):
        return self._module_loader.get_old_modules()
    
    def get_modules_dir(self):
        return self._modules_dir
    
    def get_modules(self):
        return self._module_loader.filelist
    
    def get_enabled_modules(self):
        return self._gconf.get_enabled_modules()
    
    def set_enabled_modules(self, name):
        self._gconf.set_enabled_modules(name)
    
    def get_keybinding(self):
        return self._gconf.get_keybinding()
    
    def get_min_chars(self):
        return self._gconf.get_min_chars()
    
    def get_type_delay(self):
        return self._gconf.get_type_delay()
    
    def get_use_selection(self):
        return self._gconf.get_use_selection()
    
    def get_clear_entry(self):
        return self._gconf.get_clear_entry()
    
    def get_use_http_proxy(self):
        return self._gconf.get_use_http_proxy()
    
    def get_proxy_host(self):
        return self._gconf.get_proxy_host()
    
    def get_proxy_port(self):
        return self._gconf.get_proxy_port()
    
    def get_collapsed_cat(self):
        return self._gconf.get_collapsed_cat()
    
    def get_show_history(self):
        return self._gconf.get_show_history()
    
    def get_window_width(self):
        return self._gconf.get_window_width()
    
    def get_window_height(self):
        return self._gconf.get_window_height()
    
    def get_sidebar_width(self):
        return self._gconf.get_sidebar_width()
    
    def get_resultsview_width(self):
        return self._gconf.get_resultsview_width()
    
    def get_hide_after_action(self):
        return self._gconf.get_hide_after_action()
    
    def get_max_history_items(self):
        return self._gconf.get_max_history_items()
    
    def set_keybinding(self, binding):
        self._gconf.set_keybinding(binding)
        if not self._keybinder.bind(binding):
            logging.error("Keybinding is already in use")
        else:
            logging.info("Successfully binded Deskbar to %s" % binding)
    
    def set_min_chars(self, number):
        self._gconf.set_min_chars(number)
    
    def set_type_delay(self, seconds):
        self._gconf.set_type_delay(seconds)
    
    def set_use_selection(self, val):
        self._gconf.set_use_selection(val)
    
    def set_clear_entry(self, val):
        self._gconf.set_clear_entry(val)
    
    def set_use_http_proxy(self, val):
        self._gconf.set_use_http_proxy(val)
    
    def set_proxy_host(self, host):
        self._gconf.set_proxy_host(host)
    
    def set_proxy_port(self, port):
        self._gconf.set_proxy_port(port)
    
    def set_collapsed_cat(self, cat):
        self._gconf.set_collapsed_cat(cat)
    
    def set_show_history(self, val):
        self._gconf.set_show_history(val)
    
    def set_window_width(self, width):
        self._gconf.set_window_width(width)
    
    def set_window_height(self, height):
        self._gconf.set_window_height(height)
    
    def set_sidebar_width(self, width):
        self._gconf.set_sidebar_width(width)
    
    def set_resultsview_width(self, width):
        self._gconf.set_resultsview_width(width)
    
    def set_hide_after_action(self, width):
        self._gconf.set_hide_after_action(width)
    
    def set_max_history_items(self, amount):
        self._gconf.set_max_history_items(amount)
    
    def get_history(self):
        """
        Returns History object
        
        This one is able to:
            - append
            - prepend
            - clear
        """
        return self._history
    
    def get_module_list(self):
        return self._module_list
    
    def get_disabled_module_list(self):
        return self._disabled_module_list
    
    def install_module(self, filename):
        return self._module_installer.install(filename)
    
    def uninstall_module(self, mod):
        raise NotImplementedError
    
    def stop_module(self, mod, async=True):
        if async:
            self._module_loader.stop_module_async(mod)
        else:
            self._module_loader.stop_module(mod)
        self._module_list.decrease_bottom_enabled_path()
    
    def initialize_module (self, module, async=True):
        if async:
            self._module_loader.initialize_module_async(module)
        else:
            self._module_loader.initialize_module(module)
        self._module_list.increase_bottom_enabled_path()
    
    def stop_queries(self):
        self._stop_queries = True
        self._threadpool.stop()
    
    def query(self, text):
        if (len(text) >= self.get_min_chars()):            
            if (self._start_query_id != 0):
                gobject.source_remove(self._start_query_id)
            self._start_query_id = gobject.timeout_add( self.get_type_delay(), self.query_real, text )
            self._stop_queries = False
            
    def query_real(self, text):
        self._last_query = text
        for modname in self.get_enabled_modules():
            mod = self._module_list.get_module_instance_from_name( modname )
            if mod != None:
                self._threadpool.callInThread(mod.query, text)
        
    def on_modules_loaded(self, loader, callback=None):
        enabled_list = self.get_enabled_modules()
        
        self.update_modules_priority(enabled_list)
        
        for mod in enabled_list:
            modinst = self._module_list.get_module_instance_from_name( mod )
            if modinst != None:
                self._module_loader.initialize_module_async( modinst )
                self._loaded_modules += 1
    
    def update_modules_priority(self, enabled_modules):    
        """
        module_list is a module_loader.ModuleList() with loaded modules
        enabled_modules is a list of exported classnames.
        
        Update the module priority present in both module_list and enabled_modules according
        to the ordering of enabled_modules. Optionally calls callback when != None on each
        module context, in the correct order (from important to less important)
        """
        
        # Compute the highest priority
        high_prio = (len(enabled_modules)-1)*100
        
        # Now we enable each gconf-enabled handler, and set it's priority according to gconf ordering
        for i, modname in enumerate(enabled_modules):
            mod = [mod for mod in self._module_list if mod.__class__.__name__ == modname]
            if len(mod) != 1:
                # We have a gconf handler not on disk anymore..
                continue
                
            mod = mod[0]
            mod.set_priority(high_prio-i*100)
        
        self._module_list.reorder_with_priority(enabled_modules)
        
    def on_module_initialized(self, loader, module):
        self._inited_modules += 1
        # Forward results
        module.connect ('query-ready', self.forward_query_ready)
        
        if (self._inited_modules == self._loaded_modules):
            self._history.load(self._module_list)
            self._emit_initialized()
            
    def _on_enabled_modules_changed(self, gconfstore, enabled_modules):
        # Stop all unneeded modules
        enabled_modules_set = set(enabled_modules)
        current_modules_set = set()
        for mod in self._module_list:
            if mod.is_enabled():
                if not mod.__class__.__name__ in enabled_modules:
                    self._module_loader.stop_module (mod)
                else:
                    current_modules_set.add(mod.__class__.__name__)
        
        #new_modules = enabled_modules_set - current_modules_set
        #for mod in new_modules:
            # FIXME: mod is a str but we need the class here
            #self._module_loader.initialize_module_async( mod )
        
        self.update_modules_priority(enabled_modules)
            
    def forward_query_ready(self, handler, query, matches):
        if query == self._last_query and matches != None and len(matches) > 0 and not self._stop_queries:
            self._emit_query_ready(matches)
        
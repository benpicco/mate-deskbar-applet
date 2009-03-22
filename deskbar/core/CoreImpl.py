import sys
import logging
import glib
import gtk
import deskbar
import deskbar.interfaces.Match
from deskbar.core.GconfStore import GconfStore
from deskbar.core.ModuleInstaller import ModuleInstaller
from deskbar.core.ModuleLoader import ModuleLoader
from deskbar.core.ModuleList import ModuleList, DisabledModuleList
from deskbar.core.Keybinder import Keybinder
from deskbar.core.DeskbarHistory import DeskbarHistory
from deskbar.core.ThreadPool import ThreadPool
import deskbar.interfaces

LOGGER = logging.getLogger(__name__)

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
        
        self._gconf.connect("default-browser-changed", self._on_default_browser_changed)
        #prevent double notifications
        self.browser = None
        
    def run(self):
        """
        Load modules, set keybinding and create L{deskbar.core.ThreadPool.ThreadPool}
        """
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
        self._gconf.connect("keybinding-changed", self._on_keybinding_changed)
        
        self._keybinder = Keybinder()
        keybinding = self.get_keybinding()
        if (keybinding == None or gtk.accelerator_parse(keybinding) == (0,0)):
            # Keybinding is not set or invalid, set default keybinding
            keybinding = self.DEFAULT_KEYBINDING
            self.set_keybinding(keybinding) # try to save it to Gconf
        else:
            keybinding = self.get_keybinding()
        self.bind_keybinding(keybinding) # use keybindingx
    
    def get_modules_dir(self):
        """
        Get directory where modules are stored
        """
        return self._modules_dir
    
    def get_modules(self):
        """
        Get a list of module
        """
        return self._module_loader.filelist
    
    def get_enabled_modules(self):
        """
        Get a list of class names of enabled modules
        """
        return self._gconf.get_enabled_modules()
    
    def set_enabled_modules(self, name):
        """
        Set enabled modules
        
        @type name: list of class names 
        """
        if not self._gconf.set_enabled_modules(name):
            LOGGER.error("Unable to save enabled modules list to GConf")

    def get_keybinding(self):
        """
        Get keybinding
        
        @return: str
        """
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
    
    def get_window_width(self):
        return self._gconf.get_window_width()
    
    def get_window_height(self):
        return self._gconf.get_window_height()
    
    def get_window_x(self):      
        return self._gconf.get_window_x()      
       
    def get_window_y(self):      
        return self._gconf.get_window_y()
    
    def get_hide_after_action(self):
        return self._gconf.get_hide_after_action()
    
    def get_max_history_items(self):
        return self._gconf.get_max_history_items()
    
    def get_ui_name(self):
        return self._gconf.get_ui_name()
    
    def get_entry_width(self):
        return self._gconf.get_entry_width()

    def set_keybinding(self, binding):
        """
        Store keybinding
        """
        if not self._gconf.set_keybinding(binding):
            LOGGER.error("Unable to save keybinding setting to GConf")

    def bind_keybinding(self, binding):
        """
        Actually bind keybinding
        """
        if not self._keybinder.bind(binding):
            LOGGER.error("Keybinding is already in use")
        else:
            LOGGER.info("Successfully binded Deskbar to %s", binding)
    
    def set_min_chars(self, number):
        if not self._gconf.set_min_chars(number):
            LOGGER.error("Unable to save min chars setting to GConf")
    
    def set_type_delay(self, seconds):
        if not self._gconf.set_type_delay(seconds):
            LOGGER.error("Unable to save type delay setting to GConf")
    
    def set_use_selection(self, val):
        if not self._gconf.set_use_selection(val):
            LOGGER.error("Unable to save use selection setting to GConf")

    def set_clear_entry(self, val):
        if not self._gconf.set_clear_entry(val):
            LOGGER.error("Unable to save clear entry setting to GConf")
    
    def set_use_http_proxy(self, val):
        if not self._gconf.set_use_http_proxy(val):
            LOGGER.error("Unable to save http proxy setting to GConf")
    
    def set_proxy_host(self, host):
        if not self._gconf.set_proxy_host(host):
            LOGGER.error("Unable to save http proxy host setting to GConf")
    
    def set_proxy_port(self, port):
        if not self._gconf.set_proxy_port(port):
            LOGGER.error("Unable to save proxy port setting to GConf")
    
    def set_collapsed_cat(self, cat):
        if not self._gconf.set_collapsed_cat(cat):
            LOGGER.error("Unable to save collapsed cat setting to GConf")
    
    def set_window_width(self, width):
        if not self._gconf.set_window_width(width):
            LOGGER.error("Unable to save window width setting to GConf")
    
    def set_window_height(self, height):
        if not self._gconf.set_window_height(height):
            LOGGER.error("Unable to save window height setting to GConf")
    
    def set_window_x(self, x):      
        if not self._gconf.set_window_x(x):     
            LOGGER.error("Unable to save window x position setting to GConf")
       
    def set_window_y(self, y):      
        if not self._gconf.set_window_y(y):
            LOGGER.error("Unable to save window y position setting to GConf")
    
    def set_hide_after_action(self, width):
        if not self._gconf.set_hide_after_action(width):
            LOGGER.error("Unable to save hide after action setting to GConf")
    
    def set_max_history_items(self, amount):
        if not self._gconf.set_max_history_items(amount):
            LOGGER.error("Unable to save max history items setting to GConf")
        
    def set_ui_name(self, name):
        if not self._gconf.set_ui_name(name):
            LOGGER.error("Unable to save ui name setting to GConf")
    
    def set_entry_width(self, width):
        return self._gconf.set_entry_width(width)

    def get_history(self):
        """
        @return: L{deskbar.core.DeskbarHistory.DeskbarHistory}
        """
        return self._history
    
    def get_module_list(self):
        """
        @return: L{deskbar.core.ModuleList.ModuleList}
        """
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

    def reload_all_modules(self):
        self._module_list.clear()
        self._disabled_module_list.clear()
        LOGGER.info("Reloading all modules")
        self._module_loader.load_all()
    
    def stop_queries(self):
        self._stop_queries = True
        self._threadpool.stop()
    
    def query(self, text):
        """
        Query all enables modules
        
        This method waits L{get_type_delay} milliseconds
        until the querying is started. That way we only start
        querying if search term hasn't changed for L{get_type_delay} milliseconds
        """
        if (len(text) >= self.get_min_chars()):            
            if (self._start_query_id != 0):
                glib.source_remove(self._start_query_id)
            self._start_query_id = glib.timeout_add( self.get_type_delay(), self._query_real, text )
            self._stop_queries = False
            
    def _query_real(self, text):
        self._last_query = text
        for modname in self.get_enabled_modules():
            mod = self._module_list.get_module_instance_from_name( modname )
            if mod != None:
                self._threadpool.callInThread(mod.query, text)
        
    def on_modules_loaded(self, loader, callback=None):
        """
        After module's have been loaded, initialize them
        """
        enabled_list = self.get_enabled_modules()
        
        self.update_modules_priority(enabled_list)
        
        self._keybinder.connect("activated", lambda k,t: self._emit_keybinding_activated(t))
        self._emit_loaded()
        
        for mod in enabled_list:
            modinst = self._module_list.get_module_instance_from_name( mod )
            if modinst != None:
                self._module_loader.initialize_module_async( modinst )
                self._loaded_modules += 1
    
    def update_modules_priority(self, enabled_modules):    
        """
        @type enabled_modules: a list of exported classnames.
        
        Update the module priority present in both L{self._module_list} and
        C{enabled_modules} according to the ordering of C{enabled_modules}.
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
        """
        Connect to module's C{query-ready} signal
        Load history if all modules have been initialized
        """
        self._inited_modules += 1
        # Forward results
        module.connect ('query-ready', self.forward_query_ready)
        
        if (self._inited_modules == self._loaded_modules):
            self._history.load()
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
        
        new_modules = enabled_modules_set - current_modules_set
        for mod_name in new_modules:
            iter, index = self._module_list.get_position_from_context(mod_name)
            self.initialize_module(self._module_list[index][self._module_list.MODULE_CTX_COL])
        
        self.update_modules_priority(enabled_modules)
            
    def forward_query_ready(self, handler, query, matches):
        if query == self._last_query and matches != None and not self._stop_queries:
            for match in matches:
                if not isinstance(match, deskbar.interfaces.Match):
                    raise TypeError("Handler %r returned an invalid match: %r", handler,  match)
            self._emit_query_ready(matches)
    
    def update_gconf(self):
         # Update the gconf enabled modules settings
        enabled_modules = [mod.__class__.__name__ for mod in self._module_list if mod.is_enabled()]
        self.set_enabled_modules(enabled_modules)
    
    def _on_default_browser_changed(self, gconfstore, new_browser):
        new_browser = new_browser.split(" ")[0]
        
        if new_browser.find("firefox") != -1 or new_browser.find("iceweasel") != -1 \
            or new_browser.find("iceweasel") != -1:
            new_browser = "mozilla"
        
        if new_browser.find("epiphany") != -1:
            old_browser = "mozilla"
        elif new_browser == "mozilla":
            old_browser = "epiphany"
        else:
            new_browser = "other"
        
        #Sometimes we get false notification events when the browser didn't really change. Ignore them.
        if self.browser == new_browser:
            return
        
        self.browser = new_browser
                
        #create a list of the modules that were enabled for the old browser so that we can enable them for the new browser 
        enabled_browser_modules = []
        for module in self._module_list:
            # Check if the module is related to the old browser.
            if module.__class__.__module__ == "epiphany" or module.__class__.__module__ == "mozilla":
                if module.is_enabled(): 
                    self.stop_module(module, async=False)
                    if new_browser != "other":
                        enabled_browser_modules.append(module.__class__.__name__)
                    
                self._module_list.remove_module(module)
                # Refresh instructions
                module.__class__.has_requirements ()
                # Add module to self._disabled_module_list
                self._module_loader.emit("module-not-initialized", module)
        
        # Remove modules of new browser from self._disabled_module_list
        filename = None
        for module in self._disabled_module_list:
            if module.__module__ == new_browser:
                if filename is None:
                    filename = module.filename
                self._disabled_module_list.remove_module(module)
                
        if filename is not None:
            self._module_loader.load(filename)
        
        for module in enabled_browser_modules:
            new_module_name = module.replace(old_browser.capitalize(), new_browser.capitalize())
            new_module = self._module_list.get_module_instance_from_name(new_module_name)
            
            # If new_module is None the module has missing requirements
            if new_module != None:
                # If async is True then self.update_gconf() may be run before the modules were initialized
                self.initialize_module(new_module, async=False)
        
        self.update_gconf()
        
    def _on_keybinding_changed(self, store, keybinding):
        if gtk.accelerator_parse(keybinding) != (0,0):
            self.bind_keybinding(keybinding)

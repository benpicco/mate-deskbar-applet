import gio
import logging
from deskbar.handlers.actions.OpenWithApplicationAction import OpenWithApplicationAction
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.handlers.actions.GoToLocationAction import GoToLocationAction
from deskbar.handlers.actions.SendFileViaEmailAction import SendFileViaEmailAction
from os.path import isdir
from gettext import gettext as _

LOGGER = logging.getLogger(__name__)

def get_actions_for_uri(uri, display_name=None):
    """
    Return a list of applications suitable for
    the file depending on MIME type
    
    The default application is not included.
    Use the OpenFileAction for that purpose.
    
    @param uri: Unescaped URI or path of the file
    @param display_name: The optional name of
    the file for display. 
    """
    if not uri.startswith("file://"):
        gfile = gio.File(path=uri)
    else:
        gfile = gio.File(uri=uri)
    if display_name == None:
        display_name = gfile.get_basename()
    
    # Check if file exists
    path = gfile.get_path()
    if path == None:
        LOGGER.warning("File %s does not exist", uri)
        return []

    # If we have a directory only return one action
    if isdir(path):
        return [CopyToClipboardAction( _("Location"), gfile.get_path())]
        
    try:
        fileinfo = gfile.query_info("standard::content-type")
    except Exception, msg:
        LOGGER.error("Could not retrieve content type of %s: %s", gfile.get_path(), msg)
        return []
    
    actions = []
    
    default_appinfo = gio.app_info_get_default_for_type(fileinfo.get_content_type(), True)
    for appinfo in gio.app_info_get_all_for_type(fileinfo.get_content_type()):
        if default_appinfo == None \
        or appinfo.get_executable() != default_appinfo.get_executable():
            cmd = appinfo.get_executable()
            args = [gfile.get_path ()]
            
            cmd_args = cmd.split(" ")
            if len(cmd_args) > 0:
                cmd = cmd_args[0]
                args = cmd_args[1:] + args
            
            actions.append( OpenWithApplicationAction(display_name, cmd, args,
                    display_program_name=appinfo.get_name()) ) 

    actions.append( GoToLocationAction(display_name, gfile.get_uri ()) )
    actions.append( SendFileViaEmailAction(display_name, gfile.get_uri ()) )        
    actions.append( CopyToClipboardAction( _("URL of %s") % display_name, gfile.get_path ()) )
        
    return actions

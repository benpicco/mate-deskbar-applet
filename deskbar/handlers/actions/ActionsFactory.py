import gnomevfs
from deskbar.handlers.actions.OpenWithApplicationAction import OpenWithApplicationAction
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.handlers.actions.GoToLocationAction import GoToLocationAction
from deskbar.handlers.actions.SendFileViaEmailAction import SendFileViaEmailAction
from os.path import basename, isdir
from gettext import gettext as _

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
    if uri.startswith("file://"):
        uri = uri
        path = uri[7:] # remove file:// prefix
    else:
        path = uri
        uri = "file://"+path
    if display_name == None:
        display_name = basename(path)
    
    # If we have a directory only return one action
    if isdir(path):
        return [CopyToClipboardAction( _("Location"), path)]
    
    mime = gnomevfs.get_mime_type(uri)
    actions = []
    
    mime_default_cmd = gnomevfs.mime_get_default_application(mime)[2]
    mime_apps = gnomevfs.mime_get_all_applications(mime)
    for app in mime_apps:
        # 0: .desktop file (str)
        # 1: name (str)
        # 2: command (str)
        # 3: can open multiple files (bool)
        # 4: expects_uri (int)
        # 5: supported uri schemes (list)
        if app[2] != mime_default_cmd:
            actions.append( OpenWithApplicationAction(display_name, app[2], [path],
                    display_program_name=app[1]) )
    
    actions.append( GoToLocationAction(display_name, uri) )
    actions.append( SendFileViaEmailAction(display_name, uri) )        
    actions.append( CopyToClipboardAction( _("URL of %s") % display_name, path) )
        
    return actions
from deskbar.handlers.actions.OpenWithNautilusAction import OpenWithNautilusAction
from os.path import dirname, isdir
from gettext import gettext as _

class GoToLocationAction(OpenWithNautilusAction):
    """
    Open given location in nautilus
    """
    
    def __init__(self, name, file_dir_path):
        """
        @param file_dir_path: URI of file or directory
        """
        OpenWithNautilusAction.__init__(self, name, self.__get_dir(file_dir_path))
       
    def __get_dir(self, file_dir_path):
        if isdir(file_dir_path):
            return file_dir_path
        else:
            return dirname(file_dir_path) 
     
    def get_verb(self):
        return _("Go to location of %s") % "<b>%(name)s</b>"
    
    def get_icon(self):
        return "folder"
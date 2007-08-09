from gettext import gettext as _
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction

class SendEmailToAction(ShowUrlAction):
    
    def __init__(self, name, email):
        ShowUrlAction.__init__(self, name, "mailto:"+email)
        self._email = email
    
    def get_icon(self):
        return "stock_mail-send"
    
    def get_name(self, text=None):
        return {
            "name": self._name,
            "email": self._email,
        }
    
    def get_verb(self):
        #translators: First %s is the contact full name, second %s is the email address
        return _("Send Email to <b>%(name)s</b> (%(email)s)")
    
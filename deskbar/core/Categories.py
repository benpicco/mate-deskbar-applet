from gettext import gettext as _
from deskbar.core.Utils import load_icon

CATEGORIES = {
    # Special categories
    "default"    : {    
        "name": _("Uncategorized"),
        "icon": load_icon("unknown"),
    },
    "history" : {
        "name": _("History"),
        "icon": load_icon("stock_form-time-field"),
    },
    
    # Standard handlers
    "documents"    : {    
        "name": _("Documents"),
        "icon": load_icon("empty"),
    },
    "emails"    : {    
        "name": _("Emails"),
        "icon": load_icon("gnome-stock-mail-new"),
    },
    "conversations"    : {    
        "name": _("Conversations"),
        "icon": load_icon("system-users"),
    },
    "files"    : {    
        "name": _("Files"),
        "icon": load_icon("empty"),
    },
    "people"    : {
        "name": _("People"),
        "icon": load_icon("user-info"),
    },
    "places"    : {    
        "name": _("Places"),
        "icon": load_icon("folder"),
    },
    "actions"    : {    
        "name": _("Actions"),
        "icon": load_icon("gnome-system"),
    },
    "web"    : {    
        "name": _("Web"),
        "icon": load_icon("gnome-globe"),
    },
    "websearch"    : {    
        "name": _("Web Search"),
        "icon": load_icon("gtk-find"),
    },
    "news"    : {    
        "name": _("News"),
        "icon": load_icon("dialog-information"),
    },
    "notes"    : {    
        "name": _("Notes"),
        "icon": load_icon("stock_notes"),
    },
    
}
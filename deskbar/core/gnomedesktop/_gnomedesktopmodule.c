/* -*- Mode: C; c-basic-offset: 4 -*- */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

/* include this first, before NO_IMPORT_PYGOBJECT is defined */
#include <pygobject.h>
#include <libgnome/gnome-desktop-item.h>


void py_gnomedesktop_register_classes (PyObject *d);
void py_gnomedesktop_add_constants(PyObject *module, const gchar *strip_prefix);
extern PyMethodDef py_gnomedesktop_functions[];

DL_EXPORT(void)
init_gnomedesktop(void)
{
    PyObject *m, *d;
	
    init_pygobject ();
	if (PyImport_ImportModule("gnomevfs") == NULL) {
        PyErr_SetString(PyExc_ImportError, "could not import gnomevfs");
        return;
    }
    
    m = Py_InitModule ("_gnomedesktop", py_gnomedesktop_functions);
    d = PyModule_GetDict (m);
	
    py_gnomedesktop_register_classes (d);
	py_gnomedesktop_add_constants (m, "GNOME_DESKTOP_ITEM_");
	
	if (PyErr_Occurred())
        Py_FatalError("could not initialise module _gnomedesktop");
}

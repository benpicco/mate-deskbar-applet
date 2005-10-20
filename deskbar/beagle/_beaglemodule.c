/* -*- Mode: C; c-basic-offset: 4 -*- */
#ifdef HAVE_CONFIG_H
#  include "config.h"
#endif

/* include this first, before NO_IMPORT_PYGOBJECT is defined */
#include <pygobject.h>

/* include any extra headers needed here */
#include <beagle/beagle.h>

void py_beagle_register_classes(PyObject *d);
void py_beagle_add_constants(PyObject *module, const gchar *strip_prefix);
extern PyMethodDef py_beagle_functions[];

DL_EXPORT(void)
init_beagle(void)
{
    PyObject *m, *d;

    /* perform any initialisation required by the library here */
	init_pygobject();
	
    m = Py_InitModule("_beagle", py_beagle_functions);
    d = PyModule_GetDict(m);
    
    /* add anything else to the module dictionary (such as constants) */
    py_beagle_register_classes(d);
    py_beagle_add_constants(m, "BEAGLE_");
    
    if (PyErr_Occurred())
        Py_FatalError("could not initialise module _beagle");
}

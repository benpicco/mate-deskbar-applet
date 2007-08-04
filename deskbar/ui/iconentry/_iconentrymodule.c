/* -*- Mode: C; c-basic-offset: 4 -*- */
#ifdef HAVE_CONFIG_H
#  include "config.h"
#endif

/* include this first, before NO_IMPORT_PYGOBJECT is defined */
#include <pygobject.h>

/* include any extra headers needed here */

void py_iconentry_register_classes(PyObject *d);
extern PyMethodDef py_iconentry_functions[];

DL_EXPORT(void)
init_iconentry(void)
{
    PyObject *m, *d;

    /* perform any initialisation required by the library here */
	init_pygobject();
	
    m = Py_InitModule("_iconentry", py_iconentry_functions);
    d = PyModule_GetDict(m);
    
    /* add anything else to the module dictionary (such as constants) */
    py_iconentry_register_classes(d);

    if (PyErr_Occurred())
        Py_FatalError("could not initialise module _iconentry");
}

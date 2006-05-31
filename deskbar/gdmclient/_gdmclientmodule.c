#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

/* include this first, before NO_IMPORT_PYGOBJECT is defined */
#include <pygobject.h>

void py_gdmclient_register_classes (PyObject *d);
void py_gdmclient_add_constants(PyObject *module, const gchar *strip_prefix);
extern PyMethodDef py_gdmclient_functions[];

DL_EXPORT(void)
init_gdmclient(void)
{
	PyObject *m, *d;

	init_pygobject ();

	m = Py_InitModule ("_gdmclient", py_gdmclient_functions);
	d = PyModule_GetDict (m);

	py_gdmclient_register_classes (d);
	py_gdmclient_add_constants (m, "GDM_");

	if (PyErr_Occurred ())
		Py_FatalError("could not initialise module _gdmclient");
}

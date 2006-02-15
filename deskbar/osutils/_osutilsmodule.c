#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <Python.h>
#ifdef HAVE_PRCTL
#include <sys/prctl.h>
#endif
#include <stdio.h>
#include <errno.h>

/* Function Prototypes */
static PyObject * osutils_set_process_name (PyObject *self, PyObject *args);

/* Function Mapping Table */
static PyMethodDef py_osutils_functions[] =
{
	{ "set_process_name", osutils_set_process_name, METH_VARARGS, "" },
	{ NULL, NULL, 0, NULL }
};

PyMODINIT_FUNC
init_osutils (void)
{
	Py_InitModule ("_osutils", py_osutils_functions);
}
	
static PyObject *
osutils_set_process_name (PyObject *self, PyObject *args)
{
	const char *name;

	if (!PyArg_ParseTuple (args, "s", &name))
	{
		PyErr_SetString (PyExc_TypeError, "set_process_name needs a string as argument");
		return NULL;
	}

#ifdef HAVE_PRCTL
	if (prctl (PR_SET_NAME, (unsigned long) name, 0, 0, 0))
	{
		PyErr_SetString (PyExc_IOError, "prctl() failed");
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
#else
	PyErr_SetString (PyExc_IOError, "prctl unavailable");
	return NULL;
#endif
}

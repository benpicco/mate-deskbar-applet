#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <Python.h>
#include <stdio.h>
#include <errno.h>
#include <glib.h>

/* Function Prototypes */
static PyObject * userdirs_get_xdg_user_dir (PyObject *self, PyObject *directory);

/* Function Mapping Table */
static PyMethodDef py__userdirs_functions[] =
{
	{ "get_xdg_user_dir", userdirs_get_xdg_user_dir, 0, "" },
	{ NULL, NULL, 0, NULL }
};

PyMODINIT_FUNC
init__userdirs (void)
{
	Py_InitModule ("__userdirs", py__userdirs_functions);
}
	
static PyObject *
userdirs_get_xdg_user_dir (PyObject *self, PyObject *directory)
{
    if (!PyInt_Check (directory))
        return NULL;
    else {
        const char *dir = g_get_user_special_dir ((GUserDirectory) PyInt_AsLong (directory));

        if (dir)
            return PyString_FromString (dir);
        else
            return Py_None;
    }
}

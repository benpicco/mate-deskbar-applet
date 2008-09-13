#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <Python.h>
#include <stdio.h>
#include <errno.h>
#include <glib.h>

/* Function Prototypes */
static PyObject * userdirs_get_xdg_user_dir (PyObject *self, PyObject *directory);
static void userdirs_register_constants (PyObject *self);

/* Function Mapping Table */
static PyMethodDef py__userdirs_functions[] =
{
	{ "get_xdg_user_dir", userdirs_get_xdg_user_dir, 0, "" },
	{ NULL, NULL, 0, NULL }
};

PyMODINIT_FUNC
init__userdirs (void)
{
	PyObject* m;

	m = Py_InitModule ("__userdirs", py__userdirs_functions);
	userdirs_register_constants (m);
}
	
static PyObject *
userdirs_get_xdg_user_dir (PyObject *self, PyObject *directory)
{
    if (!PyInt_Check (directory)) {
    	PyErr_SetString (PyExc_TypeError, "The first argument must be an integer");
        return NULL;
    } else {
        const gchar *dir = g_get_user_special_dir ((GUserDirectory) PyInt_AsLong (directory));

        if (dir) {
            return PyString_FromString (dir);
        } else {
        	PyErr_SetString (PyExc_ValueError, "Argument out of range");
        	return NULL;
        }
    }
}

static void
userdirs_register_constants (PyObject *m) {
    PyModule_AddIntConstant (m, "DIRECTORY_DESKTOP", G_USER_DIRECTORY_DESKTOP);
    PyModule_AddIntConstant (m, "DIRECTORY_DOCUMENTS", G_USER_DIRECTORY_DOCUMENTS);
    PyModule_AddIntConstant (m, "DIRECTORY_DOWNLOAD", G_USER_DIRECTORY_DOWNLOAD);
    PyModule_AddIntConstant (m, "DIRECTORY_MUSIC", G_USER_DIRECTORY_MUSIC);
    PyModule_AddIntConstant (m, "DIRECTORY_PICTURES", G_USER_DIRECTORY_PICTURES);
    PyModule_AddIntConstant (m, "DIRECTORY_PUBLIC_SHARE", G_USER_DIRECTORY_PUBLIC_SHARE);
    PyModule_AddIntConstant (m, "DIRECTORY_TEMPLATES", G_USER_DIRECTORY_TEMPLATES);
    PyModule_AddIntConstant (m, "DIRECTORY_VIDEOS", G_USER_DIRECTORY_VIDEOS);
}

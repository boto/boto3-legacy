import importlib

from boto3.core.exceptions import IncorrectImportPath


def import_class(import_path):
    """
    Imports a class dynamically from a full import path.
    """
    path_bits = import_path.split('.')
    mod_path = '.'.join(path_bits[:-1])
    klass_name = path_bits[-1]

    try:
        mod = importlib.import_module(mod_path)
    except ImportError:
        raise IncorrectImportPath(
            "Could not import module '{0}'.".format(mod_path)
        )

    try:
        klass = getattr(mod, klass_name)
    except AttributeError:
        raise IncorrectImportPath(
            "Imported module '{0}' but could not find class '{1}'.".format(
                mod_path,
                klass_name
            )
        )

    return klass

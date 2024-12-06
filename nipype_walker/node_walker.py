import inspect

from nipype.interfaces.base.core import BaseInterface

from nipype_walker import input_walker


def walk(cls):
    """

    Inspect a subclass of BaseInterface

    :param cls:
    :return:
    """

    if not issubclass(cls, BaseInterface):
        return {}

    for members in inspect.getmembers(cls):
        if members[0] == '__dict__':
            attributes = members[1]
            return input_walker.walk(attributes['input_spec'])
    return {}
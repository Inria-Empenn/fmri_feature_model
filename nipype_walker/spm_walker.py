import inspect
import nipype.interfaces.spm.preprocess as spm_preprocess
from nipype.interfaces.base.core import BaseInterface

from nipype_walker import node_walker


def walk():
    return walk_preprocessing()

def walk_preprocessing():
    """

    Inspect nipype.interfaces.spm.preprocess

    :return:
    """

    json = {"name": "SPM Preprocessing"}

    for cls in inspect.getmembers(spm_preprocess):
        if inspect.isclass(cls[1]) and issubclass(cls[1], BaseInterface):
            json.update({cls[1].__name__: node_walker.walk(cls[1])})
    return json

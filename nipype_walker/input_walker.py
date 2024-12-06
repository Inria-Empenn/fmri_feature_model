import inspect

import nipype.interfaces.spm.preprocess as spm_preprocess
from nipype.interfaces.base.core import BaseInterface
from nipype.interfaces.base.specs import BaseInterfaceInputSpec
from nipype.interfaces.base.traits_extension import InputMultiPath, File
from traits.trait_types import Range, Bool, Int, Float, String

def walk(cls):
    """
    Inspect a subclass of BaseInterfaceInputSpec
    :param cls:
    :return:
    """
    json = {}
    if not issubclass(cls, BaseInterfaceInputSpec):
        return json
    for members in inspect.getmembers(cls):
        if members[0] == '__base_traits__':
            attributes = members[1]
            for key in attributes:
                name = key
                input_param = attributes[key].handler
                json[name] = walk_param(input_param)
    return json

def walk_param(trait):
    for member in inspect.getmembers(trait):
        if member[0] == '__dict__':
            attributes = member[1]
            json = parse_common_param_attributes(attributes)
            if isinstance(trait, Bool):
                 json["type"] = "Boolean"
            elif isinstance(trait, String):
                 json["type"] = "String"
            elif isinstance(trait, Int):
                json["type"] = "Integer"
            elif isinstance(trait, Float):
                json["type"] = "Float"
            elif isinstance(trait, InputMultiPath):
                json["type"] = "Files"
            elif isinstance(trait, File):
                json["type"] = "File"
            elif isinstance(trait, Range):
                 json.update(parse_range(attributes))
            return json
    return None


def parse_common_param_attributes(attributes):
    """
    Parse common values of a trait

    :param name:
    :param attributes:
    :return:
    """
    json = {"desc": "", "mandatory": False, "field": "", "default_value": None, "type" : "Unsupported"}
    if "_metadata" in attributes:
        json["desc"] = attributes["_metadata"].get("desc", "")
        json["mandatory"] = attributes["_metadata"].get("mandatory", False)
        json["field"] = attributes["_metadata"].get("field", "")
    json["default_value"] = attributes.get("default_value", None)
    return json

def parse_range(attributes):
    """
    Parse a Range type trait
    :param attributes:
    :return:
    """
    json = {
        "value": attributes.get("_value", None),
        "low": attributes.get("_low", None),
        "high": attributes.get("_high", None),
    }
    json["type"] = get_range_type(json)
    return json


def get_range_type(json):
    """
    Infer range type (int, float) from value, low, high if set

    :param json:
    :return:
    """
    test = None
    if json["value"] is not None:
        test = json["value"]
    elif json["low"] is not None:
        test = json["low"]
    elif json["high"] is not None:
        test = json["high"]

    if isinstance(test, float):
        return "Float"
    if isinstance(test, int):
        return "Integer"
    return "Unsupported"
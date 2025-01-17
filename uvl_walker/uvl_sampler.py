import random

from antlr4 import *
from uvl.UVLCustomLexer import UVLCustomLexer
from uvl.UVLPythonParser import UVLPythonParser

from uvl_walker.custom_uvl_python_listener import CustomUVLPythonListener


def get_sample(path: str):
    input_stream = FileStream(path)
    lexer: UVLCustomLexer = UVLCustomLexer(input_stream)
    stream: CommonTokenStream = CommonTokenStream(lexer)
    parser = UVLPythonParser(stream)
    walker = ParseTreeWalker()
    listener = CustomUVLPythonListener()
    walker.walk(listener, parser.featureModel())
    json = listener.get_json()

    sample = {}

    if 'features' not in json:
        return sample

    for feature in json['features']:

        sample.update({feature['id']: {}})

        steps = sample_feature(feature)

        for step in steps:
            params = sample_feature(step)

            sample[feature['id']].update({step['id']: {}})

            for param in params:
                values = sample_feature(param)

                if not values:
                    sample[feature['id']][step['id']].update({param['id']: True})
                else:
                    sample[feature['id']][step['id']].update({param['id']: values[0]['id']})
    return sample


def sample_feature(json):
    features = []
    if 'optional' in json:
        for optional in json['optional']:
            if bool(random.choice([True, False])):
                features.append(optional)
    if 'mandatory' in json:
        for mandatory in json['mandatory']:
            features.append(mandatory)
    if 'alternative' in json:
        features.append(random.choice(json['alternative']))

    return features


if __name__ == '__main__':
    print(get_sample('../model/uvl/preprocessing_pipeline.uvl'))

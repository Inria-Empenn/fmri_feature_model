import os

from nipype import Node, IdentityInterface, SelectFiles, DataSink

from core.metadata import Metadata


class WorkflowService:

    def get_feature_leaf(self, prefix, features):
        for feature in features:
            if feature.startswith(prefix + '/'):
                return feature.removeprefix(prefix + '/')
        return ""

    def get_infos(self, metadata: Metadata):
        infos = Node(IdentityInterface(fields=['subject_id']), name="infos")
        infos.iterables = [('subject_id', metadata.subjects)]
        return infos

    def get_input(self, metadata: Metadata):
        templates = {'anat': os.path.join(metadata.data_path, metadata.anat_subpath),
                     'func': os.path.join(metadata.data_path, metadata.func_subpath), }
        return Node(SelectFiles(templates, base_directory=metadata.data_path), name="input")

    def get_output(self, metadata: Metadata):
        return Node(DataSink(base_directory=metadata.result_path), name="output")

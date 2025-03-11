import os

from nipype import Node, IdentityInterface, SelectFiles, DataSink
from nipype import Workflow

from core.analysis_service import AnalysisService
from core.data_descriptor import DataDescriptor
from core.file_service import RESULT_NII
from core.preproc_service import PreprocService
from model.py.constants import SPM


class WorkflowService:
    preproc_srv = PreprocService()
    analysis_srv = AnalysisService()

    def run(self, workflow: Workflow, path: str, ):
        print(f"Workflow [{workflow.name}] running...")
        workflow.run()
        print(f"Workflow results written to [{path}].")

    def build_workflow(self, config, data_descriptor: DataDescriptor, name: str) -> Workflow:

        workflow = Workflow(name=f'Workflow-{name}')

        output_path = os.path.join(data_descriptor.result_path, name)

        nodes = {}
        print("Implementing preprocessing nodes...")
        nodes.update(self.preproc_srv.get_nodes(config, data_descriptor))
        print("Implementing analysis nodes...")
        nodes.update(self.analysis_srv.get_nodes(config, data_descriptor))

        workflow.base_dir = data_descriptor.work_path

        src_infos = self.get_infos(data_descriptor)
        inputs = self.get_input(data_descriptor)

        print("Connecting all nodes...")
        workflow.connect(src_infos, 'subject_id', inputs, 'subject_id')

        # inputs -> motion_correction_realignment
        workflow.connect(inputs, 'func',
                         nodes['motion_correction_realignment'], SPM.Preprocessing.Realign.Input.in_files)

        # distorsion_correction
        # Ignore for now

        if 'slice_timing_correction' in nodes:
            # motion_correction_realignment -> slice_timing_correction
            workflow.connect(nodes['motion_correction_realignment'], SPM.Preprocessing.Realign.Output.realigned_files,
                             nodes['slice_timing_correction'], SPM.Preprocessing.SliceTiming.Input.in_files)
            # slice_timing_correction -> spatial_normalization
            workflow.connect(nodes['slice_timing_correction'], SPM.Preprocessing.SliceTiming.Output.timecorrected_files,
                             nodes['spatial_normalization'], SPM.Preprocessing.Normalize.Input.apply_to_files)
        else:
            # motion_correction_realignment -> spatial_normalization
            workflow.connect(nodes['motion_correction_realignment'], SPM.Preprocessing.Realign.Output.realigned_files,
                             nodes['spatial_normalization'], SPM.Preprocessing.Normalize.Input.apply_to_files)

        func_input = SPM.Preprocessing.Coregister.Input.target
        anat_input = SPM.Preprocessing.Coregister.Input.source

        # motion_correction_realignment -> coregistration
        workflow.connect(nodes['motion_correction_realignment'], SPM.Preprocessing.Realign.Output.mean_image,
                         nodes['coregistration'], func_input)
        # inputs -> coregistration
        workflow.connect(inputs, 'anat',
                         nodes['coregistration'], anat_input)

        # coregister -> segmentation
        workflow.connect(nodes['coregistration'], SPM.Preprocessing.Coregister.Output.coregistered_source,
                         nodes['segmentation'], SPM.Preprocessing.NewSegment.Input.channel_files)

        # segmentation -> spatial_normalization
        workflow.connect(nodes['segmentation'], SPM.Preprocessing.NewSegment.Output.forward_deformation_field,
                         nodes['spatial_normalization'], SPM.Preprocessing.Normalize12.Input.deformation_file)

        # spatial_normalization -> spatial_smoothing
        workflow.connect(nodes['spatial_normalization'], SPM.Preprocessing.Normalize12.Output.normalized_files,
                         nodes['spatial_smoothing'], SPM.Preprocessing.Smooth.Input.in_files)

        workflow.connect(nodes['spatial_smoothing'], SPM.Preprocessing.Smooth.Output.smoothed_files,
                         self.get_output(output_path),
                         f'{output_path}.@smoothed_files')

        print("Workflow ready.")
        return workflow

    def get_infos(self, metadata: DataDescriptor):
        infos = Node(IdentityInterface(fields=['subject_id']), name="infos")
        infos.iterables = [('subject_id', metadata.subjects)]
        return infos

    def get_input(self, metadata: DataDescriptor):
        templates = {'anat': os.path.join(metadata.data_path, metadata.anat_subpath),
                     'func': os.path.join(metadata.data_path, metadata.func_subpath), }
        return Node(SelectFiles(templates, base_directory=metadata.data_path), name="input")

    def get_output(self, path: str):
        datasink = Node(DataSink(base_directory=path), name="output")
        datasink.inputs.regexp_substitutions = [(r'(.*)\.nii', RESULT_NII)]
        return datasink

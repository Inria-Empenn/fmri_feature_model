import json
import os
from datetime import datetime

import nipype.interfaces.matlab as mlab  # how to run matlab
from nipype import Workflow

from model.py.constants import SPM
from core.AAFM_service import AAFMService
from core.metadata import Metadata
from core.preproc_service import PreprocService
from core.workflow_service import WorkflowService

matlab_path = '/home/ymerel/matlab/bin/matlab'
matlab_cmd = matlab_path + " -nodesktop -nosplash"
spm_path = '/home/ymerel/spm12/'
project_path = os.path.abspath('/home/ymerel/fmri-feature-model')
# Matlab command line
mlab.MatlabCommand.set_default_matlab_cmd(matlab_cmd)
# set SPM path into matlab
mlab.MatlabCommand.set_default_paths(os.path.abspath(spm_path))

aafm_srv = AAFMService()
workflow_srv = WorkflowService()
preproc_srv = PreprocService()


def get_metadata():
    metadata = Metadata()
    # http://www.fil.ion.ucl.ac.uk/spm/data/auditory/
    metadata.data_path = os.path.join(project_path, 'data/auditory')
    metadata.anat_subpath = os.path.join('sub-{subject_id}', 'anat', 'sub-{subject_id}_T1w.nii')
    metadata.func_subpath = os.path.join('sub-{subject_id}', 'func', 'sub-{subject_id}_task-auditory_bold.nii')
    metadata.result_path = os.path.join(project_path, 'results')
    metadata.work_path = os.path.join(project_path, 'work')
    metadata.subjects = ['01']
    metadata.slices_nb = 64
    metadata.tr = 7.0
    metadata.units = 'scans'
    return metadata


def write_config(path, config):
    config_txt = json.dumps({"features": config.get_selected_elements()})

    f = open(path + '/sampled_config.json', "a")
    f.write(config_txt)
    f.close()


def build_workflow(nodes, metadata):
    preproc = Workflow(name='Preprocessing')
    preproc.base_dir = metadata.work_path

    src_infos = workflow_srv.get_infos(metadata)
    inputs = workflow_srv.get_input(metadata)
    preproc.connect(src_infos, 'subject_id', inputs, 'subject_id')

    # inputs -> motion_correction_realignment
    preproc.connect(inputs, 'func',
                    nodes[1], SPM.Preprocessing.Realign.Input.in_files)

    # distorsion_correction
    # Ignore for now

    # motion_correction_realignment -> slice_timing_correction
    preproc.connect(nodes[1], SPM.Preprocessing.Realign.Output.realigned_files,
                    nodes[2], SPM.Preprocessing.SliceTiming.Input.in_files)

    # motion_correction_realignment -> coregistration
    preproc.connect(nodes[1], SPM.Preprocessing.Realign.Output.mean_image,
                    nodes[3], SPM.Preprocessing.Coregister.Input.target)
    # inputs -> coregistration
    preproc.connect(inputs, 'anat',
                    nodes[3], SPM.Preprocessing.Coregister.Input.source)

    # coregister -> segmentation
    preproc.connect(nodes[3], SPM.Preprocessing.Coregister.Output.coregistered_source,
                    nodes[4], SPM.Preprocessing.NewSegment.Input.channel_files)

    # slice_timing_correction -> spatial_normalization
    preproc.connect(nodes[2], SPM.Preprocessing.SliceTiming.Output.timecorrected_files,
                    nodes[5], SPM.Preprocessing.Normalize.Input.apply_to_files)

    # segmentation -> spatial_normalization
    preproc.connect(nodes[4], SPM.Preprocessing.NewSegment.Output.forward_deformation_field,
                    nodes[5], SPM.Preprocessing.Normalize12.Input.deformation_file)

    # spatial_normalization -> spatial_smoothing
    preproc.connect(nodes[5], SPM.Preprocessing.Normalize12.Output.normalized_files,
                    nodes[6], SPM.Preprocessing.Smooth.Input.in_files)

    preproc.connect(nodes[6], SPM.Preprocessing.Smooth.Output.smoothed_files, workflow_srv.get_output(metadata),
                    f'{metadata.result_path}.@smoothed_files')

    return preproc


if __name__ == '__main__':

    metadata = get_metadata()

    fm = aafm_srv.get_feature_model('../model/uvl/preprocessing_pipeline.uvl')
    configs = aafm_srv.sample(fm, 1)

    for config in configs:
        tstmp = datetime.now().strftime('%d%m%Y_%H%M%S')
        metadata.result_path = os.path.join(project_path, 'results', tstmp)

        if not os.path.exists(metadata.result_path):
            os.makedirs(metadata.result_path)
        write_config(metadata.result_path, config)

        nodes = preproc_srv.get_nodes(config, metadata)
        preproc = build_workflow(nodes, metadata)
        preproc.run()

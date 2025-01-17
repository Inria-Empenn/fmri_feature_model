from nipype import Workflow, Node
from nipype.interfaces.spm import Smooth, Coregister, NewSegment, SliceTiming, Normalize12, Realign

from model.py.constants import SPM
from uvl_walker.uvl_sampler import get_sample

bias_regs = {
    'light': 0.01,
    'medium': 0.1,
    'heavy': 1
}

cost_funcs = {
    'mutual_information': 'mi',
    'normalised_mutual_information': 'nmi',
    'entropy_correlation_coefficient': 'ecc',
    'normalised_cross_correlation': 'ncc'
}

def get_infos():
    infos = pe.Node(IdentityInterface(fields=['subject_id']), name="infos")
    infos.iterables = [('subject_id', subjects)]
    return infos


def get_input():
    templates = {'anat': os.path.join(data_dir, 'sub-{subject_id}', 'anat', 'sub-{subject_id}_T1w.nii'),
                 'func': os.path.join(data_dir, 'sub-{subject_id}', 'func', 'sub-{subject_id}_task-auditory_bold.nii'),
                 'events': events_file }
    return pe.Node(SelectFiles(templates, base_directory=data_dir), name="input")


def get_output():
    return pe.Node(DataSink(base_directory=results_dir), name="output")


def get_node(name, value):
    if name == 'motion_correction_realignment':
        return get_motion_correction_realignment(value)
    if name == 'slice_timing_correction':
        return get_slice_timing_correction(value)
    if name == 'coregistration':
        return get_coregistration(value)
    if name == 'segmentation':
        return get_segmentation(value)
    if name == 'spatial_normalization':
        return get_spatial_normalization(value)
    if name == 'distorsion_correction':
        print('distorsion_correction')
    if name == 'spatial_smoothing':
        return get_smoothing(value)


def get_motion_correction_realignment(params):
    node = Node(interface=Realign(), name="motion_correction_realignment")

    if SPM.Preprocessing.Realign.Input.register_to_mean in params:
        node.inputs.register_to_mean = True

    if 'register_to_first' in params:
        node.inputs.register_to_mean = False

    return node


def get_slice_timing_correction(params):
    node = Node(interface=SliceTiming(), name="slice_timing_correction")
    return node


def get_coregistration(params):
    node = Node(interface=Coregister(), name="coregistration")

    if SPM.Preprocessing.Coregister.Input.cost_function in params:
        function = params[SPM.Preprocessing.Coregister.Input.cost_function]
        node.inputs.cost_function = cost_funcs[function]

    return node


def get_segmentation(params):
    node = Node(interface=NewSegment(), name="segmentation")
    return node



def get_spatial_normalization(params):
    node = Node(interface=Normalize12(), name="spatial_normalization")

    if SPM.Preprocessing.Normalize12.Input.bias_regularization in params:
        level = params[SPM.Preprocessing.Normalize12.Input.bias_regularization]
        node.inputs.bias_regularization = bias_regs[level]

    if SPM.Preprocessing.Normalize12.Input.bias_fwhm in params:
        node.inputs.bias_fwhm = float(params[SPM.Preprocessing.Normalize12.Input.bias_fwhm])

    return node


def get_smoothing(params):
    node = Node(interface=Smooth(), name="spatial_smoothing")

    if SPM.Preprocessing.Smooth.Input.fwhm in params:
        node.inputs.fwhm = float(params[SPM.Preprocessing.Smooth.Input.fwhm])

    return node


if __name__ == '__main__':
    sample = get_sample('../model/uvl/preprocessing_pipeline.uvl')
    print(sample)

    if 'preprocessing' in sample:
        preprocessing = sample['preprocessing']

        preproc = Workflow(name='Preprocessing')

        nodes = []

        for step in preprocessing:
            nodes.append(get_node(step, preprocessing[step]))



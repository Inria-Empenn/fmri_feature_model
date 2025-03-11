import os

from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from nipype import Node
from nipype.interfaces.spm import Smooth, Coregister, NewSegment, SliceTiming, Normalize12, Realign

from core.data_descriptor import DataDescriptor


class PreprocService:

    spm_path = '/home/ymerel/spm12/'

    steps = [
        'distorsion_correction',
        'motion_correction_realignment',
        'slice_timing_correction',
        'coregistration',
        'segmentation',
        'spatial_normalization',
        'spatial_smoothing'
    ]

    bias_regs = {
        'extremely_light': 0.00001,
        'very_light': 0.0001,
        'light': 0.001,
        'medium': 0.01,
        'heavy': 0.1
    }

    cost_funcs = {
        'mutual_information': 'mi',
        'normalised_mutual_information': 'nmi',
        'entropy_correlation_coefficient': 'ecc',
        'normalised_cross_correlation': 'ncc'
    }

    def get_nodes(self, config: Configuration, data_desc: DataDescriptor) -> dict[str, Node]:
        nodes = {}
        features = config.get_selected_elements()

        for step in self.steps:
            if step in features:
                print(f"Implementing [{step}]...")
                node = self.get_node(step, features, data_desc)
                if node:
                    nodes[step] = node
                print(f"[{step}] added to workflow")

        return nodes

    def get_node(self, name, features: list, data_desc: DataDescriptor):
        if name == 'distorsion_correction':
            return self.get_distorsion_correction(features)
        if name == 'motion_correction_realignment':
            return self.get_motion_correction_realignment(features)
        if name == 'slice_timing_correction':
            return self.get_slice_timing_correction(features, data_desc)
        if name == 'coregistration':
            return self.get_coregistration(features)
        if name == 'segmentation':
            return self.get_segmentation(features)
        if name == 'spatial_normalization':
            return self.get_spatial_normalization(features)
        if name == 'spatial_smoothing':
            return self.get_smoothing(features)

    def get_motion_correction_realignment(self, features: list):

        name = "motion_correction_realignment"
        node = Node(interface=Realign(), name=name)

        if f"{name}/register_to" in features:

            if f"{name}/register_to/first" in features:
                node.inputs.register_to_mean = False

            if f"{name}/register_to/mean" in features:
                node.inputs.register_to_mean = True
        return node

    def get_slice_timing_correction(self, features: list, data_desc: DataDescriptor):
        name = "slice_timing_correction"
        node = Node(interface=SliceTiming(), name=name)
        node.inputs.num_slices = data_desc.slices_nb
        node.inputs.time_repetition = data_desc.tr
        node.inputs.time_acquisition = data_desc.tr - (data_desc.tr / data_desc.slices_nb)
        node.inputs.slice_order = list(range(data_desc.slices_nb, 0, -1))  # [64 63 62 ... 3 2 1]

        if f"{name}/ref_slice" in features:

            if f"{name}/ref_slice/first" in features:
                node.inputs.ref_slice = 1

            if f"{name}/ref_slice/middle" in features:
                node.inputs.ref_slice = data_desc.slices_nb / 2

        return node

    def get_coregistration(self, features: list):
        name = "coregistration"
        node = Node(interface=Coregister(), name=name)

        function = self.get_feature_end(f"{name}/cost_function", features)
        node.inputs.cost_function = self.cost_funcs[function]

        return node

    def get_segmentation(self, features: list):
        node = Node(interface=NewSegment(), name="segmentation")
        tpm_file = os.path.abspath(os.path.join(self.spm_path, 'tpm/TPM.nii'))
        tissue1 = (tpm_file, 1), 1, (True, False), (False, False)
        tissue2 = (tpm_file, 2), 1, (True, False), (False, False)
        tissue3 = (tpm_file, 3), 2, (True, False), (False, False)
        tissue4 = (tpm_file, 4), 3, (True, False), (False, False)
        tissue5 = (tpm_file, 5), 4, (True, False), (False, False)
        tissue6 = (tpm_file, 6), 2, (False, False), (False, False)
        node.inputs.tissues = [tissue1, tissue2, tissue3, tissue4, tissue5, tissue6]
        node.inputs.write_deformation_fields = [False, True]
        return node

    def get_spatial_normalization(self, features: list):
        name = "spatial_normalization"
        node = Node(interface=Normalize12(), name=name)

        node.inputs.jobtype = 'write'

        if f"{name}/bias_regularisation" in features:
            node.inputs.bias_regularization = self.bias_regs[self.get_feature_end(f"{name}/bias_regularisation", features)]
        else:
            node.inputs.bias_regularization = 0

        if f"{name}/bias_fwhm" in features:
            node.inputs.bias_fwhm = float(self.get_feature_end(f"{name}/bias_fwhm", features))
        else:
            node.inputs.bias_fwhm = "Inf"

        return node

    def get_smoothing(self, features: list):
        name = "spatial_smoothing"
        node = Node(interface=Smooth(), name=name)

        node.inputs.fwhm = 0
        if f"{name}/fwhm" in features:
            node.inputs.fwhm = float(self.get_feature_end(f"{name}/fwhm", features))

        return node

    def get_feature_end(self, prefix, features):
        for feature in features:
            if feature.startswith(prefix + '/'):
                return feature.removeprefix(prefix + '/')
        return ""

    def get_distorsion_correction(self, features):
        return None

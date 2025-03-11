import os

from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from nipype import Node
from nipype.interfaces.spm import EstimateModel, Level1Design, EstimateContrast, SliceTiming, Normalize12, Realign
import hashlib
import os
from builtins import range

import nipype.algorithms.modelgen as model  # model specification
from nipype.algorithms.modelgen import SpecifySPMModel
import nipype.interfaces.matlab as mlab  # how to run matlab
import nipype.interfaces.spm as spm  # spm
import nipype.pipeline.engine as pe  # pypeline engine
from nipype import IdentityInterface, SelectFiles, DataSink


from core.data_descriptor import DataDescriptor


class AnalysisService:

    steps = [
        'signal_modeling'
    ]

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
        if name == 'signal_modeling':
            return self.get_signal_modelling(features)

    def get_signal_modelling(self, features):
        pass

    def get_model_spec(self, data_desc: DataDescriptor):
        modelspec = Node(interface=SpecifySPMModel(), name="Specify_1st_level")
        modelspec.inputs.input_units = data_desc.units
        modelspec.inputs.output_units = data_desc.units
        modelspec.inputs.time_repetition = data_desc.tr
        modelspec.inputs.high_pass_filter_cutoff = 128
        return modelspec

    def get_design(self, features: list, data_desc: DataDescriptor):
        design = pe.Node(interface=Level1Design(), name="level1design")
        design.inputs.timing_units = data_desc.units
        design.inputs.interscan_interval = data_desc.tr

        name = "signal_modeling"

        if f"signal_modeling/hrf" in features:
            time = 0
            dispersion = 0
            if f"{name}/hrf/temporal_derivs" in features:
                time = 0
                dispersion = 0
            if f"{name}/hrf/temporal_derivs" in features:
                time = 1
            if f"{name}/hrf/temporal_dispersion_derivs" in features:
                time = 1
                dispersion = 1
            design.inputs.bases = {'hrf': {'derivs': [time, dispersion]}}

        if f"{name}/temporal_noise_autocorrelation" in features:
            if f"{name}/temporal_noise_autocorrelation/AR1" in features:
                design.inputs.model_serial_correlations = 'AR(1)'
            if f"{name}/temporal_noise_autocorrelation/FAST" in features:
                design.inputs.model_serial_correlations = 'FAST'

        design.inputs.mask_threshold = 0.8
        design.inputs.volterra_expansion_order = 1
        return design

    def get_estimate(self):
        estimate = pe.Node(interface=EstimateModel(), name="Model_Estimation")
        estimate.inputs.estimation_method = {'Classical': 1}
        estimate.inputs.write_residuals = True
        return estimate

    def get_contrasts(self):
        contrast = pe.Node(interface=EstimateContrast(), name="Contrast_manager")
        contrast.inputs.contrasts = [
            ('listening > rest', 'T', ['listening'], [1]),
            ('rest > listening', 'T', ['listening'], [-1])
        ]
        return contrast
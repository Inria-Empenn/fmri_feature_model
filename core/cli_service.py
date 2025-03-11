import os
from datetime import datetime

import pandas as pd

from core.AAFM_service import AAFMService
from core.data_descriptor import DataDescriptor
from core.file_service import FileService, MEAN_NII, REF_NII, CORR_MEAN, CORR_REF, CORR, RESULT_NII
from core.stat_service import StatService
from core.workflow_service import WorkflowService


class CLIService:
    path2fm = '/home/ymerel/fmri-feature-model/model/uvl/preprocessing_pipeline.uvl'
    aafm_srv = AAFMService()
    file_srv = FileService()
    workflow_srv = WorkflowService()
    stat_srv = StatService()

    def get_sample(self, size):
        fm = self.aafm_srv.get_feature_model(self.path2fm)
        sample = self.aafm_srv.sample(fm, size)
        print(f"Sampled [{str(len(sample))}] configurations from [{self.path2fm}]")
        return sample

    def sample_run(self, data_desc: DataDescriptor, size: int):
        result_path = os.path.join(data_desc.result_path, datetime.now().strftime('%d%m%Y_%H%M%S'))
        os.makedirs(result_path, exist_ok=True)
        data_desc.result_path = result_path
        self.file_srv.write_data_descriptor(data_desc)

        conf_ids = []
        print(f"Sampling & running [{size}] configurations to [{result_path}]...")
        configs = self.get_sample(size)
        for config in configs:
            hashconf = self.file_srv.hash_config(config)
            conf_dir = os.path.join(result_path, hashconf)
            os.makedirs(conf_dir, exist_ok=True)
            conf_ids.append(hashconf)

            self.file_srv.write_config2csv(config, conf_dir)

            workflow = self.workflow_srv.build_workflow(config, data_desc, hashconf)
            self.workflow_srv.run(workflow, conf_dir)

            results = []
            for sub in data_desc.subjects:
                results.append(os.path.join(conf_dir, '_subject_id_', sub, RESULT_NII))

            print(f"Write mean result image for configuration [{hashconf}]...")
            self.file_srv.write_mean_image(results, os.path.join(conf_dir, MEAN_NII))

        self.run_ref(data_desc)
        conf_ids.append('ref')

        self.file_srv.merge_configs2csv(conf_ids, result_path)

        print(f"Sampling & running finished.")

    def mean(self, data_desc: DataDescriptor):
        result_path = data_desc.result_path
        niis = self.file_srv.list_all_nifti(result_path)
        mean_img = os.path.join(result_path, MEAN_NII)
        csv = os.path.join(result_path, CORR_MEAN)
        self.file_srv.write_mean_image(niis, mean_img)
        print(f"Computing correlations from mean [{mean_img}]...")
        correlations = self.stat_srv.compute_correlations(mean_img, niis)
        self.file_srv.write_dataframe2csv(correlations, csv)
        print(f"Correlations written to [{csv}]")

    def run_ref(self, data_desc: DataDescriptor):
        name = 'ref'
        result_path = data_desc.result_path
        conf_dir = os.path.join(result_path, name)
        os.makedirs(conf_dir, exist_ok=True)
        print(f"Running reference configuration to [{result_path}]...")

        fm = self.aafm_srv.get_feature_model(self.path2fm)
        config = self.aafm_srv.get_ref_config(fm)
        self.file_srv.write_config2csv(config, conf_dir)

        workflow = self.workflow_srv.build_workflow(config, data_desc, 'ref')
        self.workflow_srv.run(workflow, conf_dir)

        results = []
        for sub in data_desc.subjects:
            results.append(os.path.join(conf_dir, '_subject_id_', sub, RESULT_NII))

        print(f"Write mean result image for configuration [{name}]...")
        self.file_srv.write_mean_image(results, os.path.join(conf_dir, MEAN_NII))

        print(f"Running reference configuration finished")

        return conf_dir

    def ref(self, data_desc: DataDescriptor):
        result_path = data_desc.result_path
        ref = os.path.join(result_path, REF_NII)
        csv = os.path.join(result_path, CORR_REF)
        print(f"Computing correlations from reference [{ref}]...")
        if not os.path.exists(ref):
            print(f"Reference image [{ref}] does not exist.")
            return

        niis = self.file_srv.list_all_nifti(result_path)
        correlations = self.stat_srv.compute_correlations(ref, niis)
        self.file_srv.write_dataframe2csv(correlations, csv)
        print(f"Correlations written to [{csv}]")

    def correlations(self, data_desc: DataDescriptor):
        result_path = data_desc.result_path
        csv = os.path.join(result_path, CORR)
        niis = self.file_srv.list_all_nifti(result_path)
        print(f"Computing all correlations between [{len(niis)}] files...")
        dataframes = []
        for nii in niis:
            dataframes.append(self.stat_srv.compute_correlations(nii, niis))
        merged = pd.concat(dataframes, ignore_index=True)
        merged.sort_values(by='correlation', ascending=False)
        self.file_srv.write_dataframe2csv(merged, csv)
        print(f"Correlations written to [{csv}]")

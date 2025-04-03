import numpy as np

from aafm.AAFM_service import AAFMService


class SampleService:
    path2fm = '/home/ymerel/fmri-feature-model/model/uvl/full_pipeline.uvl'
    aafm_srv = AAFMService()

    def get_config_sample(self, size) -> list[dict]:
        fm = self.aafm_srv.get_feature_model(self.path2fm)
        configs = self.aafm_srv.sample(fm, size)
        sample = []
        for conf in configs:
            sample.append(conf.elements)

        print(f"Sampled [{str(len(sample))}] configurations from [{self.path2fm}]")

        return sample

    def get_all_configs(self) -> list[dict]:
        fm = self.aafm_srv.get_feature_model(self.path2fm)
        configs = self.aafm_srv.get_all_config(fm)
        all = []
        for conf in configs:
            all.append(conf.elements)
        print(f"Retrieved all [{str(len(all))}] configurations from [{self.path2fm}]")
        return all

    def get_ref_config(self) -> dict:
        fm = self.aafm_srv.get_feature_model(self.path2fm)
        config = self.aafm_srv.get_ref_config(fm)
        print(f"Sampled reference configuration from [{self.path2fm}]")
        return config.elements

import importlib
import json
import os

import datalad.api as dl
import numpy as np

from core.data_descriptor import DataDescriptor
from core.file_service import HCP_DS

DATASET_PATH = '/home/ymerel/hcp/'
URL = 'git@github.com:datalad-datasets/human-connectome-project-openaccess.git'

class HcpService:

    def read_release_notes(self):
        dataset = dict()
        path = os.path.join(DATASET_PATH, 'HCP1200')
        for subject in os.listdir(path):
            data = []
            for file in os.listdir(os.path.join(path, subject, 'release-notes')):
                if file.endswith('_unproc.txt'):
                    blocks = file.replace('_unproc.txt', '').split('_')
                    paradigm = blocks[0]
                    ttype = ''
                    if len(blocks) > 1:
                        ttype = blocks[1]
                    if paradigm == 'Structural':
                        ttype = "T2w_SPC1"
                    data.append({'paradigm': paradigm, 'type': ttype})
            dataset[subject] = data
        return dataset

    def write_dataset_desc(self):
        dataset = self.read_release_notes()
        with open(HCP_DS, 'w') as json_file:
            json.dump(dataset, json_file, indent=4)

    def download_subject_data(self, subject: str, data_desc: DataDescriptor):
        paths = [os.path.join(data_desc.data_path, data_desc.func_subpath.replace('{subject_id}', subject)),
                 os.path.join(data_desc.data_path, data_desc.func_subpath.replace('{subject_id}', subject))]

        dataset = self.get_dataset(data_desc.data_path)

        for path in paths:
            dataset.get(path)

    def get_dataset(self, path):
        return dl.Dataset(path)

    def sample_subjects(self, size: int):
        with importlib.resources.open_text('hcp', HCP_DS) as file:
            dataset = json.load(file)
            return np.random.choice(np.array(list(dataset.keys())), size=size, replace=False)

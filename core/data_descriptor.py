class DataDescriptor:
    data_path = ""
    anat_subpath = ""
    func_subpath = ""
    result_path = ""
    work_path = ""
    subjects = []
    slices_nb = 0
    tr = 0
    units = ""

    def __init__(self, data: {}):
        self.data_path = data["data_path"]
        self.anat_subpath = data["anat_subpath"]
        self.func_subpath = data["func_subpath"]
        self.result_path = data["result_path"]
        self.work_path = data["work_path"]
        self.subjects = data["subjects"]
        self.slices_nb = data["slices_nb"]
        self.tr = data["tr"]
        self.units = data["units"]

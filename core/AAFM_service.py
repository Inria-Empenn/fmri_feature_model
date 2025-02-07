from flamapy.core.discover import DiscoverMetamodels
from flamapy.core.models import VariabilityModel
from flamapy.core.operations import Operation

from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration


class AAFMService:
    dm = DiscoverMetamodels()

    def get_feature_model(self, path: str):
        """
        Serialize a .uvl file into a python object

        :param path: path to the .uvl file
        :return:
        """
        return self.dm.use_transformation_t2m(path, 'fm')

    def get_sat_model(self, feature_model: VariabilityModel):
        """

        :param feature_model: feature model to transform
        :return:
        """
        return self.dm.use_transformation_m2m(feature_model, "pysat")

    def get_bdd_model(self, feature_model: VariabilityModel):
        """

        :param feature_model: feature model to transform
        :return:
        """
        return self.dm.use_transformation_m2m(feature_model, "bdd")

    def is_satisfiable(self, fm: VariabilityModel) -> bool:
        """

        :param fm: feature model to check
        :return:
        """
        sat_model = self.get_sat_model(fm)
        operation = self.dm.get_operation(sat_model, 'PySATSatisfiable')
        operation.execute(sat_model)
        return operation.get_result()

    def sample(self, fm: VariabilityModel, size: int) -> list[Configuration]:
        """

        :param size: size of the sample
        :param fm: feature model to sample
        :return:
        """
        bdd_model = self.get_bdd_model(fm)
        operation = self.dm.get_operation(bdd_model, 'BDDSampling')
        operation.set_sample_size(size)
        operation.execute(bdd_model)
        return operation.get_result()


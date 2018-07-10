from adlib.learners.learner import Learner
from adlib.learners.models import sklearner
from typing import Dict


class SimpleLearner(Learner):
    """Simple Learner for initial learning methods.
    Defines the bare-minimum functionality for initial learning
    strategies.
    """

    def __init__(self, model=None, training_instances=None):
        Learner.__init__(self)
        if model:
            self.set_model(model)
        else:
            self.model = None
        self.training_instances = training_instances

    def set_model(self, model):
        self.model = sklearner.Model(model)

    def train(self):
        if not self.model:
            raise ValueError('Must specify classification model')
        if self.training_instances is None:
            raise ValueError('Must set training instances before training')
        self.model.train(self.training_instances)

    def predict(self, instances):
        """

        :param instances: feature matrix. shape (num_instances, num_feautres_per_instance)
        :return: array of predicted labels
        """
        return self.model.predict(instances)

    def predict_proba(self, testing_instances):
        return self.model.predict_proba(testing_instances)

    def predict_log_proba(self, testing_instances):
        return self.model.predict_log_proba(testing_instances)

    def decision_function(self, X):
        return self.model.learner.decision_function(X)

    def set_params(self, params: Dict):
        if params['model'] is not None:
            self.model = self.set_model(params['model'])

    def get_weight(self):
        weight = self.model.learner.coef_[0]
        return weight

    def get_constant(self):
        return self.model.learner.intercept_
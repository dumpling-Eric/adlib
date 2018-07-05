# alternating_trim_learner.py
# A learner that implements the Alternating TRIM algorithm.
# Matthew Sedam

from adlib.learners.learner import Learner
from adlib.utils.common import get_fvs_and_labels, logistic_loss
from copy import deepcopy
from typing import Dict
import cvxpy as cvx
import numpy as np


class AlternatingTRIMLearner(Learner):
    """
    A learner that implements the Alternating TRIM algorithm.
    """

    def __init__(self, training_instances, max_iter=10, verbose=False):

        Learner.__init__(self)
        self.set_training_instances(deepcopy(training_instances))
        self.max_iter = max_iter
        self.verbose = verbose

        self.poison_percentage = None
        self.n = None
        self.theta = None
        self.b = None

    def train(self):
        """
        Train on the set of training instances.
        """

        if len(self.training_instances) < 2:
            raise ValueError('Must have at least 2 instances to train.')

        step_size = 1 / len(self.training_instances)
        best_poison_percentage = 0.05
        best_theta = None
        best_b = None
        best_loss = None

        self.poison_percentage = 0.05
        self.n = int((1 - self.poison_percentage) *
                     len(self.training_instances))

        while self.poison_percentage < 0.5:
            loss = self._train_helper()
            if self.verbose:
                print('\nPoison Percentage:', self.poison_percentage, '- loss:',
                      loss, '\n')

            if not best_loss or loss < best_loss:
                best_poison_percentage = self.poison_percentage
                best_loss = loss
                best_theta = self.theta
                best_b = self.b

            self.poison_percentage += step_size
            self.n = int((1 - self.poison_percentage) *
                         len(self.training_instances))

        self.poison_percentage = best_poison_percentage
        self.n = int((1 - self.poison_percentage) *
                     len(self.training_instances))
        self.theta = best_theta
        self.b = best_b

    def _train_helper(self):
        """
        Helper function for train. Does the actual training.
        :return: the total loss
        """

        fvs, labels = get_fvs_and_labels(self.training_instances)
        tau = self._generate_tau()
        old_tau = np.full(len(tau), 0)
        tau_dist = int(np.linalg.norm(tau - old_tau) ** 2)
        iteration = 0

        while tau_dist != 0 and iteration < self.max_iter:
            if self.verbose:
                print('Iteration: ', iteration, ' - tau_dist: ', tau_dist,
                      sep='')

            # Setup variables
            theta = cvx.Variable(fvs.shape[1])
            b = cvx.Variable()

            # Setup CVXPY problem
            f_vector = []
            for vector in fvs:
                f_vector.append(sum(map(lambda x, y: x * y, vector, theta)) + b)

            tmp = []
            for i, val in enumerate(tau):
                if val == 1:
                    tmp.append(cvx.logistic(-1 * labels[i] * f_vector[i]))

            # Solve the minimization problem
            func = sum(tmp)
            problem = cvx.Problem(cvx.Minimize(func), [])
            problem.solve(solver=cvx.ECOS, verbose=self.verbose, parallel=True)

            self.theta = np.array(theta.value).flatten()
            self.b = b.value

            # Minimize based on loss
            loss = logistic_loss(self.training_instances, self)
            loss_sort_list = list(enumerate(loss))
            loss_sort_list.sort(key=lambda x: x[1])
            old_tau = deepcopy(tau)

            for i, val in enumerate(loss_sort_list):
                tau[val[0]] = 1 if i < self.n else 0

            tau_dist = int(np.linalg.norm(tau - old_tau) ** 2)
            iteration += 1

        if self.verbose:
            print('Iteration: FINAL - tau_dist: ', tau_dist, sep='')

        return sum(loss)

    def _generate_tau(self):
        """
        Generates a random tau, where tau[i] in {0, 1} for i in range(len(tau))
        and sum(tau) = self.n
        :return: tau
        """

        tau = np.random.binomial(1, 1 - self.poison_percentage,
                                 len(self.training_instances))

        total = sum(tau)
        while total != self.n:
            for i, val in enumerate(tau):
                if total > self.n:
                    if val == 1 and np.random.binomial(1, 0.5) == 1:
                        tau[i] = 0
                        break
                else:
                    if val == 0 and np.random.binomial(1, 0.5) == 1:
                        tau[i] = 1
                        break
            total = sum(tau)

        return tau

    def predict(self, instances):
        fvs, _ = get_fvs_and_labels(instances)
        decision_vals = self.decision_function(fvs)
        return list(map(lambda x: 1 if x >= 0 else -1, decision_vals))

    def set_params(self, params: Dict):
        if params['training_instances'] is not None:
            self.set_training_instances(deepcopy(params['training_instances']))
        if params['max_iter'] is not None:
            self.max_iter = params['max_iter']
        if params['verbose'] is not None:
            self.verbose = params['verbose']

        self.poison_percentage = None
        self.n = None
        self.theta = None
        self.b = None

    def predict_proba(self, X):
        raise NotImplementedError

    def decision_function(self, X):
        return X.dot(self.theta) + self.b
"""
Implements simple stochastic gradient optimisation.
It is inspired from `_stochastic_optimizers.py
<https://github.com/scikit-learn/scikit-learn/blob/master/sklearn/
neural_network/_stochastic_optimizers.py>`_.
"""
import numpy


class BaseOptimizer:
    """
    Base stochastic gradient descent optimizer.

    :param coef: array, initial coefficient
    :param learning_rate_init: float
        The initial learning rate used. It controls the step-size
        in updating the weights.

    The class holds the following attributes:

    * *learning_rate*: float, the current learning rate
    """

    def __init__(self, coef, learning_rate_init=0.1):
        if not isinstance(coef, numpy.ndarray):
            raise TypeError("coef must be an array.")
        self.coef = coef
        self.learning_rate_init = learning_rate_init
        self.learning_rate = float(learning_rate_init)

    def _get_updates(self, grad):
        raise NotImplementedError("Must be overwritten.")  # pragma no cover

    def update_coef(self, grad):
        """
        Updates coefficients with given gradient.

        :param grad: array, gradient
        """
        if self.coef.shape != grad.shape:
            raise ValueError("coef and grad must have the same shape.")
        update = self._get_updates(grad)
        self.coef += update

    def iteration_ends(self, time_step):
        """
        Performs update to learning rate and potentially other states at the
        end of an iteration.
        """
        pass  # pragma: no cover

    def train(self, X, y, fct_loss, fct_grad, max_iter=100,
              early_th=None, verbose=False):
        """
        Optimizes the coefficients.

        :param X: datasets (array)
        :param y: expected target
        :param fct_loss: loss function, signature: `f(coef, X, y) -> float`
        :param fct_grad: gradient function, signature: `g(coef, x, y) -> array`
        :param max_iter: number maximum of iteration
        :param early_th: stops the training if the error goes below
            this threshold
        :param verbose: display information
        :return: loss
        """
        if not isinstance(X, numpy.ndarray):
            raise TypeError("X must be an array.")
        if not isinstance(y, numpy.ndarray):
            raise TypeError("y must be an array.")
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y must have the same number of rows.")

        loss = fct_loss(self.coef, X, y)
        if verbose:
            self._display_progress(0, max_iter, loss)
        n_samples = 0
        for it in range(max_iter):
            irows = numpy.random.choice(X.shape[0], X.shape[0])
            for irow in irows:
                grad = fct_grad(self.coef, X[irow, :], y[irow])
                self.update_coef(grad)
                n_samples += 1

            self.iteration_ends(n_samples)
            loss = fct_loss(self.coef, X, y)
            if verbose:
                self._display_progress(it + 1, max_iter, loss)
            self.iter_ = it + 1
            if early_th is not None and loss <= early_th:
                break
        return loss

    def _display_progress(self, it, max_iter, loss):
        'Displays training progress.'
        print('{}/{}: loss: {:1.4g}'.format(it, max_iter, loss))


class SGDOptimizer(BaseOptimizer):
    """
    Stochastic gradient descent optimizer with momentum.

    :param coef: array, initial coefficient
    :param learning_rate_init: float
        The initial learning rate used. It controls the step-size
        in updating the weights,
    :param lr_schedule: `{'constant', 'adaptive', 'invscaling'}`,
        learning rate schedule for weight updates,
        `'constant'` for a constant learning rate given by
        *learning_rate_init*. `'invscaling'` gradually decreases
        the learning rate *learning_rate_* at each time step *t*
        using an inverse scaling exponent of *power_t*.
        `learning_rate_ = learning_rate_init / pow(t, power_t)`,
        `'adaptive'`, keeps the learning rate constant to
        *learning_rate_init* as long as the training keeps decreasing.
        Each time 2 consecutive epochs fail to decrease the training loss by
        tol, or fail to increase validation score by tol if 'early_stopping'
        is on, the current learning rate is divided by 5.
    :param momentum: float
        Value of momentum used, must be larger than or equal to 0
    :param power_t: double
        The exponent for inverse scaling learning rate.
    :param early_th: stops if the error goes below that threshold

    The class holds the following attributes:

    * *learning_rate*: float, the current learning rate
    * velocity*: array, velocity that are used to update params

    .. exref::
        :title: Stochastic Gradient Descent applied to linear regression

        The following example how to optimize a simple linear regression.

        .. runpython::
            :showcode:

            import numpy
            from aftercovid.optim import SGDOptimizer


            def fct_loss(c, X, y):
                return numpy.linalg.norm(X @ c - y) ** 2


            def fct_grad(c, x, y):
                return x * (x @ c - y) * 0.1


            coef = numpy.array([0.5, 0.6, -0.7])
            X = numpy.random.randn(10, 3)
            y = X @ coef

            sgd = SGDOptimizer(numpy.random.randn(3))
            sgd.train(X, y, fct_loss, fct_grad, max_iter=15, verbose=True)
            print('optimized coefficients:', sgd.coef)
    """

    def __init__(self, coef, learning_rate_init=0.1, lr_schedule='constant',
                 momentum=0.9, power_t=0.5, early_th=None):
        super().__init__(coef, learning_rate_init)
        self.lr_schedule = lr_schedule
        self.momentum = momentum
        self.power_t = power_t
        self.early_th = early_th
        self.velocity = numpy.zeros_like(coef)

    def iteration_ends(self, time_step):
        """
        Performs updates to learning rate and potential other states at the
        end of an iteration.

        :param time_step: int
            number of training samples trained on so far, used to update
            learning rate for 'invscaling'
        """
        if self.lr_schedule == 'invscaling':
            self.learning_rate = (float(self.learning_rate_init) /
                                  (time_step + 1) ** self.power_t)

    def _get_updates(self, grad):
        """
        Gets the values used to update params with given gradients.

        :param grad: array, gradient
        :return: updates, array, the values to add to params
        """
        update = self.momentum * self.velocity - self.learning_rate * grad
        self.velocity = update
        return update

    def _display_progress(self, it, max_iter, loss):
        'Displays training progress.'
        print('{}/{}: loss: {:1.4g} lr={:1.3g}'.format(
            it, max_iter, loss, self.learning_rate))

"""
.. module:: edna.ema
     :platform: Any
     :synopsis: moving average filter
"""

class EMA(object):
    """
    Exponential moving average filter with weighting coefficient *alpha*.
    Filters the input values :math:`Y_i` to produce the output values
    :math:`S_i` such that:

    .. math::

        S_1 = Y_1

        S_i = \\alpha*Y_i+(1-\\alpha)*S_{i-1}

    """
    def __init__(self, alpha: float):
        self._alpha = alpha
        self._inv = 1. - alpha
        self.s = None

    def __call__(self, y: float) -> float:
        if self.s is None:
            self.s = y
        else:
            self.s = self._alpha * y + self.s * self._inv
        return self.s

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, value: float):
        self._alpha = value
        self._inv = 1. - value

    def reset(self):
        """
        Reset the filter to its initial state.
        """
        self.s = None

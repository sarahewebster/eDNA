"""
Tests for the edna.periph module
"""
import edna.periph
import unittest


class PeriphTestCase(unittest.TestCase):
    def test_sawtooth(self):
        l = 100
        gen = edna.periph.sawtooth(l)
        # Integrate over one wavelength
        integral = sum([next(gen) for i in range(l)])
        # Integral should equal wavelength/2
        self.assertAlmostEqual(integral, float(l)/2.)


if __name__ == '__main__':
    unittest.main()

"""
Tests for the edna.config module
"""
from edna.config import Config, BadEntry
import unittest
import os.path
from io import StringIO


INPUT = """
[DEFAULT]
BASEDIR = /home/pi/eDNA

[System]
#where to put logs
LogDir = ${BASEDIR}/logs
DataDir = ${BASEDIR}/data

# Valves
[Valve.1]
Enable=27
Power=24
Gnd=25
[Foo]
Bar = 2.5
Baz = 42
Array = 5, 6, 7, 8
[Adc]
Addr=0x48
Gain=2/3
[Deployment]
Downcast = yes
"""

OVERRIDE = """
[Foo]
baz = 43
"""

class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.cfg = Config(StringIO(INPUT))
        self.cfg.load(StringIO(OVERRIDE))

    def test_get_int(self):
        x = self.cfg.get_int('Valve.1', 'Enable')
        self.assertEqual(x, 27)

    def test_get_int_hex(self):
        x = self.cfg.get_int('Adc', 'Addr')
        self.assertEqual(x, 0x48)

    def test_get_str(self):
        s = self.cfg.get_string('System', 'LogDir')
        self.assertEqual(s, "/home/pi/eDNA/logs")

    def test_get_float(self):
        x = self.cfg.get_float('Foo', 'Bar')
        self.assertEqual(x, 2.5)

    def test_get_array(self):
        x = self.cfg.get_array('Foo', 'Array')
        self.assertEqual(x, [5., 6., 7., 8.])

    def test_override(self):
        x = self.cfg.get_int('Foo', 'Baz')
        self.assertEqual(x, 43)

    def test_expr(self):
        x = self.cfg.get_expr('Adc', 'Gain')
        self.assertEqual(x, 2/3)

    def test_bad_key(self):
        self.assertRaises(BadEntry,
                          self.cfg.get_int,
                          'Valve.5', 'Enable')

    def test_get_bool(self):
        x = self.cfg.get_bool('Deployment', 'Downcast')
        self.assertEqual(x, True)

    def test_bool_default(self):
        x = self.cfg.get_bool('Foo', 'NotFound')
        self.assertEqual(x, False)


class ValidationTest(unittest.TestCase):
    def setUp(self):
        path = os.path.join(os.path.dirname(__file__), "example.cfg")
        self.cfg = Config(path)
        self.badcfg = Config(StringIO(INPUT))

    def test_validate(self):
        missing = self.cfg.validate()
        self.assertEqual(len(missing), 0)

    def test_validate_fail(self):
        missing = self.badcfg.validate()
        self.assertGreater(len(missing), 0)


if __name__ == '__main__':
    unittest.main()

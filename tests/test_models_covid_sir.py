"""
Unit tests for ``CovidSir``.
"""
import unittest
import numpy
from numpy.testing import assert_almost_equal
from aftercovid.models._base_sir import BaseSIR
from aftercovid.models.covid_sir import CovidSIR


class TestModelsCovidSir(unittest.TestCase):

    def test_base_sir(self):
        with self.assertRaises(TypeError):
            BaseSIR(('p', 0.5, 'PP'), [('q', 0.6, 'QQ')])
        with self.assertRaises(TypeError):
            BaseSIR([('p', 0.5, 'PP')], ('q', 0.6, 'QQ'))
        with self.assertRaises(TypeError):
            BaseSIR([('p', 0.5, 'PP')], [('q', 0.6, 'QQ')],
                    ('N', 0.6, 'NN'))
        with self.assertRaises(TypeError):
            BaseSIR([('p', 0.5, 'PP')], [('q', 0.6, 'QQ')],
                    [('N', 0.6, 'NN')], "r")
        models = BaseSIR([('p', 0.5, 'PP')], [('q', 0.6, 'QQ')],
                         [('N', 0.6, 'NN')])
        names = models.names
        self.assertEqual(names, ['N', 'p', 'q'])
        self.assertEqual(models['p'], 0.5)
        self.assertEqual(models['q'], 0.6)
        self.assertEqual(models['N'], 0.6)
        self.assertEqual(models.P, [('p', 0.5, 'PP')])
        self.assertEqual(models.Q, [('q', 0.6, 'QQ')])
        self.assertEqual(models.C, [('N', 0.6, 'NN')])
        with self.assertRaises(ValueError):
            models['qq']
        models['q'] = 6.1
        self.assertEqual(models['q'], 6.1)
        rst = models.to_rst()
        self.assertIn('*q*: QQ', rst)

    def test_covid_sir(self):
        model = CovidSIR()
        rst = model.to_rst()
        self.assertIn('\\frac', rst)
        self.assertIn('I', rst)
        par = model.get()
        self.assertIn('I', par)
        p = {'I': 5.}
        model.update(**p)
        par = model.get()
        self.assertEqual(par['I'], 5.)
        dot = model.to_dot(verbose=True)
        self.assertIn("I -> R", dot)
        self.assertNotIn("I -> I", dot)
        self.assertIn('beta', dot)
        self.assertNotIn('-beta', dot)
        dot = model.to_dot(verbose=True, full=True)
        self.assertIn("I -> I", dot)
        self.assertIn('-beta', dot)

    def test_covid_sir_eval(self):
        model = CovidSIR()
        cst = model.cst_param
        self.assertEqual(cst, {'N': 10000.0, 'beta': 0.5,
                               'mu': 0.07142857142857142,
                               'nu': 0.047619047619047616})
        ev = model.eval_diff()
        self.assertEqual(ev['S'], -4.995)
        self.assertEqual(len(ev), 4)

    def test_covid_sir_loop(self):
        model = CovidSIR()
        sim = list(model.iterate())
        self.assertEqual(len(sim), 10)
        self.assertTrue(sim[-1]['S'] >= 9500)
        self.assertTrue(sim[-1]['S'] < 10000)
        r0 = model.R0()
        self.assertEqual(r0, 4.2)

    def test_predict(self):
        model = CovidSIR()
        sim = list(model.iterate(derivatives=True))
        self.assertIsInstance(sim, list)
        X = model.iterate2array(derivatives=False)
        self.assertIsInstance(X, numpy.ndarray)
        X, y = model.iterate2array(derivatives=True)
        self.assertEqual(X.shape, y.shape)
        y2 = model.predict(X)
        assert_almost_equal(y / 100, y2 / 100, decimal=6)


if __name__ == '__main__':
    unittest.main()

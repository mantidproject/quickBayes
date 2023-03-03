import unittest
from quasielasticbayes.v2.workflow.template import Workflow
from quasielasticbayes.v2.functions.BG import LinearBG, FlatBG
from quasielasticbayes.v2.functions.composite import CompositeFunction
from quasielasticbayes.test_helpers.fitting_data import basic_data


class TestWorkflow(Workflow):
    def _update_function(self, func):
        """
        Add a flat BG term
        """
        bg = FlatBG()
        func.add_function(bg)
        return func


class WorkflowTemplateTest(unittest.TestCase):

    def setUp(self):
        self.func = CompositeFunction()
        lin = LinearBG()
        self.func.add_function(lin)
        results = {}
        errors = {}
        self.wf = TestWorkflow(results, errors)

    def test_preprocess_data(self):
        x, y, e = basic_data()
        self.wf.preprocess_data(x, y, e)
        self.assertEqual(len(self.wf._data), 3)
        self.assertEqual(len(self.wf._data['x']), len(x))
        self.assertEqual(len(self.wf._data['y']), len(y))
        self.assertEqual(len(self.wf._data['e']), len(e))
        for j in range(len(x)):
            self.assertEqual(self.wf._data['x'][j], x[j])
            self.assertEqual(self.wf._data['y'][j], y[j])
            self.assertEqual(self.wf._data['e'][j], e[j])

    def test_update_function(self):
        """
        Going to use get_guess to tell if the
        function has had anything added to it
        """
        self.assertEqual(len(self.func.get_guess()), 2)
        self.assertEqual(self.func._prefix, '')
        func = self.wf.update_function(self.func, 1)
        self.assertEqual(len(self.func.get_guess()), 3)
        for j, function in enumerate(func._funcs):
            self.assertEqual(function._prefix, f'N1:f{j + 1}.')

    def test_get_parameters_and_errors(self):
        params, errors = self.wf.get_parameters_and_errors
        self.assertEqual(params, {})
        self.assertEqual(errors, {})

        # setup workflow + generate data
        x, y, e = basic_data()
        self.wf.preprocess_data(x, y, e)
        self.wf.set_scipy_engine([0], [-9], [9])
        _ = self.wf.execute(1, self.func)
        # check parameters and errors updated
        params, errors = self.wf.get_parameters_and_errors
        self.assertEqual(len(params), 4)
        self.assertEqual(len(errors), 3)
        expected_keys = ['N1:f1.BG gradient',
                         'N1:f1.BG constant',
                         'N1:f2.BG constant']

        self.assertEqual(list(errors.keys()), expected_keys)
        expected_param = [0.986, 0.061, 0.061]
        expected_error = [0.045, 0.041, 0.041]
        for j, key in enumerate(expected_keys):
            self.assertAlmostEqual(params[key][0], expected_param[j], 3)
            self.assertAlmostEqual(errors[key][0], expected_error[j], 3)

        prob_key = 'N1:loglikelihood'
        expected_keys.append(prob_key)
        self.assertEqual(list(params.keys()), expected_keys)
        self.assertAlmostEqual(params[prob_key][0], -17.290, 3)

    def test_fails_if_no_data(self):
        with self.assertRaises(ValueError):
            self.wf.set_scipy_engine([0], [-9], [9])

    def test_execute_no_engine(self):
        x, y, e = basic_data()
        self.wf.preprocess_data(x, y, e)
        with self.assertRaises(ValueError):
            _ = self.wf.execute(1, self.func)

    def test_add_second_engine_errors(self):
        x, y, e = basic_data()
        self.wf.preprocess_data(x, y, e)
        self.wf.set_scipy_engine([0], [-9], [9])
        with self.assertRaises(RuntimeError):
            self.wf.set_scipy_engine([0], [-9], [9])

    def test_set_scipy_engine(self):
        self.assertEqual(self.wf.fit_engine, None)
        x, y, e = basic_data()
        self.wf.preprocess_data(x, y, e)
        self.wf.set_scipy_engine([], [], [])
        self.assertEqual(self.wf.fit_engine.name, 'scipy')


if __name__ == '__main__':
    unittest.main()

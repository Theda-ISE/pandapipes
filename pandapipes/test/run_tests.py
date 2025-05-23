# Copyright (c) 2020-2022 by Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel, and University of Kassel. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import os
import shutil
import tempfile

import pytest

from pandapipes.test import test_path, tutorials_path

try:
    import coverage as cov
except ImportError:
    pass
from pandapower.test.run_tests import _get_cpus

try:
    import pandaplan.core.pplog as logging
    # logger = logging.getLogger()
    # for handler in logger.handlers:
    #     logger.removeHandler(handler)
except ImportError:
    import logging

logger = logging.getLogger()
for handler in logger.handlers:
    logger.removeHandler(handler)
    logger.setLevel(logging.CRITICAL)


def _get_test_dir(pp_module=None):
    # helper function to get the test dir and check if it exists
    test_dir = test_path
    if pp_module is not None and isinstance(pp_module, str):
        test_dir = os.path.join(test_dir, pp_module)
    if not os.path.isdir(test_dir):
        raise ValueError("test_dir {} is not a dir".format(test_dir))
    return test_dir


def run_tests(parallel=False, n_cpu=None, coverage=False):
    """
    Function to execute all tests or the tests in a module.

    :param parallel: If true and pytest-xdist is installed, tests are run in parallel
    :type parallel: bool, default False
    :param n_cpu: number of CPUs to run the tests on in parallel. Only relevant for parallel runs.
    :type n_cpu:int, default None
    :param coverage: creates some coverage with coverage module
    :type coverage: bool, default False
    :return: No Output.
    """

    test_dir = _get_test_dir()

    if coverage:
        cov_tracker = cov.Coverage()
        cov_tracker.start()

    if parallel:
        if n_cpu is None:
            n_cpu = _get_cpus()
        err = pytest.main([test_dir, "-xs", "-n", str(n_cpu)])
        if err == 4:
            raise ModuleNotFoundError("Parallel testing not possible. Please make sure that "
                                      "pytest-xdist is installed correctly.")
        elif err > 2:
            logger.error("Testing not successfully finished.")
    else:
        pytest.main([test_dir, "-xs"])

    if coverage:
        cov_tracker.stop()
        cov_tracker.save()
        cov_tracker.html_report(ignore_errors=True)


def run_tutorials(parallel=False, n_cpu=None):
    """
    Function to execute all tutorials / jupyter notebooks.

    Copies the whole "tutorials" folder to a temporary folder which is removed after all
    notebooks have been executed. Errors in the notebooks show up as Failures.
    For further options on nbmake, visit
    https://semaphoreci.com/blog/test-jupyter-notebooks-with-pytest-and-nbmake

    :param parallel: If true and pytest-xdist is installed, jupyter notebooks are run in parallel
    :type parallel: bool, default False
    :param n_cpu: number of CPUs to run the files on in parallel. Only relevant for parallel runs.
    :type n_cpu: int, default None
    :return: No return value.
    """
    try:
        import nbmake
    except (ImportError, ModuleNotFoundError) as e:
        raise ModuleNotFoundError(f"Testing of jupyter notebooks requires the pytest extension "
                                  f"'nbmake'. Please make sure that nbmake is installed correctly."
                                  f"\nError message: {e}")

    # run notebooks in tempdir to safely remove output files
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(tutorials_path, os.path.join(tmpdir, "tmp"))
        test_dir = tmpdir

        if parallel:
            if n_cpu is None:
                n_cpu = 'auto'
            err = pytest.main(["--nbmake", f"-n={n_cpu}", test_dir])
            if err == 4:
                raise ModuleNotFoundError("Parallel testing not possible. Please make sure "
                                          "that pytest-xdist is installed correctly.")
            elif err > 2:
                logger.error("Testing not successfully finished.")
        else:
            pytest.main(["--nbmake", test_dir])


if __name__ == "__main__":
    run_tests()
    # run_tutorials()
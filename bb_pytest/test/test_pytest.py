# Pytest support for Buildbot.
# Copyright (C) 2012 Russell Sim

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
from subprocess import Popen
from os.path import abspath, dirname

from twisted.trial import unittest
from buildbot.status.results import SUCCESS, FAILURE, WARNINGS
from buildbot.test.util import steps
from buildbot.test.fake.remotecommand import ExpectShell
from buildbot.process.properties import Property

from bb_pytest import step


class Pytest(steps.BuildStepMixin, unittest.TestCase):

    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def test_run_env(self):
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              testpath=None,
                              env={'PYTHONPATH': 'somepath'}))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config",
                        env=dict(PYTHONPATH='somepath'))
            + ExpectShell.log('stdio', stdout="collected 0 items\n")
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=['no tests', 'run'])
        return self.runStep()

    def test_run_env_supplement(self):
        self.setupStep(
                step.Pytest(workdir='build',
                            tests='testname',
                            testpath='path1',
                            env={'PYTHONPATH': ['path2', 'path3']}))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config",
                        env=dict(PYTHONPATH=['path1', 'path2', 'path3']))
            + ExpectShell.log('stdio', stdout="collected 0 items\n")
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=['no tests', 'run'])
        return self.runStep()

    def test_run_env_nodupe(self):
        self.setupStep(
                step.Pytest(workdir='build',
                            tests='testname',
                            testpath='path2',
                            env={'PYTHONPATH': ['path1', 'path2']}))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config",
                        env=dict(PYTHONPATH=['path1', 'path2']))
            + ExpectShell.log('stdio', stdout="collected 0 items\n")
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=['no tests', 'run'])
        return self.runStep()

    def test_run_singular(self):
        self.setupStep(
                step.Pytest(workdir='build',
                                     tests='testname',
                                     testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio', stdout="""collected 2 items

==== 1 passed in 11.1 seconds =====
""")
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=['1 test', 'passed'])
        return self.runStep()

    def test_run_plural(self):
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio', stdout="""collected 2 items

==== 2 passed in 11.1 seconds =====
""")
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=['2 tests', 'passed'])
        return self.runStep()

    def testProperties(self):
        self.setupStep(step.Pytest(workdir='build',
                                     tests=Property('test_list'),
                                     testpath=None))
        self.properties.setProperty('test_list', ['testname'], 'Test')

        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio', stdout="""collected 2 items

==== 2 passed in 11.1 seconds =====
""")
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=['2 tests', 'passed'])
        return self.runStep()

    def test_run_plural_with_failures(self):
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout="""collected 3 items
==== 1 failed, 2 passed, 0 skipped in 10.1 seconds =====
""")
            + 1
        )
        self.expectOutcome(result=FAILURE,
                           status_text=['3 tests', '1 failure'])
        return self.runStep()

    def test_run_plural_with_skips(self):
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout="""collected 3 items
==== 0 failed, 2 passed, 1 skipped in 11.1 seconds =====
""")
            + 0
        )
        self.expectOutcome(result=SUCCESS,
                           status_text=['3 tests', 'passed', '1 skip'])
        return self.runStep()

    def test_run_with_xfail(self):
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout="""collecting ... collected 12 items

===== 5 passed, 2 skipped, 4 deselected, 1 xfailed in 0.02 seconds =====
""")
            + 0
        )
        self.expectOutcome(result=SUCCESS,
                           status_text=['12 tests', '2 skips', '1 todo', '4 deselected'])
        return self.runStep()

    def test_run_with_passing_xfail(self):
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout="""collecting ... collected 11 items

===== 3 failed, 4 passed, 2 skipped, 1 xfailed, 1 xpassed in 0.03 seconds ======
""")
            + 0
        )
        self.expectOutcome(result=SUCCESS,
                           status_text=['11 tests', '2 skips', '1 todo', '1 surprises'])
        return self.runStep()

    def test_run_with_deselected(self):
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout="""collected 11 items

===== 6 tests deselected by "-m 'not failure and not skipped'" =====
==== 5 passed, 6 deselected in 0.01 seconds ====
""")
            + 0
        )
        self.expectOutcome(result=SUCCESS,
                           status_text=['11 tests', 'passed', '6 deselected'])
        return self.runStep()

    def test_fail_run_with_deselected(self):
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              pytestMode="xdist",
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout="""============================= test session starts ==============================
platform linux2 -- Python 2.6.5 -- pytest-2.3.4 -- /usr/bin/python
plugins: xdist
collecting ... collected 11 items

------------------------------- Captured stderr --------------------------------
2013-04-04 08:35:48,752 INFO Starting new HTTP connection (1): example.com
===== 6 tests deselected by "-m 'not failure and not skipped'" =====
==== 1 failed, 4 passed, 6 deselected in 0.01 seconds ====
""")
            + 1
        )
        self.expectOutcome(result=FAILURE,
                           status_text=['11 tests', '1 failure', '6 deselected'])
        return self.runStep()

    def test_run_with_error(self):
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout="""collecting ... collected 11 items

================== 408 tests deselected by "-m 'serialtest'" ===================
======== 1 failed, 2 passed, 1 deselected, 3 error in 9.46 seconds ========
""")
            + 1
        )
        self.expectOutcome(result=FAILURE,
                           status_text=['7 tests', '1 failure', '3 errors', '1 deselected'])
        return self.runStep()


MODULE_DIR = abspath(dirname(__file__))
FIXTURE_PATH = MODULE_DIR + "/fixture.py"


def call_pytest():
    print FIXTURE_PATH
    print ['py.test', FIXTURE_PATH]
    pytest = Popen(['py.test', FIXTURE_PATH],
                   stdout=subprocess.PIPE)
    return pytest.communicate()


class PytestIntegration(steps.BuildStepMixin, unittest.TestCase):

    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def test_pytest_problems(self):
        pytest_stdout = open(MODULE_DIR + "/fixture.stdout").read()
        pytest_problems = open(MODULE_DIR + "/fixture.problems").read()
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout=pytest_stdout)
            + 1
        )
        self.expectOutcome(result=FAILURE,
                           status_text=['9 tests', '3 failures', '2 skips'])
        self.expectLogfile(logfile='problems', contents=pytest_problems)

        return self.runStep()

    def test_pytest_problems(self):
        pytest_stdout = open(MODULE_DIR + "/fixture_failures.stdout").read()
        pytest_problems = open(MODULE_DIR + "/fixture_failures.problems").read()
        self.setupStep(
                step.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout=pytest_stdout)
            + 1
        )
        self.expectOutcome(result=FAILURE,
                           status_text=['53 tests', '37 failures'])
        self.expectLogfile(logfile='problems', contents=pytest_problems)

        return self.runStep()

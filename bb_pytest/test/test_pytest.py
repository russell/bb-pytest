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

from twisted.trial import unittest
from bb_pytest import pytest
from buildbot.status.results import SUCCESS, FAILURE
from buildbot.test.util import steps
from buildbot.test.fake.remotecommand import ExpectShell
from buildbot.process.properties import Property


class Trial(steps.BuildStepMixin, unittest.TestCase):

    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def test_run_env(self):
        self.setupStep(
                pytest.Pytest(workdir='build',
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
                pytest.Pytest(workdir='build',
                                     tests='testname',
                                     testpath='path1',
                                     env={'PYTHONPATH': ['path2','path3']}))
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
                pytest.Pytest(workdir='build',
                              tests='testname',
                              testpath='path2',
                              env={'PYTHONPATH': ['path1','path2']}))
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
                pytest.Pytest(workdir='build',
                                     tests='testname',
                                     testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio', stdout="collected 1 items\n")
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=['1 test', 'passed'])
        return self.runStep()

    def test_run_plural(self):
        self.setupStep(
                pytest.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio', stdout="collected 2 items\n")
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=['2 tests', 'passed'])
        return self.runStep()

    def testProperties(self):
        self.setupStep(pytest.Pytest(workdir='build',
                                     tests=Property('test_list'),
                                     testpath=None))
        self.properties.setProperty('test_list', ['testname'], 'Test')

        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio', stdout="collected 2 items\n")
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=['2 tests', 'passed'])
        return self.runStep()

    def test_run_plural_with_failures(self):
        self.setupStep(
                pytest.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout="collected 3 items\n==== 1 failed, 2 passed, 0 skipped in 10.1 seconds =====\n")
            + 1
        )
        self.expectOutcome(result=FAILURE, status_text=['3 tests', '1 failure'])
        return self.runStep()

    def test_run_plural_with_skips(self):
        self.setupStep(
                pytest.Pytest(workdir='build',
                              tests='testname',
                              testpath=None))
        self.expectCommands(
            ExpectShell(workdir='build',
                        command=['py.test', '-v', 'testname'],
                        usePTY="slave-config")
            + ExpectShell.log('stdio',
                              stdout="collected 3 items\n==== 0 failed, 2 passed, 1 skipped in 11.1 seconds =====\n")
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=['3 tests', 'passed', '1 skip'])
        return self.runStep()

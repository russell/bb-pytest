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

from __future__ import absolute_import
from __future__ import print_function
from future.builtins import range

import re

from twisted.internet import defer
from twisted.python import log

from buildbot.process.results import FAILURE
from buildbot.process.results import SKIPPED
from buildbot.process.results import SUCCESS
from buildbot.process.results import WARNINGS
from buildbot.process import logobserver
from buildbot.process.buildstep import BuildStep
from buildbot.process.buildstep import ShellMixin


RE_LINE_COLLECTING = re.compile(r"^(collecting .*)(collected)(.*)(items)$")
RE_LINE_COLLECTED = re.compile(r"^(collected)(.*)(items)$")
RE_LINE_FAILURES = re.compile(r"^=+ FAILURES =+$")
RE_LINE_RESULTS = re.compile(r"=+ ((?P<failures>\d+) failed|)(,? ?(?P<passed>\d+) passed|)(,? ?(?P<skips>\d+) skipped|)(,? ?(?P<deselected>\d+) deselected|)(,? ?(?P<expectedFailures>\d+) xfailed|)(,? ?(?P<unexpectedSuccesses>\d+) xpassed|)(,? ?(?P<error>\d+) error|) in [\d.]+ seconds =+")
RE_TEST_MODES = {
    "pytest": re.compile(r"^(?P<path>.+):\d+: (?P<testname>.+) (?P<status>.+)$"),
    "xdist": re.compile(r"^\[.+\] (?P<status>.+) (?P<path>.+):\d+: (?P<testname>.+)$")
    }


class PytestTestCaseCounter(logobserver.LogLineObserver):

    def __init__(self, pytestMode):
        self._line_regexp = RE_TEST_MODES[pytestMode]
        self.numTests = 0
        self.totalTests = 0
        self.finished = False
        self.collecting = True
        self.testing = False
        self.catching = False
        logobserver.LogLineObserver.__init__(self)

    def outLineReceived(self, line):
        # line format
        # fixture.py:28: test_test4 PASSED
        # or xdist output
        # [gw1] PASSED fixture.py:4: test_test
        if self.finished:
            return

        if (not self.testing) and (not self.catching):
            if self.step.verbose:
                m = RE_LINE_COLLECTING.search(line.strip())
            else:
                m = RE_LINE_COLLECTED.search(line.strip())
            if m:
                try:
                    collected = m.group(3 if self.step.verbose else 2)
                    self.totalTests = int(collected)
                    self.step.description.extend(["0", "of", str(self.totalTests), "tests"])
                    self.step.updateSummary()
                    self.testing = True
                    self.collecting = False
                    self.catching = False
                except:
                    self.totalTests = -1
            return

        # testing mode
        if self.testing and line.startswith("="):
            m = RE_LINE_FAILURES.search(line.strip())
            if m:
                self.step.catched_failures.append(line)
                self.testing = False
                self.catching = True
                return

        if (self.testing or self.catching) and line.startswith("="):
            # check for final row with summary
            m = RE_LINE_RESULTS.search(line.strip())
            if m:
                self.step.collected_results.update(dict([(k, 0 if v is None else int(v)) for k, v in m.groupdict().items()]))
                self.step.collected_results["total"] = self.totalTests
                self.step.description = [self.step.description[0], "finished"]
                self.step.updateSummary()
                self.finished = True
                self.testing = False
                self.catching = False
                return
 
        if self.testing and line.strip():
            self.numTests += 1
            self.step.description[1] = str(self.numTests)
            self.step.updateSummary()
            return
  
        if self.catching:
            self.step.catched_failures.append(line)
            return


UNSPECIFIED = ()  # since None is a valid choice
class Pytest(BuildStep, ShellMixin):
    """
    There are some class attributes which may be usefully overridden
    by subclasses. 'pytestArgs' can influence the pytest command line.
    """
    DEFAULT_PYTEST = 'pytest'

    name = "pytest"
    progressMetrics = ('output', 'tests')

    description = ["testing"]
    descriptionDone = ["testing", "finished"]

    renderables = ['tests']
    flunkOnFailure = True
    python = None
    pytest = DEFAULT_PYTEST
    pytestMode = "pytest"
    pytestArgs = []
    verbose = True # verbose by default
    testpath = UNSPECIFIED  # required (but can be None)
    testChanges = False  # TODO: needs better name
    tests = None  # required

    collected_results = {
        'total': 0,
        'failures': 0,
        'skips': 0,
        'error': 0,
        'deselected': 0,
        'expectedFailures': 0,
        'unexpectedSuccesses': 0,
        }

    catched_failures = []

    def __init__(self, python=None, pytest=None,
                 testpath=UNSPECIFIED,
                 tests=None, testChanges=None, verbose=True,
                 pytestMode=None, pytestArgs=None,
                 **kwargs):
        """
        @type  testpath: string
        @param testpath: use in PYTHONPATH when running the tests. If
                         None, do not set PYTHONPATH. Setting this to '.' will
                         cause the source files to be used in-place.

        @type  python: string (without spaces) or list
        @param python: which python executable to use. Will form the start of
                       the argv array that will launch pytest. If you use this,
                       you should set 'pytest' to an explicit path (like
                       /usr/bin/pytest or ./bin/pytest). Defaults to None, which
                       leaves it out entirely (running 'pytest args' instead of
                       'python ./bin/pytest args'). Likely values are 'python',
                       ['python2.2'], ['python', '-Wall'], etc.

        @type  pytest: string
        @param pytest: which 'pytest' executable to run.
                      Defaults to 'pytest', which will cause $PATH to be
                      searched and probably find /usr/bin/pytest . Innnnf you set
                      'python', this should be set to an explicit path (because
                      'python2.3 pytest' will not work).

        @type pytestMode: string
        @param pytestMode: a specific test parser to use. Options are pytest
                          or xdist.  Default pytest.

        @type pytestArgs: list of strings
        @param pytestArgs: a list of arguments to pass to pytest, available to
                          turn on any extra flags you like. Defaults to ['-v'].

        @type verbose: boolean
        @param verbose: if True, pytest runs in verbose mode (-v), othervise not verbose.

        @type  tests: list of strings
        @param tests: a list of test modules to run, like
                      ['twisted.test.test_defer', 'twisted.test.test_process'].
                      If this is a string, it will be converted into a one-item
                      list.

        @type  testChanges: boolean
        @param testChanges: if True, ignore the 'tests' parameter and instead
                            ask the Build for all the files that make up the
                            Changes going into this build. Pass these filenames
                            to pytest and ask it to look for test-case-name
                            tags, running just the tests necessary to cover the
                            changes.

        @type  kwargs: dict
        @param kwargs: parameters. The following parameters are inherited from
                       L{ShellCommand} and may be useful to set: workdir,
                       haltOnFailure, flunkOnWarnings, flunkOnFailure,
                       warnOnWarnings, warnOnFailure, want_stdout, want_stderr,
                       timeout.
        """
        if python:
            self.python = python
        if self.python is not None:
            if isinstance(self.python, str):
                self.python = [self.python]
            for s in self.python:
                if " " in s:
                    # this is not strictly an error, but I suspect more
                    # people will accidentally try to use python="python2.3
                    # -Wall" than will use embedded spaces in a python flag
                    log.msg("python= component '%s' has spaces")
                    log.msg("To add -Wall, use python=['python', '-Wall']")
                    why = "python= value has spaces, probably an error"
                    raise ValueError(why)

        if pytest:
            self.pytest = pytest
        if " " in self.pytest:
            raise ValueError("pytest= value has spaces")
        if pytestMode is not None:
            self.pytestMode = pytestMode
        if pytestArgs is not None:
            self.pytestArgs = pytestArgs
        if verbose is not None:
            self.verbose = verbose

        if testpath is not UNSPECIFIED:
            self.testpath = testpath
        if self.testpath is UNSPECIFIED:
            raise ValueError("You must specify testpath= (it can be None)")
        assert isinstance(self.testpath, str) or self.testpath is None

        if tests is not None:
            self.tests = tests
        if isinstance(self.tests, str):
            self.tests = [self.tests]
        if testChanges is not None:
            self.testChanges = testChanges

        if not self.testChanges and self.tests is None:
            raise ValueError("Must either set testChanges= or provide tests=")

        if not self.pytestMode in RE_TEST_MODES:
            raise ValueError("pytestMode must be one of: %s" % ", ".join(RE_TEST_MODES.keys()))

        kwargs = self.setupShellMixin(kwargs, prohibitArgs=['command'])
        super(Pytest, self).__init__(**kwargs)

        self.observer = PytestTestCaseCounter(self.pytestMode)
        self.addLogObserver('stdio', self.observer)


    @defer.inlineCallbacks
    def run(self):
        """
        run PyTest
        """
        # build up most of the command, then stash it until start()
        command = []
        if self.python:
            command.extend(self.python)
        command.append(self.pytest)
        command.extend(self.pytestArgs)
        if self.verbose:
            command.append("-v")

        if self.testChanges:
            for f in self.build.allFiles():
                if f.endswith(".py"):
                    command.append("--testmodule=%s" % f)
        else:
            command.extend(self.tests)

        self.command = command

        if self.testpath is not None:
            # this bit produces a list, which can be used
            # by buildbot_worker.runprocess.RunProcess
            ppath = self.env.get('PYTHONPATH', self.testpath)
            if isinstance(ppath, str):
                ppath = [ppath]
            if self.testpath not in ppath:
                ppath.insert(0, self.testpath)
            self.env['PYTHONPATH'] = ppath

        cmd = yield self.makeRemoteShellCommand(command=command)

        self.collected_results = {
            'total': 0,
            'failures': 0,
            'skips': 0,
            'error': 0,
            'deselected': 0,
            'expectedFailures': 0,
            'unexpectedSuccesses': 0,
            }
        self.catched_failures = []

        yield self.runCommand(cmd)

        self.descriptionDone = self.finalDescription(cmd)
        self.updateSummary()

        if self.catched_failures:
            self.addCompleteLog("problems", "\n".join(self.catched_failures))

        defer.returnValue(cmd.results())


    def finalDescription(self, cmd):
        # figure out all status, then let the various hook functions return
        # different pieces of it

        total = self.collected_results['total']

        if total is None:
            results = FAILURE
            return ["testlog", "unparseable"]

        failures = self.collected_results['failures']
        errors = self.collected_results['error']
        skips = self.collected_results['skips']
        expectedFailures = self.collected_results['expectedFailures']
        unexpectedSuccesses = self.collected_results['unexpectedSuccesses']
        deselected = self.collected_results['deselected']
        passed = 0

        if cmd.rc == 0:
            results = SUCCESS
        else:
            # something failed
            results = FAILURE

        text = []
        if total:
            passed = total
            text.append("total %d %s" % (total, total == 1 and "test" or "tests"))
        else:
            text.extend(["no tests", "run"])

        if failures:
            passed -= failures
            text.append("%d %s" % (failures, "failed"))

        if errors:
            passed -= errors
            text.append("%d %s" % (errors, errors == 1 and "error" or "errors"))

        if skips:
            passed -= skips
            text.append("%d %s" % (skips, "skiped"))

        if expectedFailures:
            passed -= expectedFailures
            text.append("%d %s" % (expectedFailures, expectedFailures == 1 and "todo" or "todos"))

        if unexpectedSuccesses:
            passed -= unexpectedSuccesses
            text.append("%d %s" % (unexpectedSuccesses, "surprises"))

        if deselected:
            passed -= deselected
            text.append("%d %s" % (deselected, "deselected"))

        if passed < total:
            text.append("%d" % passed)

        if total:
            text.append("passed")

        return text

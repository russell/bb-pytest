bb_pytest
=========

bb_pytest is a library that adds a `Buildbot`_ buildstep that can
parse py.test output and generate correct status text at completion of
tests.

Arguments
---------

This test step is derived from the ShellCommand step.  So besides the
arguments listed below the following steps will also be accpeted and
will behave as per the ShellCommand step: workdir, haltOnFailure,
flunkOnWarnings, flunkOnFailure, warnOnWarnings, warnOnFailure,
want_stdout, want_stderr, timeout


testpath
  The PYTHONPATH to use when running the tests.

python
  The python executable to use.

pytest
  The pytest executable to use.

pytestMode
  The mode that should used to track the progress of the step. Valid
  options are "pytest" or "xdist".

Example
-------

.. code:: python

  from bb_pytest import step
  from buildbot.process import factory 

  f = factory.BuildFactory()

  f.Factory.addStep(
      Pytest(
          pytest="py.test",
          pytestArgs=['-u', '-i'],
          testpath=None,
          tests=[""],
          flunkOnFailure=True))


.. _buildbot: http://trac.buildbot.net/

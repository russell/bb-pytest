from setuptools import setup, find_packages
from os import path

version = '0.2'

changelog_header = """
Changelog
=========

"""

desc_file = path.join(path.dirname(__file__), "README.rst")
changelog_file = path.join(path.dirname(__file__), "CHANGELOG.rst")
description = open(desc_file).read() + changelog_header + open(changelog_file).read()


setup(name='bb-pytest',
      version=version,
      description="Buildbot step for py.test.",
      long_description=description,
      classifiers=[],  # Get strings from
                       #http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Russell Sim',
      author_email='russell.sim@gmail.com',
      url='https://github.com/russell/bb-pytest',
      license='GPL',
      packages=find_packages(exclude=['tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )

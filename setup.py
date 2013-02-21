from setuptools import setup, find_packages

version = '0.1'

setup(name='bb-pytest',
      version=version,
      description="Buildbot step for py.test.",
      long_description="""\
""",
      classifiers=[],  # Get strings from
                       #http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Russell Sim',
      author_email='russell.sim@gmail.com',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )

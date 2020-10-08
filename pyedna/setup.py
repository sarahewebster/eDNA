from setuptools import setup


setup(name='edna',
      description='Data acquisition software for the eDNA project',
      url='https://github.com/sarahewebster/eDNA',
      author='Michael Kenney',
      author_email='mikek@apl.uw.edu',
      license='GPL',
      packages=['edna', 'edna.apps'],
      install_requires=[],
      entry_points = {
      },
      zip_safe=False)

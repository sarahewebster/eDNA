from setuptools import setup


setup(name="edna",
      use_scm_version = {
          "root": "..",
          "relative_to": __file__,
          "local_scheme": "node-and-timestamp"
      },
      setup_requires=['setuptools_scm'],
      description="Data acquisition software for the eDNA project",
      url="https://github.com/sarahewebster/eDNA",
      author="Michael Kenney",
      author_email="mikek@apl.uw.edu",
      license="MIT",
      packages=["edna", "edna.apps"],
      package_data={"edna": ["py.typed", "resources/eDNA.cfg"],
                    "edna.apps": ["py.typed"]},
      install_requires=[
          'importlib-metadata ~= 1.0 ; python_version < "3.8"'
      ],
      python_requires="~=3.7",
      entry_points = {
          "console_scripts": [
              "runedna=edna.apps.runedna:main",
              "pumptest=edna.apps.pumptest:main",
              "prtest=edna.apps.prtest:main",
              "installcfg=edna.apps.installcfg:main"
          ]
      },
      zip_safe=False)

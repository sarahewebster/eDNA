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
      package_data={"edna": ["py.typed"],
                    "edna.apps": ["py.typed"]},
      install_requires=[],
      entry_points = {
          "console_scripts": [
              "runedna=edna.apps.runedna:main",
              "pumptest=edna.apps.pumptest:main",
              "prtest=edna.apps.prtest:main"
          ]
      },
      zip_safe=False)

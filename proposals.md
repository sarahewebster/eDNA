# Proposed software updates

## Near term

1. Move to a single data file. Newline-delimited JSON (ndjson) is a good candidate because it is somewhat "self describing" and can be processed with most programming languages.
2. Move Python code into a package.
3. Replace init scripts with Systemd service files.
4. Split the current configuration file into a "system configuration" file and a deployment file. The user should never need to change the system configuration file.

## Longer term

1. Collect all base OS modifications into one or more Debian package(s). This will simplify the process of building a new system.
2. Add unit tests for Python code
3. Ensure Python code passes a style checker test (e.g. [Flake8](https://flake8.pycqa.org/en/latest/)

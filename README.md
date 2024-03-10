# latextools

This is a collection of simple tools that may be useful when preparing journal papers with LaTeX.

The tools are implemented in Python and packaged as a Python package for ease of use.

Since there is an existing Python package named `latextools` on PyPI, the package name might be changed in the future.

## Installation
If you use Python and pip:
```
pip install git+https://github.com/ycwang-astro/latextools.git
```

For Windows users that do not use Python: you may download the executables in the [release page](https://github.com/ycwang-astro/latextools/releases/latest), and use `latexport.exe` or `authtex.exe` in your terminal.

## Documentation

This package consists of 2 tools:
- latexport: This tool makes it simpler to merge your LaTeX manuscript files, and generate a minimum set of files (that can be complied, and have no subdirectories), ready to be submitted to a website or journal. See [documentation](docs/latexport.md) for detials.
- authtex: This tool makes it simpler to change your manuscript from one journal to another. Author+affiliation information is stored in a separate file; the LaTeX codes for them can be generated for different journals. See [documentation](docs/authtex.md) for details.

These tools can be used in the terminal after installing this package. You can always check the usage by:
```
latexport -h
```
and
```
authtex -h
```

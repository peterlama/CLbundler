CLbundler
=========

A tool for creating and maintaining packages of pre-compiled libraries.

CLbundler _formulas_ are used to build and install software packages into a _bundle_. A _bundle_ is simply a directory containing a database that keeps track of all the information needed to manage the packages.

### Installation
Simply clone the repository to somewhere on your computer, and add the location of `CLbundler/bin` to the PATH environment variable.
To run CLbundler you will need Python >= 2.6.x < 3.x.

### Configuration
By default, CLbundler will download source code to `CLbundler/workspace/src_cache` and will create the builds in `CLbundler/workspace`. This can be changed in the configuration file: `CLbundler/CLbundler.cfg`

### Documentation
`clbundler --help` for general usage, and [Formula Development Guide](https://github.com/peterl94/CLbundler/wiki/Formula-Development-Guide) for information on creating CLbundler formulas.

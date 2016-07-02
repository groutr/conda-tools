A collection of Python modules and tools for working with the conda packaging system.

These modules provide, what I think, are useful abstractions for modeling information about conda environments and packages.

The core of the implementation are a collection of classes that act as interfaces to various stores of information in the conda packaging system.
These classes are designed to be read-only and for only querying information.
 * PackageInfo: Represents an extracted package in the package cache.  It allows easy access to everything in index.json and each file under the info/ directory.
 * Environment: An interface to a conda environment. Allows easy access to bits of information about an environment found in the conda-meta/ directory.
 * History: The history file parser from conda, adapted to be read-only.  Designed to allow Environment objects access to the states stored in the history file.

The methods of the classes are read-only lazy properties.  This means that for an instance of a class, the filesystem is only touched once to read the file.  The contents of that file are then cached in memory. To update the information in property, a new instance of the class must be created, which will prompt another read from the filesystem upon property access.

Creating instances of the core classes should be low overhead.  The classes, upon initialization, check that an expected structure is present.  No files are read at instantiation.  Thus a large number of instances can be created relatively quickly (as fast as a few os.path.exists() calls).
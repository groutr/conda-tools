A collection of Python modules and tools for working with the conda packaging system.  The package itself does not depend conda.

These modules provide, what I think, are useful abstractions for modeling information about conda environments and packages.
Some of the useful queries are:
 1. List packages that are not linked to any environment
    ```
    import cache_utils
    cache_utils.unlinked_packages(cache_path, envs_path)
    ```
 2. List all environments a package is linked to
    ```
    import cache_utils
    cache_utils.all_linked_environments(cache_path, envs_path)
    ```
 3. List all environments
    ```
    import environment

    environment.named_environments(envs_path)
    ```
 4. List all packages in cache
    ```
    import cache

    cache.named_cache(cache_path)
    ```
 5. List all files in package/environment that are not hardlinked from the cache
    ```
    import environment_utils

    environment_utils.
    ```
 6. List all packages that were explicitly installed by the user
 7. List all channels used by an environment
 8. How is each package linked to an environment (soft-linked, hard-linked, or copied)
 9. Which package(s) owns a file path

The core of the implementation are a collection of classes that act as interfaces to various stores of information in the conda packaging system.
These classes are designed to be read-only and for only querying information.
 * PackageInfo: Represents an extracted package in the package cache.  It allows easy access to everything in index.json and each file under the `info/` directory.
 * Environment: An interface to a conda environment. Allows easy access to bits of information about an environment found in the `conda-meta/` directory.
 * History: The history file parser from conda, adapted to be read-only.  Designed to allow Environment objects access to the states stored in the history file.

The methods of the classes are read-only lazy properties.  This means that for an instance of a class, the filesystem is only touched once to read the file.  The contents of that file are then cached in memory. To update the information in property, a new instance of the class must be created, which will prompt another read from the filesystem upon property access.

Creating instances of the core classes should be low overhead.  The classes, upon initialization, check that an expected structure is present.  No files are read at instantiation.  Thus a large number of instances can be created relatively quickly (as fast as a few os.path.exists() calls).

Several convenience functions for environments and package caches are located in `environment_utils.py` and `cache_utils.py` respectively.
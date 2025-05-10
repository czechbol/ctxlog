Installation
============

Requirements
-----------

ctxlog requires Python 3.9 or higher.

Installing from PyPI
-------------------

Install ctxlog from PyPI using pip:

.. code-block:: bash

    pip install ctxlog

Alternativelly use other package managers like `uv`, `pipx` or `poetry`:

.. code-block:: bash

    pipx install ctxlog
    uv add ctxlog
    poetry add ctxlog

Installing from Source
--------------------

You can also install ctxlog from source using pip:

.. code-block:: bash

    git clone https://github.com/czechbol/ctxlog.git
    cd ctxlog
    pip install -e .

Or use `poetry`:

.. code-block:: bash

    git clone https://github.com/czechbol/ctxlog.git
    cd ctxlog
    poetry install

Development Installation
----------------------

For development, you can install ctxlog with development dependencies:

.. code-block:: bash

    pip install -e ".[dev]"

This will install the package in development mode along with testing and linting tools.

Documentation Dependencies
------------------------

To build the documentation, you need to install the documentation dependencies:

.. code-block:: bash

    pip install -e ".[docs]"

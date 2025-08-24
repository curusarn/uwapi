Setup Python
============
Instructions to install Python:

.. tab-set::
   :sync-group: platform

   .. tab-item:: Windows
      :sync: windows

      .. warning::
         Do *not* use ``Python install manager``. It causes a lot of issues.

      .. important::
         In the installer wizard, make sure to add python to system path.

      Install latest stable version of python from: https://www.python.org/downloads/windows/.

      Update pip (package manager for python):

      .. code-block:: bash

         python -m pip install --upgrade pip

   .. tab-item:: Linux
      :sync: linux

      Install python using system package manager:

      .. code-block:: bash

         sudo apt update
         sudo apt install python3-dev python3-pip

Install mandatory dependencies:

.. code-block:: bash

   pip install cffi

Optionally install tools for python type checking:

.. code-block:: bash

   pip install pyright mypy types-cffi


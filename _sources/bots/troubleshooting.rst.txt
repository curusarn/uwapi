Troubleshooting
===============

.. important::
	Do *not* use Flatpak for Steam on Linux.

.. dropdown:: Unable to load DLL 'unnatural-uwapi-hard'

	Make sure you have installed Unnatural Worlds in Steam.

	If your Steam games are in non-default location, define environment variable ``UNNATURAL_ROOT`` to the directory containing the library.

.. dropdown:: OSError: cannot load library 'unnatural-uwapi-hard'

	Make sure you have installed Unnatural Worlds in Steam.

	If your Steam games are in non-default location, define environment variable ``UNNATURAL_ROOT`` to the directory containing the library.

.. dropdown:: Failed to initialize Steam API

	Make sure that Steam is running and logged in.  
	It must run under the same user as the program.
	Do not use any containerization.

.. dropdown:: Linux laptop with switchable GPUs

	To run using nvidia gpu:

	.. code-block:: bash

		__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia your_program

	Alternatively, define these two environment variables in your IDE to be used when debugging your program.

.. dropdown:: Corrupted game files

	Shut down Steam - click on the icon in the status bar, choose *Exit Steam*.
	Make sure that no Steam processes are running.
	Remove the whole folder ``Unnatural Worlds`` with the game.
	Start steam again, select UW in the library, click the settings (looks like a gear), *Properties...*, in the pop-up window select *Installed Files* tab, and click *Verify integrity of game files*.
	This will force Steam to download the whole game again.

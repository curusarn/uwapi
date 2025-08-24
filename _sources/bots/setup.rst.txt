Setup
=====
You can write your bot in any language, as long as it can load a dynamic/shared library (.dll/.so).
The shared library is distributed together with the game.

The uwapi repository contains c/c++ headers for all functions and structures provided by the library.
Furthermore, it contains convenient wrappers for Python and C# for easy start.

.. important::
   Do *not* use Flatpak, or Snap, or any other containerization for Steam on Linux.

Steam Appid Txt
---------------

.. important::
   Copy ``steam_appid.txt`` into the ``bin`` folder.

The file ``steam_appid.txt`` tells Steam that this is developer copy of the game.
It allows running multiple processes of the game simultaneously, and to start the programs directly from outside the Steam.
This allows you to start and debug your bot program from inside your IDE.
You may also start the game client, game server, built-in AI, or any other associated programs from your terminal.
You will find the ``steam_appid.txt`` in the uwapi repository.
Copy it into the ``bin`` folder, next to the game executable.

It is recommended to remove the ``steam_appid.txt`` when you are done with your AI/bot program.
Presence of the file may cause corruption of some files when the game is updated.

Game Install Path
-----------------

.. important::
   If you installed Unnatural World in non-default location, define environment variable ``UNNATURAL_ROOT`` pointing to the ``bin`` directory containing the library.

.. tab-set::
   :sync-group: platform

   .. tab-item:: Windows
      :sync: windows

      Default path: ``C:\Program Files (x86)\Steam\steamapps\common\Unnatural Worlds\bin``

   .. tab-item:: Linux
      :sync: linux

      Default path: ``~/.steam/steam/steamapps/common/Unnatural Worlds/bin``

Show Extra Information
----------------------

In the game, navigate to *Options*, *User Interface*, and change *Selected info level* to *Extra*.
This will show you additional information about any single thing you select in the game.
For example: unit id, its state, position (both index and 3D coordinates), etc.
It shows at the bottom of the left panel.

Enable *Detailed tooltips* too.

Program State
=============
The program state is controlled by several independent variables.

Game State
----------

- ``None`` - the game is initializing.
- ``Session`` - players are connecting, and are negotiating the map and other settings. An admin will start the game.
- ``Preparation`` - countdown before the game actually starts. This alerts players to get ready.
- ``Starting`` - briefly used between the transition from ``Preparation`` to ``Game``.
  This state is best used for initialization - all forces already know their real race (in case of random), and their starting positions.
- ``Game`` - game is in progress.
- ``Pause`` - some players have requested the game to pause. It will return to the ``Game`` state when all players are ready again.
- ``CutscenePaused`` - the game is playing a cut-scene, and game time is stopped. It will return to the ``Game`` state when the cut-scene finishes.
- ``CutsceneRunning`` - the game is playing a cut-scene, and simulation continues. It will return to the ``Game`` state when the cut-scene finishes.
- ``Finish`` - game is over. Winners and defeated have been declared.

Map State
---------

- ``None`` - no map is set to load.
- ``Downloading`` - the map is not available locally and is being downloaded.
- ``Loading`` - the map is being loaded.
- ``Loaded`` - map is fully available. This is the only state when you can access any of the functions that interact with the map.
- ``Unloading`` - the map is being unloaded.
- ``Error`` - loading a map has encountered an error. Loading is cancelled.

.. warning::
   Do *not* access any of the map-related functions unless the map is ``Loaded``.

Accessing any of the map-related functions when the map is *not* ``Loaded`` will crash the game, since all data are loaded concurrently.

Connection State
----------------

- ``None`` - there is no connection. Do *not* send any commands.
- ``Connecting`` - connection is being attempted. You may send commands, they will be delivered once the connection is established.
- ``Connected`` - connection has been fully established. We are receiving data, and can send commands.
- ``Error`` - connection has been closed or broken. Do *not* send any commands.

Ticks
-----
Ticks are the measurement of time in the game simulation.

When ticks are ticking, units are moving.
When tick is the same, no units are moving, no one is shooting, etc.

There are 20 ticks per second, by default.
This is provided as a constant in the api.

Program Overview
================
High-level look at basic bot program.

Accessor Objects
-----------------

These are globally accessible objects that you use to interact with the game.

.. tab-set::
   :sync-group: language

   .. tab-item:: Python
      :sync: python

      - ``uw_admin`` - managing the game server and other players; requires administrator privilege on the game server.
      - ``uw_commands`` - sending commands and orders to your units, and queries for current orders.
      - ``uw_events`` - register your callbacks here.
      - ``uw_game`` - managing game connection, and other settings.
      - ``uw_map`` - queries about tiles, clusters, etc; data that do *not* change during game.
      - ``uw_prototypes`` - access to all prototypes; they do *not* change during game.
      - ``uw_world`` - list all entities, and some additional queries for data that do change during game.

   .. tab-item:: C#
      :sync: csharp

      - ``Admin`` - managing the game server and other players; requires administrator privilege on the game server.
      - ``Commands`` - sending commands and orders to your units, and queries for current orders.
      - ``Events`` - register your callbacks here.
      - ``Game`` - managing game connection, and other settings.
      - ``Map`` - queries about tiles, clusters, etc; data that do *not* change during game.
      - ``Prototypes`` - access to all prototypes; they do *not* change during game.
      - ``World`` - list all entities, and some additional queries for data that do change during game.

Program Lifetime
----------------
At start, you are in full control of the program.

Initialization
^^^^^^^^^^^^^^

1) Change current working directory to the ``bin`` directory in the game installation.
   Without it, the game will be unable to load maps and assets (even if it might happen to load the shared library).

.. warning::
   Do *not* change current working directory afterwards.

2) Load the shared library.

.. tab-set::
   :sync-group: language

   .. tab-item:: Python
      :sync: python

      Class UwapiLibrary is responsible for loading the library.
      This is done in the ``main.py``.

   .. tab-item:: C#
      :sync: csharp

      The library is automatically loaded when you first access the global ``Events`` object.
      This happens inside the ``Bot`` constructor.

3) Setup all callbacks now.
   You may also set some parameters for the connection.

Connect
^^^^^^^
There are multiple ways to connect to a game server.
The usual approach is to first try reconnecting, in case the game has crashed previously.
Second, you connect to an existing game server using parameters provided in the environment, if any.
Third, you spin up your own game server.

Alternatively, you may implement your own logic to determine how to connect to a server.

No matter the method, the game will now take control over the program.
Your program is blocked until the network connection closes.
*All your further actions will happen inside callbacks only.*

Game Loop
^^^^^^^^^
All your registered callbacks are now called, when appropriate.
Notably, the ``Update`` callback is periodically called, no matter the game state.
This is where you keep track of the state of the game, and perform any of your actions.

.. warning::
   The ``Update`` callback, and some others, may be called before the game has actually started (eg. in ``Session``), or when the map is not yet ``Loaded``.
   Be mindful of what operations are valid in these circumstances.

You may prematurely close the connection with the ``disconnect`` function.
This will do a graceful closing of the connection, that is, you will get some additional callbacks called.
After that the connect function will return.

Finalization
^^^^^^^^^^^^
When the connection function returns, the network connection has already been closed, and you take back control over the program.
You may do any cleanup operations, for example you may save some statistics from the game.
Ultimately, you should unload the shared library, and exit the program.

It may be tempting to just loop over and connect to next server, however this is strongly discouraged.

Network
-------
The game is designed for multiplayer, and always plays over network, even in single-player scenarios.

Any actions that you do in your program are first send to the game server, then processed, and then the results are send back to your client.

Example: you call a function to place a construction.
After that you look through all the entities and the construction is not there, as expected.
You will not know the id of the entity either.
The construction will appear only after the game server has processed the request.
It is recommended to wait several ticks between these kinds of actions, to avoid placing same construction multiple times in different places.

.. note::
   Test your program over a real network, not just localhost.

Client-only State
^^^^^^^^^^^^^^^^^
Some state is stored on client only, notably:

- Units orders
- Pathfinding
- Logistics planning

Environment Variables
---------------------
Some variables that may alter the behavior of your bot program.

- ``UNNATURAL_ROOT`` - path to the ``bin`` folder that contains the shared library.
- ``UNNATURAL_CONNECT_LOBBY`` - id of Steam lobby to connect to.
- ``UNNATURAL_CONNECT_ADDR`` - IP address or domain name to connect to.
- ``UNNATURAL_CONNECT_PORT`` - port of the game server to connect to.

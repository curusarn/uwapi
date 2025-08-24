Performance
===========
Some hints on improving performance.

Distribute Work Over Multiple Ticks
-----------------------------------
Most events in the game take some time: shooting, moving, building, processing, etc.
Therefore, it is generally unnecessary to keep updating everything all the time.

It is recommended to split work between multiple ticks to save some cpu time.
Use switch on ``workStep++ mod 10``, and update different systems (eg. analyzing enemies, controlling armies, building, etc..).
Note the use of ``workStep``, which is different variable than the tick provided by the game.
This is to ensure continuous processing of all systems in case that some game ticks are skipped.

Be mindful of potential changes in the game state (eg. entities being destroyed) in between processing different systems.

Performance Statistics
----------------------
The game provides several statistics related to performance, which you can monitor and adapt your program.

- mainThreadUtilization - fraction (0..1) of the time the main thread does any work, vs time it sleeps.
- ping - network round-trip time measured in milliseconds.
- networkUp - network bandwidth use measured in KB/s, from client to game server.
- networkDown - same going from game server to client.

Profiling
---------
The game has built-in performance profiler.
When enabled, it will open a browser with real-time flame-graphs of tasks running on all threads in the game client.

You may also inject your own profiling events.

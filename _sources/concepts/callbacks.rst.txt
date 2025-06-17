Callbacks
=========

Game/Map/Connection State Callback
----------------------------------
Viz :ref:`concepts/programState:Game State`, :ref:`concepts/programState:Map State`, and :ref:`concepts/programState:Connection State`.

Update Callback
---------------
This callback is called every time the simulation time progresses (:ref:`tick <concepts/programState:Ticks>` changes).
It is also called when game time is not progressing (eg. when paused, or in session), but real time elapses.
The difference is indicated with the ``stepping`` parameter.

This callback is the primary driving point for your program.

.. note::
	Some ticks may be skipped, eg. when the game is lagging.
	Use ``>=`` when waiting for number of ticks to pass.

Shooting Callback
-----------------
Shooting events are synchronized *asynchronously and unreliably*.
This event is useful for measuring threat levels.

.. warning::
	The entity id may be expired.

Explosions Callback
-------------------
Explosions events are synchronized *asynchronously and unreliably* - some events may be lost, or delivered much later.
Do *not* depend on explosions events for important decisions.
It is useful for measuring threat levels.

.. warning::
	The entity id may be expired.

Task Completed Callback
-----------------------
Some functions, such as pathfinding and clusters distances, need more time to compute the results.
The calculations happen on separate threads internally in the uwapi library.
Finally, this callback is called, passing in the results, when it finishes.

This callback may be called at any time, relative to other callbacks - there are no guarantees.

.. warning::
	Do *not* try to wait (blocking) for the tasks.
	It will block the whole program indefinitely.

.. warning::
	Any entity id may have expired by the time the task completed.

Force Eliminated Callback
-------------------------
This informs you that a force/player lost.

Chat Callback
-------------
You have received a message. Chat events are synchronized *asynchronously*.

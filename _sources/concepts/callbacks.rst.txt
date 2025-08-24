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

Shootings Callback
------------------
Shootings events are synchronized *asynchronously and unreliably*.
This event is useful for measuring threat.

The data encode multiple events, possibly of different types, mixed together.
Make sure to carefully decode them, as shown in the example below.

.. warning::
   The entity id may be expired.

.. tab-set::
   :sync-group: language

   .. tab-item:: Python
      :sync: python

      .. code-block:: python

          def shootings_callback(data: List[int]) -> None:
              index = 0
              while index < len(data):
                  control = uw_events.shooting_control_data(data[index])
                  if control.type == UwShootingEventEnum.Shooting:
                      shooter_id = data[index + 1]
                      for i in range(1, control.count):
                          target_id = data[index + i + 1]
                          # handle shooting event
                          pass
                  index += control.count + 1

   .. tab-item:: C#
      :sync: csharp

      .. code-block:: csharp

          void ShootingsCallback(IReadOnlyList<uint> data)
          {
              int index = 0;
              while (index < data.Count)
              {
                  var control = Events.ShootingControlData(data[index]);
                  if (control.type == UwShootingEventEnum.Shooting)
                  {
                      uint shooterId = data[index + 1];
                      for (uint i = 1; i < control.count; i++)
                      {
                          uint targetId = data[index + i + 1];
                          // handle data event
                      }
                  }
                  index += control.count + 1;
              }
          }

   .. tab-item:: C++
      :sync: cpp

      .. code-block:: cpp

          extern "C"
          void uwShootingsCallback(const UwShootingsArray *data)
          {
          	const auto shooting = uw::makeVector(data);
          	uint32 index = 0;
          	while (index < shooting.size())
          	{
          		const auto control = uw::shootingControlData(shooting[index]);
          		if (control.type == UwShootingEventEnum_Shooting)
          		{
          			const uint32 shooterId = shooting[index + 1];
          			for (uint32 i = 1; i < control.count; i++)
          			{
          				const uint32 targetId = shooting[index + i + 1];
          				// handle shooting event
          			}
          		}
          		index += control.count + 1;
          	}
          }


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

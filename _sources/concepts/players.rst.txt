Players & Forces
================
Usually, there is one-to-one mapping between players and forces.
But the game is designed for other modes too.

Players
-------
Each client connected to the game server is separate player.
Each player has a name, and an avatar.
Finally, each player is associated with up to one force.

Observers
^^^^^^^^^
A player that is not associated with any force is an observer.

Forces
------
Forces represent the actual armies in the world.
Each force has associated a color, a starting position, and a race.
Each unit has associated owner - one of the forces.

Controllers
^^^^^^^^^^^
Notice that multiple players can be associated with one force.
In that case, these players share ownership of all the units associated with the force.

Each unit remembers the last player that gave it any order, this player is called the controller.
Any automated system in the game (eg. logistics controls for trucks) will not give any orders to units with different controller.

.. note::
	Controllers are only partially implemented in the game for now.

Neutral
^^^^^^^
Some units in the game are not associated with any force.
These are neutral rocks, trees, decorations, ore deposits, etc.

Foreign Policies
----------------
Each force has associated a policy with each other force.
Policies define how armies of different forces act towards each other.

Two forces can be allies, neutral, or enemies with each other.

The game has additional enumeration values for some edge cases.

Diplomacy
^^^^^^^^^

.. note::
	Diplomacy is not yet implemented.

Teams
^^^^^
Before a match starts, all forces are assigned into teams.
All forces in same team are assigned as allies with each other.
Forces in different teams are assigned as enemies.
Teams are not used afterwards.

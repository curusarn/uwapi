Entities & Components
=====================

.. epigraph::

	.. image:: /_static/ecs.svg
		:alt: ECS Diagram from Wikipedia
		:height: 100pt
		:align: right

	"Entity–component–system (ECS) is a software architectural pattern mostly used in video game development for the representation of game world objects. An ECS comprises entities composed from components of data, with systems which operate on the components.

	ECS follows the principle of composition over inheritance, meaning that every entity is defined not by a type hierarchy, but by the components that are associated with it. Systems act globally over all entities which have the required components."

	— `Wikipedia - Entity Component System <https://en.wikipedia.org/wiki/Entity_component_system>`_

Entity
------
In Unnatural Worlds specifically, each entity is identified by its unique 32-bit integer.
These ids are assigned by the server, and client cannot predict the values.

.. note::
	An id may be reused, especially in longer game.

.. note::
	Some entities and/or components are synchronized only with the owner of the entity.

Proto Component
---------------
Defines the prototype of the entity.

It is allowed to change from construction to unit, or from unit to another unit.
It is forbidden to change eg. from unit to resource.

Owner Component
---------------
Defines which force owns this entity.

Immutable.

Controller Component
--------------------
In case that multiple players belong to the same force, the last player to give any orders to this entity will become the controller of the entity.

.. note::
	Controllers are not yet implemented.

Position Component
------------------
Index of the tile this entity is placed on.
In case the entity has large radius, this component defines the center tile.

The yaw defines the orientation (a rotation along the local vertical axis) of this entity on the tile.
The actual facing of 0 degrees yaw is different for each tile.

Unit Component
--------------
Contains additional state for a unit (or building).

- ``Shooting`` - waiting for the cannon to cool down.
- ``Processing`` - the unit has processed a recipe and is waiting for it to complete.
- ``Rebuilding`` - recipe for the unit has changed, and the unit is waiting for the changes to complete.
- ``Stalling`` - the unit's recipe cannot be executed, usually because a limit for the outputs has been reached.
- ``Damaged`` - the unit has less than half life.

Life Component
--------------
Amount of life of the unit (or building).

Mana Component
--------------
Amount of mana of the unit (or building).

Move Component
--------------
Contains information about current movement of the unit.
Information is available for the next neighboring tile only.

Aim Component
-------------
Id of a target unit that this unit will automatically shoot at.

Recipe Component
----------------
Id of the prototype of the recipe that this unit will automatically process.

Recipe Statistics Component
---------------------------
Used for calculating this unit's processing efficiency.

It is reset when the recipe changes.

Logistics Timestamp Component
-----------------------------
Contains a timestamp (tick) of when this construction started, or when this unit's recipe was last processed.
It is used for planning logistics deliveries.

Priority Component
------------------
Contains the priority assigned by the player.
The priority applies to both constructions and recipe processing.
It is used by the logistics planning.

Amount Component
----------------
Contains the count of the resource in this entity.

Attachment Component
--------------------
Defines that this entity is attached to another entity.
This entity is automatically moved to the position (and orientation) of the target.
This is commonly used by a resource carried by a truck.

Ping Component
--------------
This entity represents a signal sent by an ally.

- ``Attention`` - generic warning signal.
- ``Attack`` - request to attack this location.
- ``Defend`` - request to quard this location.
- ``Rally`` - prepare troops there and await further signals.
- ``Build`` - build base in this location.
- ``Evacuate`` - request to leave this area.

Player Component
----------------
This entity represents a client - a player or an observer.

Player Ai Config Component
--------------------------
Behavioral configuration for AI player.

Force Component
---------------
This entity represents a force.
The component contains public information about the force.

Force Details Component
-----------------------
This component contains private information about the force.

Foreign Policy Component
------------------------
This entity declares the policy between two forces.

Diplomacy Proposal Component
----------------------------
This entity contains a proposal of a policy to another force.

.. note::
	Diplomacy is not yet implemented.

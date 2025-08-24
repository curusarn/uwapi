Prototypes
==========
Prototypes are data definitions used for everything in the game.
They are loaded with the map, and are immutable.

Each prototype is identified by its id, which is a hash of its name (the full path in the source files).

Resource Prototype
------------------
Defines properties of a resource - aka a crate/pallet/barrel that would exist in the world.

Recipe Prototype
----------------
Defines a transformation of resources, units, and upgrades.
It contains amounts and ids of inputs and outputs.
Also defines the duration of the recipe.
Recipes are processed in buildings/units.

Some recipes have a *place-over* requirement, which is an id of a unit prototype, that the building must be placed on, in order for the recipe to operate.

Construction Prototype
----------------------
Constructions are similar to recipes, but are manually placed into the world by the player.
It contains amounts of input resources, and has exactly one output unit/building.

Unit Prototype
--------------
Both buildings and units are treated as units in the game.

.. note::
   Some neutral objects, such as trees, rocks, ore deposits, etc. are units too.

The prototype contains combat related properties, movement speeds or building radius, a list of available recipes, and a list of applicable upgrades.
Additionally, there are several boolean properties, which modify behavior or requirements of the unit/building.

Upgrade Prototype
-----------------
Upgrades improve combat or economy of specified units/buildings of the same player.
The upgrade itself defines the improvements that it will apply, and units have a list of upgrades that may be applied to them.

The upgrades are temporary, and will disappear after specified duration.
Multiple same upgrades stack together, up to a specified limit.

Race Prototype
--------------
Each player selects one race that they play as.
The race defines their starting resources and units, and a list of available constructions.

Note that neither resources, recipes, units, or upgrades are inherently associated with any particular race.
There are no restrictions on units that the player may control, if they get hold of them.

Tags
----
All prototypes may have associated some tags with them.
Tags are short strings (mapped to unique ids), that are provided by the game/map/mods to help programs understand the nuances of that particular prototype.
Tags are *not* used by the game, except by the built-in AI/bot, which uses tags to alter behavior of some units.
Tags may be used by both Bots and Scripts.

- ``ambush`` - walks over additional terrain types.
- ``artillery`` - longer range than most.
- ``assault`` - good for front-line combat.
- ``harassment`` - good for hit-and-run attacks, especially targeting workers.
- ``home`` - the center of your base. dont let it die.
- ``miner`` - generates resources, usually from ore deposits.
- ``navy`` - moves on water only.
- ``noncombat`` - not intended for combat, even if it has an attack/explosion.
- ``nonprogression`` - an alternative for another prototype (this tag is used to break cyclic dependencies).
- ``production`` - produces more units.
- ``research`` - produces upgrades.
- ``scout`` - fast and cheap, good as a scout.
- ``siege`` - designed for destroying buildings.
- ``splash`` - area-of-effect attack/explosion.
- ``suicidal`` - sacrifices itself when attacking.
- ``tank`` - defensive unit with life above typical.
- ``tower`` - stationary defensive structure.
- ``volatile`` - may damage own/allied units.
- ``wall`` - stationary path blocking structure.
- ``worker`` - carries resources, automatic control by logistics planning.

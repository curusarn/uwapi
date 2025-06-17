Program Safety
==============
Memory and threads guarantees of the api.

Memory
------

Memory ownership is never transferred across the api boundary.
Usually, any pointers returned from any of the *c* functions are valid until next call to the same function.
Therefore, most *c* functions are *not* reentrant.

The Python and C# wrappers functions always copy all necessary memory from the provided pointers into the managed memory of the language.
Be careful if you use a *c* function directly.

Threads
-------

.. important::
	The api is strictly single-threaded!

Hardened Library
----------------
We provide a separate library that contains additional validation of correct use of the api.
The library will provide you an opportunity to stop the program in debugger when a problem is detected.
It will terminate the program afterwards.
This library is the default.

It is recommended to use the optimized (non-hardened) library when not actively developing your bots, or when in a tournament game.

.. tab-set::
   :sync-group: language

   .. tab-item:: Python
      :sync: python

      TODO

   .. tab-item:: C#
      :sync: csharp

      Define ``UW_USE_OPTIMIZED_LIBRARY`` macro to use non-hard library.



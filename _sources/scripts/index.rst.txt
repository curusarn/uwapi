Scripts
=======
Guide on making scripts for custom maps for Unnatural Worlds.

.. warning::
	Making custom scripts is not yet fully supported.

Scripts are executed within the server.
They have access to all data within the game, and may modify all data.

Scripts can be written in any language that can be compiled into `WASM <https://en.wikipedia.org/wiki/WebAssembly>`_.

The uwapi repository provides c/c++ headers for scripts.
If you want to use another language, you will need to specify all the imported functions and structures yourself.

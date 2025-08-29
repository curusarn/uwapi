from uwapi import UwapiLibrary
from bot2 import JuggernautBot

if __name__ == "__main__":
    with UwapiLibrary():
        JuggernautBot().run()
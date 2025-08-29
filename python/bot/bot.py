import random
from uwapi import *


class Bot:
    is_configured: bool = False
    work_step: int = 0  # save some cpu cycles by splitting work over multiple steps

    def __init__(self):
        uw_events.on_update(self.on_update)

    def attack_nearest_enemies(self):
        own_units = [
            x
            for x in uw_world.entities().values()
            if x.own() and x.Unit is not None and x.proto().data.get("dps", 0) > 0
        ]
        if not own_units:
            return
        enemy_units = [
            x for x in uw_world.entities().values() if x.enemy() and x.Unit is not None
        ]
        if not enemy_units:
            return
        for own in own_units:
            if len(uw_commands.orders(own.id)) == 0:
                enemy = min(
                    enemy_units,
                    key=lambda x: uw_map.distance_estimate(own.pos(), x.pos()),
                )
                uw_commands.order(own.id, uw_commands.fight_to_entity(enemy.id))

    def assign_random_recipes(self):
        for own in uw_world.entities().values():
            if not own.own() or own.Unit is None or own.Recipe is not None:
                continue
            recipes = own.proto().data.get("recipes", [])
            if recipes:
                recipe = random.choice(recipes)
                uw_commands.set_recipe(own.id, recipe)

    def configure(self):
        if self.is_configured:
            return
        self.is_configured = True

        uw_game.set_player_name("bot-py")
        uw_game.player_join_force(0)  # create new force
        uw_game.set_force_color(1, 0, 0)
        # Set race to technocracy
        technocracy_id = uw_prototypes.hashString("technocracy")
        if technocracy_id != 0:
            uw_game.set_force_race(technocracy_id)

    def on_update(self, stepping: bool):
        if uw_game.game_state() == GameState.Session:
            self.configure()
            return

        if not stepping:
            return

        self.work_step += 1
        match self.work_step % 10:  # save some cpu cycles by splitting work over multiple steps
            case 1:
                self.attack_nearest_enemies()
            case 5:
                self.assign_random_recipes()

    def run(self):
        uw_game.log_info("bot-py start")
        if not uw_game.try_reconnect():
            uw_game.set_connect_start_gui(True)
            if not uw_game.connect_environment():
                uw_game.connect_new_server()
        uw_game.log_info("bot-py done")

import random
from uwapi import *


class JuggernautBot:
    """Bot that focuses on building Juggernauts"""
    
    is_configured: bool = False
    work_step: int = 0
    
    # Resource IDs from recipes.md
    RESOURCE_OIL = 3626035542
    RESOURCE_METAL = 3637378061
    RESOURCE_FUEL_RODS = 2338948473
    
    # Deposit IDs (placeOver values)
    DEPOSIT_METAL = 2702889254
    DEPOSIT_OIL = 3984569945
    
    # Construction prototype IDs - these are what we place
    # These need to be the construction IDs that BUILD the units we want
    # For now, try using the unit IDs directly as some games allow this
    CONSTRUCTION_DRILL = 2910644843  # drill unit ID - might work as construction
    CONSTRUCTION_REFINERY = 2183816954  # refinery unit ID 
    CONSTRUCTION_BOTS_FACTORY = 3126591205  # bots factory unit ID
    
    # Recipe IDs from recipes.md
    RECIPE_METAL = 3161943147  # metal extraction
    RECIPE_OIL = 2337074000  # oil extraction
    RECIPE_FUEL_RODS = 3517532115  # fuel rods from oil
    RECIPE_JUGGERNAUT = 3277593549  # juggernaut unit
    
    # Track what we've built
    built_metal_drill = False
    built_oil_drill = False
    built_refinery = False
    built_bots_factory = False
    
    # Track found deposits
    metal_deposit_pos = None
    oil_deposit_pos = None
    
    # Track build attempts to avoid spamming
    last_build_attempt = 0
    
    # Track if we've done admin setup
    admin_setup_done = False
    
    def __init__(self):
        uw_events.on_update(self.on_update)
    
    def configure(self):
        if self.is_configured:
            return
        self.is_configured = True
        
        uw_game.log_info("Configuring Juggernaut Bot")
        
        # Log current map state
        uw_game.log_info(f"Map state during config: {uw_game.map_state()}")
        
        # Check if we're admin before trying admin commands
        # Note: We may not be admin until after we join, so we'll try admin commands later
            
        uw_game.set_player_name("juggernaut-bot")
        uw_game.player_join_force(0)  # create new force
        uw_game.set_force_color(0, 0, 1)  # blue
        
        # Set race to technocracy - ID from recipes.md
        TECHNOCRACY_ID = 3867317061
        
        uw_game.log_info(f"Setting race to technocracy (ID: {TECHNOCRACY_ID})")
        uw_game.set_force_race(TECHNOCRACY_ID)
    
    def log_available_races(self):
        """Log all available race prototypes for debugging"""
        uw_game.log_info("Listing all available races:")
        for proto_id, prototype in uw_prototypes._all.items():
            if prototype.type == PrototypeType.Race:
                uw_game.log_info(f"  Race: {prototype.name} (ID: {proto_id})")
        
        # Also log construction prototypes that build what we need
        uw_game.log_info("Finding construction prototypes for technocracy buildings:")
        for proto_id, prototype in uw_prototypes._all.items():
            if prototype.type == PrototypeType.Construction:
                # Check if this construction builds drill, refinery, or bots factory
                if prototype.data and "result" in prototype.data:
                    result_id = prototype.data["result"]
                    if result_id == 2910644843:  # Drill unit
                        uw_game.log_info(f"  Construction for DRILL: {prototype.name} (ID: {proto_id})")
                        self.CONSTRUCTION_DRILL = proto_id
                    elif result_id == 2183816954:  # Refinery unit
                        uw_game.log_info(f"  Construction for REFINERY: {prototype.name} (ID: {proto_id})")
                        self.CONSTRUCTION_REFINERY = proto_id
                    elif result_id == 3126591205:  # Bots factory unit
                        uw_game.log_info(f"  Construction for BOTS FACTORY: {prototype.name} (ID: {proto_id})")
                        self.CONSTRUCTION_BOTS_FACTORY = proto_id
    
    def find_resource_deposits(self):
        """Find resource deposit entities by checking entity type"""
        if self.metal_deposit_pos and self.oil_deposit_pos:
            uw_game.log_info(f"Already found deposits - metal: {self.metal_deposit_pos}, oil: {self.oil_deposit_pos}")
            return
        
        uw_game.log_info(f"Searching for resource deposits among {len(uw_world.entities())} entities")
        
        # Find control core position first
        control_core_pos = None
        for entity in uw_world.entities().values():
            if entity.own() and entity.Proto and entity.Proto.proto == 3805195479:  # CONTROL_CORE_ID
                control_core_pos = entity.pos()
                break
        
        if control_core_pos is None:
            uw_game.log_warning("Could not find control core for deposit search!")
            return
        
        resource_count = 0
        closest_metal_distance = float('inf')
        closest_oil_distance = float('inf')
        
        for entity in uw_world.entities().values():
            # Check if this is a resource entity
            if entity.type() != PrototypeType.Resource:
                continue
            
            resource_count += 1
            
            # Skip if no position
            if entity.Position is None:
                continue
            
            # Check if this is a resource deposit by looking at proto ID
            if entity.Proto is None:
                continue
            
            proto = entity.proto()
            if not proto:
                continue
                
            proto_id = entity.Proto.proto
            proto_name = proto.name
            
            # Log resource entities
            uw_game.log_info(f"  Resource entity: {proto_name} (ID: {proto_id}), Pos: {entity.pos()}")
            
            # Check if this is specifically a metal or oil deposit by ID
            distance = uw_map.distance_estimate(control_core_pos, entity.pos())
            
            if proto_id == self.DEPOSIT_METAL:  # Metal deposit ID from recipes.md
                if distance < closest_metal_distance:
                    closest_metal_distance = distance
                    self.metal_deposit_pos = entity.pos()
                    uw_game.log_info(f"*** FOUND METAL DEPOSIT at position {self.metal_deposit_pos}, distance {distance}")
            
            elif proto_id == self.DEPOSIT_OIL:  # Oil deposit ID from recipes.md
                if distance < closest_oil_distance:
                    closest_oil_distance = distance
                    self.oil_deposit_pos = entity.pos()
                    uw_game.log_info(f"*** FOUND OIL DEPOSIT at position {self.oil_deposit_pos}, distance {distance}")
        
        uw_game.log_info(f"Search complete. Found {resource_count} resource entities")
        if self.metal_deposit_pos:
            uw_game.log_info(f"  Closest metal deposit at {self.metal_deposit_pos}")
        if self.oil_deposit_pos:
            uw_game.log_info(f"  Closest oil deposit at {self.oil_deposit_pos}")
    
    def build_infrastructure(self):
        """Build the required infrastructure for Juggernaut production"""
        
        # Don't spam build attempts - wait at least 10 ticks between attempts
        current_tick = uw_game.game_tick()
        if current_tick - self.last_build_attempt < 10:
            uw_game.log_info(f"Waiting before next build attempt (tick {current_tick}, last attempt {self.last_build_attempt})")
            return
        
        uw_game.log_info(f"=== BUILD INFRASTRUCTURE CHECK (tick {current_tick}) ===")
        uw_game.log_info(f"  Built status - Metal drill: {self.built_metal_drill}, Oil drill: {self.built_oil_drill}, Refinery: {self.built_refinery}, Factory: {self.built_bots_factory}")
        
        # Find control core by its prototype ID
        control_core_pos = None
        CONTROL_CORE_ID = 3805195479  # From technocracy starting provisions
        for entity in uw_world.entities().values():
            if entity.own() and entity.Proto and entity.Proto.proto == CONTROL_CORE_ID:
                control_core_pos = entity.pos()
                uw_game.log_info(f"Found control core at position {control_core_pos}")
                break
        
        if control_core_pos is None:
            uw_game.log_warning("Could not find control core!")
            return
        
        # Place drills on deposits if we found them
        if not self.built_metal_drill:
            if self.metal_deposit_pos:
                # Place drill ON the metal deposit
                uw_game.log_info(f">>> PLACING METAL DRILL on deposit at position {self.metal_deposit_pos}")
                uw_game.log_info(f"    Using drill construction ID: {self.CONSTRUCTION_DRILL}")
                uw_commands.place_construction(
                    self.CONSTRUCTION_DRILL,
                    self.metal_deposit_pos,  # ON the deposit
                    0,  # yaw
                    self.RECIPE_METAL,  # metal extraction recipe
                    Priority.Normal
                )
                self.built_metal_drill = True
                self.last_build_attempt = current_tick
                uw_game.log_info("    Metal drill placement command sent")
                return
            else:
                # No metal deposit found yet - skip for now
                uw_game.log_info("    No metal deposit found yet, skipping metal drill")
        
        if not self.built_oil_drill:
            if self.oil_deposit_pos:
                # Place drill ON the oil deposit
                uw_game.log_info(f">>> PLACING OIL DRILL on deposit at position {self.oil_deposit_pos}")
                uw_game.log_info(f"    Using drill construction ID: {self.CONSTRUCTION_DRILL}")
                uw_commands.place_construction(
                    self.CONSTRUCTION_DRILL,
                    self.oil_deposit_pos,  # ON the deposit
                    0,
                    self.RECIPE_OIL,  # oil extraction recipe
                    Priority.Normal
                )
                self.built_oil_drill = True
                self.last_build_attempt = current_tick
                uw_game.log_info("    Oil drill placement command sent")
                return
            else:
                # No oil deposit found yet - skip for now
                uw_game.log_info("    No oil deposit found yet, skipping oil drill")
            
        if not self.built_refinery:
            nearby_tiles = uw_map.area_neighborhood(control_core_pos, 20.0)
            if nearby_tiles:
                refinery_pos = nearby_tiles[len(nearby_tiles)//2]
                uw_game.log_info(f">>> PLACING REFINERY near control core at position {refinery_pos}")
                uw_game.log_info(f"    Using refinery construction ID: {self.CONSTRUCTION_REFINERY}")
                uw_commands.place_construction(
                    self.CONSTRUCTION_REFINERY,
                    refinery_pos,
                    0,
                    0,  # no initial recipe
                    Priority.Normal
                )
                self.built_refinery = True
                self.last_build_attempt = current_tick
                uw_game.log_info("    Refinery placement command sent")
                return
        
        if not self.built_bots_factory:
            nearby_tiles = uw_map.area_neighborhood(control_core_pos, 25.0)
            if nearby_tiles:
                factory_pos = nearby_tiles[len(nearby_tiles)*2//3]
                uw_game.log_info(f">>> PLACING BOTS FACTORY near control core at position {factory_pos}")
                uw_game.log_info(f"    Using factory construction ID: {self.CONSTRUCTION_BOTS_FACTORY}")
                uw_commands.place_construction(
                    self.CONSTRUCTION_BOTS_FACTORY,
                    factory_pos,
                    0,
                    0,
                    Priority.Normal
                )
                self.built_bots_factory = True
                self.last_build_attempt = current_tick
                uw_game.log_info("    Bots factory placement command sent")
        
        uw_game.log_info("=== END BUILD INFRASTRUCTURE CHECK ===")
    
    def manage_production(self):
        """Set recipes and manage production queues"""
        
        uw_game.log_info("=== MANAGE PRODUCTION CHECK ===")
        own_building_count = 0
        
        for entity in uw_world.entities().values():
            if not entity.own() or entity.Unit is None:
                continue
            
            own_building_count += 1
            
            # Check if this is one of our buildings
            if entity.Proto is None:
                continue
                
            proto_id = entity.Proto.proto
            proto_name = entity.proto().name
            
            # Log owned buildings
            uw_game.log_info(f"  Owned building: {proto_name} (entity {entity.id}, proto {proto_id})")
            if entity.Recipe is not None:
                uw_game.log_info(f"    Current recipe: {entity.Recipe.recipe}")
            
            # Set refinery to produce fuel rods
            if proto_id == self.CONSTRUCTION_REFINERY and entity.Recipe is None:
                uw_game.log_info(f">>> SETTING REFINERY {entity.id} to produce fuel rods (recipe {self.RECIPE_FUEL_RODS})")
                uw_commands.set_recipe(entity.id, self.RECIPE_FUEL_RODS)
            
            # Set bots factory to produce juggernauts
            elif proto_id == self.CONSTRUCTION_BOTS_FACTORY and entity.Recipe is None:
                uw_game.log_info(f">>> SETTING BOTS FACTORY {entity.id} to produce juggernauts (recipe {self.RECIPE_JUGGERNAUT})")
                uw_commands.set_recipe(entity.id, self.RECIPE_JUGGERNAUT)
        
        uw_game.log_info(f"Total owned buildings: {own_building_count}")
        uw_game.log_info("=== END MANAGE PRODUCTION CHECK ===")
    
    def control_juggernauts(self):
        """Control existing juggernaut units"""
        
        juggernauts = []
        enemies = []
        
        for entity in uw_world.entities().values():
            if entity.Unit is None:
                continue
                
            # Check if it's our juggernaut (would need to check proto name)
            if entity.own() and entity.Proto and "juggernaut" in entity.proto().name.lower():
                juggernauts.append(entity)
            elif entity.enemy():
                enemies.append(entity)
        
        # Attack nearest enemies with juggernauts
        for juggernaut in juggernauts:
            if len(uw_commands.orders(juggernaut.id)) == 0 and enemies:
                nearest_enemy = min(
                    enemies,
                    key=lambda e: uw_map.distance_estimate(juggernaut.pos(), e.pos())
                )
                uw_commands.order(juggernaut.id, uw_commands.fight_to_entity(nearest_enemy.id))
                uw_game.log_info(f"Juggernaut {juggernaut.id} attacking enemy {nearest_enemy.id}")
    
    def on_update(self, stepping: bool):
        # Configure during session state
        if uw_game.game_state() == GameState.Session:
            self.configure()
            
            # Try admin setup after configuration if we're admin
            if not self.admin_setup_done and uw_world.is_admin():
                uw_game.log_info("We are admin - setting up lobby")
                
                # Set map
                uw_game.log_info("Setting map to 'planets/h2o.uwmap'")
                uw_admin.set_map_selection("planets/h2o.uwmap")
                
                self.admin_setup_done = True
            return
        
        if not stepping:
            return
        
        # Split work across multiple steps to save CPU
        self.work_step += 1
        
        # Log races once when prototypes are loaded
        if self.work_step == 1 and len(uw_prototypes._all) > 0:
            uw_game.log_info(f"First update - {len(uw_prototypes._all)} prototypes loaded")
            self.log_available_races()
            
            # Log map info
            if uw_game.map_state() == MapState.Loaded:
                uw_game.log_info(f"Playing on map: name='{uw_map._name}', path='{uw_map._path}'")
            else:
                uw_game.log_info(f"Map not loaded yet, state: {uw_game.map_state()}")
        
        # Log periodic status
        if self.work_step % 100 == 0:
            uw_game.log_info(f"=== STATUS UPDATE (step {self.work_step}, tick {uw_game.game_tick()}) ===")
            uw_game.log_info(f"  Game state: {uw_game.game_state()}")
            uw_game.log_info(f"  Map state: {uw_game.map_state()}")
            uw_game.log_info(f"  Total entities: {len(uw_world.entities())}")
        
        match self.work_step % 30:
            case 1:
                # Find resource deposits first
                self.find_resource_deposits()
            case 5:
                # Build infrastructure every 30 steps
                self.build_infrastructure()
            case 10:
                # Manage production
                self.manage_production()
            case 20:
                # Control units
                self.control_juggernauts()
    
    def run(self):
        uw_game.log_info("Juggernaut bot start")
        
        # Try to reconnect to existing game
        if not uw_game.try_reconnect():
            uw_game.log_info("No existing game to reconnect to, starting new server")
            
            # Start GUI and create new server
            uw_game.set_connect_start_gui(True)
            
            # Check environment for connection params
            if not uw_game.connect_environment():
                uw_game.log_info("Starting new local server")
                # Start a new local server
                # visibility: 0 = localhost, 1 = friends, 2 = public
                # name: server name
                # extra_params: additional server parameters
                uw_game.connect_new_server(0, "Juggernaut Bot Server", "")
        
        uw_game.log_info("Juggernaut bot done")
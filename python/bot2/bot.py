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
    
    # Construction prototype IDs - these will be found dynamically
    CONSTRUCTION_DRILL = None
    CONSTRUCTION_REFINERY = None
    CONSTRUCTION_BOTS_FACTORY = None
    CONSTRUCTION_LABORATORY = None
    CONSTRUCTION_FABRICATOR = None
    CONSTRUCTION_VEHICLE_FACTORY = None
    
    # Recipe IDs from recipes.md
    RECIPE_METAL = 3161943147  # metal extraction
    RECIPE_OIL = 2337074000  # oil extraction
    RECIPE_FUEL_RODS = 3517532115  # fuel rods from oil
    RECIPE_JUGGERNAUT = 3277593549  # juggernaut unit (12 metal + 1 fuel, 1440 ticks)
    RECIPE_TRIPOD = 3084381729  # tripod unit (4 metal + 1 fuel, 480 ticks)
    RECIPE_TRIPOD_RANGE = 4002099296  # tripod range upgrade (5 aether, 600 ticks)
    RECIPE_JUGGERNAUT_RANGE = 2920254240  # juggernaut range upgrade (5 aether, 600 ticks)
    RECIPE_ATV = 2861495354  # ATV recipe (2 metal -> 1 ATV, 240 ticks)
    
    # Track what we've built
    built_refinery = False
    built_bots_factory = False
    built_bots_factory_count = 0  # Track total number of factories
    built_laboratory = False
    built_fabricator_count = 0  # Track number of fabricators (max 2)
    built_vehicle_factory = False  # Track vehicle factory for ATV production
    
    # Track found deposits
    ore_deposit_positions = []  # We'll find 2 closest ore deposits
    oil_deposit_pos = None
    aether_deposit_pos = None
    
    # Track what we've built on each deposit
    built_ore_drills = 0
    built_oil_drill = False
    built_aether_drill = False
    
    # Track build attempts to avoid spamming
    last_build_attempt = 0
    
    # Track if we've done admin setup
    admin_setup_done = False
    
    # Track if we have combat units (to trigger additional factories)
    has_combat_units = False
    
    # Track individual juggernaut movement states
    juggernaut_states = {}  # {entity_id: {'angle': float, 'last_pos': int, 'patrol_index': int}}
    
    # Track enemy units for threat assessment
    enemy_unit_counts = {}  # {proto_name: count}
    last_enemy_log = 0  # To avoid spam
    
    def __init__(self):
        uw_events.on_update(self.on_update)
    
    def configure(self):
        import time
        
        # Auto start the game if available and we're admin
        if (
            self.is_configured
            and uw_game.game_state() == GameState.Session
            and uw_world.is_admin()
        ):
            time.sleep(3)  # Give observer time to connect
            uw_admin.start_game()
            return
            
        # Is configuring possible?
        if (
            self.is_configured
            or uw_game.game_state() != GameState.Session
            or uw_world.my_player_id() == 0
        ):
            return
            
        self.is_configured = True
        
        uw_game.log_info("Configuring Juggernaut Bot")
        uw_game.log_info(f"Map state during config: {uw_game.map_state()}")
        
        uw_game.set_player_name("juggernaut-bot")
        uw_game.player_join_force(0)  # create new force
        uw_game.set_force_color(0, 0, 1)  # blue
        
        # Set race to technocracy - ID from recipes.md
        TECHNOCRACY_ID = 3867317061
        uw_game.log_info(f"Setting race to technocracy (ID: {TECHNOCRACY_ID})")
        uw_game.set_force_race(TECHNOCRACY_ID)
        
        # Admin setup: set map and add AI opponent
        if uw_world.is_admin():
            uw_game.log_info("Setting up game as admin...")
            # Set map to a balanced one for testing
            uw_admin.set_map_selection("planets/tetrahedron.uwmap")  # Good balanced map
            # Add AI opponent for testing our improvements
            uw_admin.add_ai()
            uw_admin.set_automatic_suggested_camera_focus(True)
            uw_game.log_info("Admin setup complete: map set, AI added")
        
        uw_game.log_info("Configuration done")
    
    def log_available_races(self):
        """Log all available race prototypes for debugging"""
        uw_game.log_info("Listing all available races:")
        for proto_id, prototype in uw_prototypes._all.items():
            if prototype.type == PrototypeType.Race:
                uw_game.log_info(f"  Race: {prototype.name} (ID: {proto_id})")
        
        # Find construction prototypes
        uw_game.log_info("Finding construction prototypes:")
        construction_count = 0
        for proto_id, prototype in uw_prototypes._all.items():
            if prototype.type == PrototypeType.Construction:
                construction_count += 1
                # Log first few constructions to understand structure
                if construction_count <= 20:
                    uw_game.log_info(f"  Construction: {prototype.name} (ID: {proto_id})")
                    if prototype.data:
                        uw_game.log_info(f"    Data keys: {list(prototype.data.keys())}")
                        
                # Try to match by name
                name_lower = prototype.name.lower()
                if "drill" in name_lower:
                    uw_game.log_info(f"  >>> Found DRILL construction: {prototype.name} (ID: {proto_id})")
                    self.CONSTRUCTION_DRILL = proto_id
                elif "refinery" in name_lower:
                    uw_game.log_info(f"  >>> Found REFINERY construction: {prototype.name} (ID: {proto_id})")
                    self.CONSTRUCTION_REFINERY = proto_id
                elif "bots factory" in name_lower or "bots_factory" in name_lower:
                    uw_game.log_info(f"  >>> Found BOTS FACTORY construction: {prototype.name} (ID: {proto_id})")
                    self.CONSTRUCTION_BOTS_FACTORY = proto_id
                elif "laboratory" in name_lower:
                    uw_game.log_info(f"  >>> Found LABORATORY construction: {prototype.name} (ID: {proto_id})")
                    self.CONSTRUCTION_LABORATORY = proto_id
                elif "fabricator" in name_lower:
                    uw_game.log_info(f"  >>> Found FABRICATOR construction: {prototype.name} (ID: {proto_id})")
                    self.CONSTRUCTION_FABRICATOR = proto_id
                elif "vehicle factory" in name_lower:
                    uw_game.log_info(f"  >>> Found VEHICLE FACTORY construction: {prototype.name} (ID: {proto_id})")
                    self.CONSTRUCTION_VEHICLE_FACTORY = proto_id
        
        uw_game.log_info(f"Total constructions found: {construction_count}")
        
        # If we didn't find them by name, use hardcoded IDs from technocracy's construction list
        # These are from the technocracy constructions array in recipes.md
        if not self.CONSTRUCTION_DRILL:
            self.CONSTRUCTION_DRILL = 2410646287  # Try second construction ID
            uw_game.log_info(f"Using technocracy construction ID for drill: {self.CONSTRUCTION_DRILL}")
        if not self.CONSTRUCTION_REFINERY:
            self.CONSTRUCTION_REFINERY = 3226437573  # From technocracy constructions list
            uw_game.log_info(f"Using technocracy construction ID for refinery: {self.CONSTRUCTION_REFINERY}")
        if not self.CONSTRUCTION_BOTS_FACTORY:
            self.CONSTRUCTION_BOTS_FACTORY = 3458449634  # From technocracy constructions list  
            uw_game.log_info(f"Using technocracy construction ID for bots factory: {self.CONSTRUCTION_BOTS_FACTORY}")
        if not self.CONSTRUCTION_LABORATORY:
            self.CONSTRUCTION_LABORATORY = 2840078502  # From game log detection
            uw_game.log_info(f"Using technocracy construction ID for laboratory: {self.CONSTRUCTION_LABORATORY}")
        if not self.CONSTRUCTION_FABRICATOR:
            self.CONSTRUCTION_FABRICATOR = 3458449634  # Need to find actual fabricator construction ID
            uw_game.log_info(f"Using placeholder construction ID for fabricator: {self.CONSTRUCTION_FABRICATOR}")
    
    def find_resource_deposits(self):
        """Find resource deposit entities - deposits are Units not Resources"""
        # Check if we already found all deposits
        if len(self.ore_deposit_positions) >= 2 and self.oil_deposit_pos and self.aether_deposit_pos:
            uw_game.log_info("Already found all deposits")
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
        
        # Track all found deposits
        ore_deposits = []  # We want 2 closest
        oil_deposits = []  # We want 1 closest
        aether_deposits = []  # We want 1 closest
        deposit_count = 0
        
        for entity in uw_world.entities().values():
            # Deposits are Units that are not owned by anyone
            if entity.own() or entity.enemy():
                continue
                
            if entity.type() != PrototypeType.Unit:
                continue
            
            # Skip if no position
            if entity.Position is None:
                continue
            
            # Check if this is a resource deposit by looking at proto
            if entity.Proto is None:
                continue
            
            proto = entity.proto()
            if not proto:
                continue
                
            proto_id = entity.Proto.proto
            proto_name = proto.name.lower()
            
            # Check if this is a deposit by name
            if "deposit" in proto_name or "ore" in proto_name or "oil" in proto_name or "aether" in proto_name:
                distance = uw_map.distance_estimate(control_core_pos, entity.pos())
                deposit_info = (distance, entity.pos(), proto.name, proto_id)
                
                uw_game.log_info(f"  Found deposit: {proto.name} (ID: {proto_id}), Pos: {entity.pos()}, Distance: {distance}")
                deposit_count += 1
                
                # Categorize by type
                if "ore" in proto_name or "metal" in proto_name:
                    ore_deposits.append(deposit_info)
                elif "oil" in proto_name:
                    oil_deposits.append(deposit_info)
                elif "aether" in proto_name:
                    aether_deposits.append(deposit_info)
        
        # Sort deposits by distance and keep closest ones
        ore_deposits.sort(key=lambda x: x[0])
        oil_deposits.sort(key=lambda x: x[0])
        aether_deposits.sort(key=lambda x: x[0])
        
        # Store the closest deposits we need
        self.ore_deposit_positions = []
        
        # Get 2 closest ore deposits
        for i in range(min(2, len(ore_deposits))):
            self.ore_deposit_positions.append(ore_deposits[i][1])
            uw_game.log_info(f"*** Selected ORE DEPOSIT #{i+1} at position {ore_deposits[i][1]}, distance {ore_deposits[i][0]}")
        
        # Get 1 closest oil deposit
        if oil_deposits:
            self.oil_deposit_pos = oil_deposits[0][1]
            uw_game.log_info(f"*** Selected OIL DEPOSIT at position {oil_deposits[0][1]}, distance {oil_deposits[0][0]}")
        
        # Get 1 closest aether deposit
        if aether_deposits:
            self.aether_deposit_pos = aether_deposits[0][1]
            uw_game.log_info(f"*** Selected AETHER DEPOSIT at position {aether_deposits[0][1]}, distance {aether_deposits[0][0]}")
        
        uw_game.log_info(f"Search complete. Found {deposit_count} total deposits")
        uw_game.log_info(f"  Selected: {len(self.ore_deposit_positions)} ore, {'1 oil' if self.oil_deposit_pos else '0 oil'}, {'1 aether' if self.aether_deposit_pos else '0 aether'}")
        
        # Calculate base defense perimeter based on deposit distances
        max_deposit_distance = 0
        if self.ore_deposit_positions and len(ore_deposits) > 0:
            max_deposit_distance = max(max_deposit_distance, ore_deposits[0][0])
            if len(ore_deposits) > 1:
                max_deposit_distance = max(max_deposit_distance, ore_deposits[1][0])
        if oil_deposits:
            max_deposit_distance = max(max_deposit_distance, oil_deposits[0][0])
        if aether_deposits:
            max_deposit_distance = max(max_deposit_distance, aether_deposits[0][0])
        
        uw_game.log_info(f"*** BASE DEFENSE PERIMETER: {max_deposit_distance:.0f} units from core (furthest deposit)")
        uw_game.log_info(f"    Juggernaut patrol range: up to 300 units (covers base perimeter)")
        uw_game.log_info(f"    Enemies within {max_deposit_distance:.0f} units = INSIDE OUR BASE")
    
    def build_infrastructure(self):
        """Build the required infrastructure for Juggernaut production"""
        
        # Don't spam build attempts - wait at least 10 ticks between attempts
        current_tick = uw_game.game_tick()
        if current_tick - self.last_build_attempt < 10:
            uw_game.log_info(f"Waiting before next build attempt (tick {current_tick}, last attempt {self.last_build_attempt})")
            return
        
        uw_game.log_info(f"=== BUILD INFRASTRUCTURE CHECK (tick {current_tick}) ===")
        uw_game.log_info(f"  Built status - Ore drills: {self.built_ore_drills}/2, Oil drill: {self.built_oil_drill}, Aether drill: {self.built_aether_drill}")
        uw_game.log_info(f"  Refinery: {self.built_refinery}, Factories: {self.built_bots_factory_count}/4, Has Combat Units: {self.has_combat_units}")
        uw_game.log_info(f"  Laboratory: {self.built_laboratory}, Fabricators: {self.built_fabricator_count}/2, Vehicle Factory: {self.built_vehicle_factory}")
        
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
        
        # OPTIMIZED BUILD ORDER: Metal → Oil → Metal (gets fuel faster)
        
        # Place FIRST ore drill
        if self.built_ore_drills == 0 and len(self.ore_deposit_positions) > 0:
            deposit_pos = self.ore_deposit_positions[0]
            uw_game.log_info(f">>> PLACING ORE DRILL #1 on deposit at position {deposit_pos}")
            uw_game.log_info(f"    Using drill construction ID: {self.CONSTRUCTION_DRILL}")
            uw_commands.place_construction(
                self.CONSTRUCTION_DRILL,
                deposit_pos,  # ON the deposit
                0,  # yaw
                self.RECIPE_METAL,  # metal extraction recipe
                Priority.Normal
            )
            self.built_ore_drills = 1
            self.last_build_attempt = current_tick
            uw_game.log_info(f"    Ore drill #1 placement command sent")
            return
        
        # Place oil drill SECOND (before 2nd metal drill) for faster fuel production
        if not self.built_oil_drill and self.oil_deposit_pos and self.built_ore_drills >= 1:
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
        
        # Place SECOND ore drill (after oil for optimal timing)
        if self.built_ore_drills == 1 and len(self.ore_deposit_positions) > 1 and self.built_oil_drill:
            deposit_pos = self.ore_deposit_positions[1]
            uw_game.log_info(f">>> PLACING ORE DRILL #2 on deposit at position {deposit_pos}")
            uw_game.log_info(f"    Using drill construction ID: {self.CONSTRUCTION_DRILL}")
            uw_commands.place_construction(
                self.CONSTRUCTION_DRILL,
                deposit_pos,  # ON the deposit
                0,  # yaw
                self.RECIPE_METAL,  # metal extraction recipe
                Priority.Normal
            )
            self.built_ore_drills = 2
            self.last_build_attempt = current_tick
            uw_game.log_info(f"    Ore drill #2 placement command sent")
            return
        
        # Build aether drill only after we have 4 factories (we don't need aether for Juggernauts)
        if not self.built_aether_drill and self.aether_deposit_pos and self.built_bots_factory_count >= 4:
            uw_game.log_info(f">>> PLACING AETHER DRILL on deposit at position {self.aether_deposit_pos}")
            uw_game.log_info(f"    Using drill construction ID: {self.CONSTRUCTION_DRILL}")
            # Find aether recipe ID
            RECIPE_AETHER = 2718646897  # From recipes.md
            uw_commands.place_construction(
                self.CONSTRUCTION_DRILL,
                self.aether_deposit_pos,  # ON the deposit
                0,
                RECIPE_AETHER,  # aether extraction recipe
                Priority.Normal
            )
            self.built_aether_drill = True
            self.last_build_attempt = current_tick
            uw_game.log_info("    Aether drill placement command sent")
            return
            
        # Only build refinery and factory after we have drills
        if self.built_ore_drills >= 1 and self.built_oil_drill:
            if not self.built_refinery:
                # Use find_construction_placement to find a valid spot near control core
                refinery_pos = uw_world.find_construction_placement(
                    self.CONSTRUCTION_REFINERY,
                    control_core_pos,
                    self.RECIPE_FUEL_RODS
                )
                if refinery_pos != -1:  # -1 means no valid position found
                    uw_game.log_info(f">>> PLACING REFINERY at position {refinery_pos} (near control core at {control_core_pos})")
                    uw_game.log_info(f"    Distance from core: {uw_map.distance_estimate(control_core_pos, refinery_pos)}")
                    uw_game.log_info(f"    Using refinery construction ID: {self.CONSTRUCTION_REFINERY}")
                    uw_commands.place_construction(
                        self.CONSTRUCTION_REFINERY,
                        refinery_pos,
                        0,
                        self.RECIPE_FUEL_RODS,  # Set to produce fuel rods
                        Priority.Normal
                    )
                    self.built_refinery = True
                    self.last_build_attempt = current_tick
                    uw_game.log_info("    Refinery placement command sent")
                    return
                else:
                    uw_game.log_warning("Could not find valid position for refinery!")
            
            # Build first factory regardless, then additional ones only after first factory is built
            # This is more aggressive than waiting for first combat unit to be produced
            first_factory_built = False
            if self.built_bots_factory_count >= 1:
                # Check if we have at least 1 actual factory entity (built, not just placed)
                for entity in uw_world.entities().values():
                    if entity.own() and entity.Proto and entity.Proto.proto == 3126591205:  # Bots factory
                        first_factory_built = True
                        break
            
            target_factories = 4 if first_factory_built else 1
            
            # Check resources and logistics before building additional factories
            # Each factory needs metal to build, and we need to maintain production
            # Only build new factories if we have excess resources AND available ATVs
            can_build_factory = True
            if self.built_bots_factory_count >= 1:
                # Check if we have enough metal (need at least 25 metal and 1 fuel rod)
                metal_count = 0
                fuel_count = 0
                for entity in uw_world.entities().values():
                    if entity.own() and entity.Amount is not None and entity.Proto:
                        if entity.Proto.proto == 3637378061:  # Metal
                            metal_count += entity.Amount.amount
                        elif entity.Proto.proto == 2338948473:  # Fuel rods
                            fuel_count += entity.Amount.amount
                
                # Check ATV availability - don't overwhelm our logistics
                force_stats = uw_world.my_force_statistics()
                idle_atv_percentage = 0.0
                atv_total = 0
                atv_idle = 0
                if force_stats and force_stats.logisticsUnitsTotal > 0:
                    atv_total = force_stats.logisticsUnitsTotal
                    atv_idle = force_stats.logisticsUnitsIdle
                    idle_atv_percentage = 100.0 * atv_idle / atv_total
                
                # Log ATV statistics for monitoring
                uw_game.log_info(f"  ATV Status: {atv_idle}/{atv_total} idle ({idle_atv_percentage:.1f}%)")
                
                # REQUIREMENTS: Need metal, fuel, and available logistics
                resource_ok = metal_count >= 25 and fuel_count >= 1
                logistics_ok = idle_atv_percentage >= 30.0  # At least 30% ATVs should be idle
                
                if not resource_ok:
                    can_build_factory = False
                    uw_game.log_info(f"  Deferring factory construction (Metal: {metal_count}, Fuel: {fuel_count}, need 25+ metal)")
                elif not logistics_ok:
                    can_build_factory = False
                    uw_game.log_info(f"  Deferring factory construction (ATV idle: {idle_atv_percentage:.1f}%, need 30%+ idle ATVs)")
                else:
                    uw_game.log_info(f"  Factory construction OK (Metal: {metal_count}, Fuel: {fuel_count}, ATV idle: {idle_atv_percentage:.1f}%)")
            
            # Only build ONE factory at a time to avoid resource starvation
            if self.built_bots_factory_count < target_factories and can_build_factory:
                # Use find_construction_placement to find a valid spot near control core
                factory_pos = uw_world.find_construction_placement(
                    self.CONSTRUCTION_BOTS_FACTORY,
                    control_core_pos,
                    self.RECIPE_JUGGERNAUT
                )
                if factory_pos != -1:  # -1 means no valid position found
                    uw_game.log_info(f">>> PLACING BOTS FACTORY #{self.built_bots_factory_count + 1} at position {factory_pos} (near control core at {control_core_pos})")
                    uw_game.log_info(f"    Distance from core: {uw_map.distance_estimate(control_core_pos, factory_pos)}")
                    uw_game.log_info(f"    Using factory construction ID: {self.CONSTRUCTION_BOTS_FACTORY}")
                    factory_trigger = "first_factory_built" if first_factory_built else "startup_mode"
                    uw_game.log_info(f"    Target: {target_factories} factories total (trigger: {factory_trigger})")
                    uw_commands.place_construction(
                        self.CONSTRUCTION_BOTS_FACTORY,
                        factory_pos,
                        0,
                        self.RECIPE_JUGGERNAUT,  # Set to produce Juggernauts
                        Priority.Normal
                    )
                    if not self.built_bots_factory:
                        self.built_bots_factory = True
                    # Increment count immediately to prevent placing multiple factories
                    self.built_bots_factory_count += 1
                    self.last_build_attempt = current_tick
                    uw_game.log_info(f"    Bots factory placement command sent (now tracking {self.built_bots_factory_count} factories)")
                    return  # Important: return after placing to avoid placing multiple in one tick
                else:
                    uw_game.log_warning("Could not find valid position for bots factory!")
        
        # Build Aether drill right before laboratory (need aether for upgrades)
        if (self.built_bots_factory_count >= 2 and 
            not self.built_aether_drill and 
            self.aether_deposit_pos is not None):
            
            # Check if we have enough resources (aether drill needs metal)
            metal_count = 0
            for entity in uw_world.entities().values():
                if entity.own() and entity.Amount is not None and entity.Proto:
                    if entity.Proto.proto == 3637378061:  # Metal
                        metal_count += entity.Amount.amount
            
            if metal_count >= 20:  # Aether drill needs metal to build
                uw_game.log_info(f">>> PLACING AETHER DRILL on deposit at position {self.aether_deposit_pos}")
                uw_game.log_info(f"    Using drill construction ID: {self.CONSTRUCTION_DRILL}")
                uw_game.log_info(f"    Distance from core: {uw_map.distance_estimate(control_core_pos, self.aether_deposit_pos)}")
                RECIPE_AETHER = 2718646897  # From recipes.md
                uw_commands.place_construction(
                    self.CONSTRUCTION_DRILL,
                    self.aether_deposit_pos,
                    0,
                    RECIPE_AETHER,  # aether extraction recipe
                    Priority.Normal
                )
                self.built_aether_drill = True
                self.last_build_attempt = current_tick
                uw_game.log_info("    Aether drill placement command sent")
                return  # Return after placing to avoid multiple builds in one tick
            else:
                uw_game.log_info(f"  Waiting for metal to build aether drill (have {metal_count}, need 20)")
        
        # Build Laboratory after we have basic production (2+ factories) AND aether drill for upgrades
        if (self.built_bots_factory_count >= 2 and 
            self.built_aether_drill and  # Now require aether drill first
            not self.built_laboratory and 
            self.CONSTRUCTION_LABORATORY is not None):
            
            # Check if we have enough resources (laboratory needs metal)
            metal_count = 0
            for entity in uw_world.entities().values():
                if entity.own() and entity.Amount is not None and entity.Proto:
                    if entity.Proto.proto == 3637378061:  # Metal
                        metal_count += entity.Amount.amount
            
            if metal_count >= 25:  # Further reduced - with 4 factories consuming 48 metal/cycle, we need lower threshold
                # Find aether drill position to place laboratory nearby
                aether_drill_pos = None
                if self.built_aether_drill and self.aether_deposit_pos:
                    aether_drill_pos = self.aether_deposit_pos
                else:
                    # Fallback to control core if no aether drill yet
                    aether_drill_pos = control_core_pos
                
                lab_pos = uw_world.find_construction_placement(
                    self.CONSTRUCTION_LABORATORY,
                    aether_drill_pos,  # Place near aether drill, not control core
                    0  # Will set recipe later when aether drill is built
                )
                if lab_pos != -1:
                    uw_game.log_info(f">>> PLACING LABORATORY at position {lab_pos} (near aether drill for unit upgrades)")
                    if aether_drill_pos != control_core_pos:
                        uw_game.log_info(f"    Distance from aether drill: {uw_map.distance_estimate(aether_drill_pos, lab_pos)}")
                    else:
                        uw_game.log_info(f"    Distance from core: {uw_map.distance_estimate(control_core_pos, lab_pos)}")
                    uw_commands.place_construction(
                        self.CONSTRUCTION_LABORATORY,
                        lab_pos,
                        0,
                        0,  # Will set recipe later when aether drill is built
                        Priority.Normal
                    )
                    self.built_laboratory = True
                    self.last_build_attempt = current_tick
                    uw_game.log_info("    Laboratory placement command sent")
                    return
                else:
                    uw_game.log_warning("Could not find valid position for laboratory!")
            else:
                uw_game.log_info(f"  Waiting for metal to build laboratory (have {metal_count}, need 25)")
        
        # Build Vehicle Factory after laboratory to replace lost ATVs
        if (self.built_bots_factory_count >= 3 and  # After we have good combat production
            self.built_laboratory and  # After research capability established  
            not self.built_vehicle_factory and
            self.CONSTRUCTION_VEHICLE_FACTORY is not None):
            
            # Check ATV levels - build vehicle factory if we're low on ATVs
            force_stats = uw_world.my_force_statistics()
            should_build_vehicle_factory = False
            
            if force_stats:
                total_atvs = force_stats.logisticsUnitsTotal
                idle_atvs = force_stats.logisticsUnitsIdle
                
                # Build vehicle factory if:
                # 1. We have fewer than 8 ATVs total, OR
                # 2. We have 0% idle ATVs (all overworked)
                if total_atvs < 8 or idle_atvs == 0:
                    should_build_vehicle_factory = True
                    uw_game.log_info(f"  ATV Crisis: {idle_atvs}/{total_atvs} ATVs idle - need vehicle factory")
                else:
                    uw_game.log_info(f"  ATV Status OK: {idle_atvs}/{total_atvs} ATVs idle")
            else:
                # No force stats available, play it safe and build
                should_build_vehicle_factory = True
                
            if should_build_vehicle_factory:
                # Check if we have enough resources (vehicle factory needs metal)
                metal_count = 0
                for entity in uw_world.entities().values():
                    if entity.own() and entity.Amount is not None and entity.Proto:
                        if entity.Proto.proto == 3637378061:  # Metal
                            metal_count += entity.Amount.amount
                
                if metal_count >= 25:  # Same threshold as other buildings
                    vehicle_factory_pos = uw_world.find_construction_placement(
                        self.CONSTRUCTION_VEHICLE_FACTORY,
                        control_core_pos,
                        0  # Will set recipe after placement
                    )
                    if vehicle_factory_pos != -1:
                        uw_game.log_info(f">>> PLACING VEHICLE FACTORY at position {vehicle_factory_pos} to produce replacement ATVs")
                        uw_game.log_info(f"    Distance from core: {uw_map.distance_estimate(control_core_pos, vehicle_factory_pos)}")
                        uw_commands.place_construction(
                            self.CONSTRUCTION_VEHICLE_FACTORY,
                            vehicle_factory_pos,
                            0,
                            0,  # Will set recipe later
                            Priority.Normal
                        )
                        self.built_vehicle_factory = True
                        self.last_build_attempt = current_tick
                        uw_game.log_info("    Vehicle factory placement command sent")
                        return
                    else:
                        uw_game.log_warning("Could not find valid position for vehicle factory!")
                else:
                    uw_game.log_info(f"  Waiting for metal to build vehicle factory (have {metal_count}, need 25)")

        # Build Fabricators for production speed bonuses (+5% every 30s, max +100%)
        # Build first at ~3min (180s = tick 3600), second at ~5min (300s = tick 6000)
        target_fabricators = 0
        if current_tick >= 3600 and self.built_refinery:  # After 3 minutes and refinery is built
            target_fabricators = 1
        if current_tick >= 6000 and self.built_bots_factory_count >= 3:  # After 5 minutes and 3+ factories
            target_fabricators = 2
            
        if (self.built_fabricator_count < target_fabricators and 
            self.CONSTRUCTION_FABRICATOR is not None):
            
            # Check resources - fabricators need metal and consume oil
            metal_count = 0
            oil_count = 0
            for entity in uw_world.entities().values():
                if entity.own() and entity.Amount is not None and entity.Proto:
                    if entity.Proto.proto == 3637378061:  # Metal
                        metal_count += entity.Amount.amount
                    elif entity.Proto.proto == 3626035542:  # Oil
                        oil_count += entity.Amount.amount
            
            # Only build if we have stable oil production (50+ oil) and metal
            if metal_count >= 25 and oil_count >= 50:
                # Place fabricators near oil drill since they consume oil continuously
                oil_drill_pos = None
                if self.built_oil_drill and self.oil_deposit_pos:
                    oil_drill_pos = self.oil_deposit_pos
                else:
                    # Fallback to control core if no oil drill yet
                    oil_drill_pos = control_core_pos
                
                fab_pos = uw_world.find_construction_placement(
                    self.CONSTRUCTION_FABRICATOR,
                    oil_drill_pos,  # Place near oil drill since fabricators consume oil
                    2258394140  # Fabrication recipe ID from recipes.md
                )
                if fab_pos != -1:
                    fabricator_num = self.built_fabricator_count + 1
                    uw_game.log_info(f">>> PLACING FABRICATOR #{fabricator_num} at position {fab_pos} (near oil drill, +5% production speed every 30s)")
                    if oil_drill_pos != control_core_pos:
                        uw_game.log_info(f"    Distance from oil drill: {uw_map.distance_estimate(oil_drill_pos, fab_pos)}")
                    else:
                        uw_game.log_info(f"    Distance from core: {uw_map.distance_estimate(control_core_pos, fab_pos)}")
                    uw_game.log_info(f"    Resources: Metal={metal_count}, Oil={oil_count}")
                    uw_commands.place_construction(
                        self.CONSTRUCTION_FABRICATOR,
                        fab_pos,
                        0,
                        2258394140,  # Fabrication recipe
                        Priority.Normal
                    )
                    self.built_fabricator_count += 1
                    self.last_build_attempt = current_tick
                    uw_game.log_info(f"    Fabricator #{fabricator_num} placement command sent")
                    return
                else:
                    uw_game.log_warning("Could not find valid position for fabricator!")
            else:
                uw_game.log_info(f"  Waiting for resources to build fabricator #{target_fabricators} (Metal: {metal_count}, Oil: {oil_count}, need Metal: 25)")
        
        uw_game.log_info("=== END BUILD INFRASTRUCTURE CHECK ===")
    
    def manage_production(self):
        """Set recipes and manage production queues"""
        
        uw_game.log_info("=== MANAGE PRODUCTION CHECK ===")
        
        # Determine which unit to produce based on threats
        selected_recipe = self.RECIPE_JUGGERNAUT  # Default to Juggernaut
        
        # Check enemy composition for adaptive strategy
        total_enemy_units = sum(self.enemy_unit_counts.values())
        if total_enemy_units > 0:
            # Log enemy composition for strategy decision
            uw_game.log_info(f"Enemy composition detected: {self.enemy_unit_counts}")
            
            # Simple adaptive strategy:
            # - Against many light units (maggots), Juggernauts are good
            # - Against heavy units (overlord), still use Juggernauts
            # Could be expanded to use different units if available
            if 'maggot' in self.enemy_unit_counts and self.enemy_unit_counts['maggot'] > 5:
                uw_game.log_info("  Strategy: Mass Juggernauts against maggot swarm")
            elif 'overlord' in self.enemy_unit_counts:
                uw_game.log_info("  Strategy: Juggernauts to counter overlord threat")
        
        own_building_count = 0
        actual_factory_count = 0  # Count actual built factories
        
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
            
            # Set refinery to produce fuel rods (refinery unit ID is 2183816954)
            if proto_id == 2183816954 and entity.Recipe is None:
                uw_game.log_info(f">>> SETTING REFINERY {entity.id} to produce fuel rods (recipe {self.RECIPE_FUEL_RODS})")
                uw_commands.set_recipe(entity.id, self.RECIPE_FUEL_RODS)
            
            # Set laboratory to research upgrades (laboratory unit ID is 3612099239)
            elif proto_id == 3612099239 and entity.Recipe is None:
                # Only set recipe if we have aether drill built (need aether for upgrades)
                if self.built_aether_drill:
                    # Check if we have any aether available (need 5 aether for upgrade)
                    aether_count = 0
                    for resource_entity in uw_world.entities().values():
                        if resource_entity.own() and resource_entity.Amount is not None and resource_entity.Proto:
                            if resource_entity.Proto.proto == 3005410251:  # Aether
                                aether_count += resource_entity.Amount.amount
                    
                    if aether_count >= 5:
                        uw_game.log_info(f">>> SETTING LABORATORY {entity.id} to research Tripod range upgrades (recipe {self.RECIPE_TRIPOD_RANGE})")
                        uw_commands.set_recipe(entity.id, self.RECIPE_TRIPOD_RANGE)
                    else:
                        uw_game.log_info(f"  Laboratory {entity.id} waiting for aether (have {aether_count}, need 5)")
                else:
                    uw_game.log_info(f"  Laboratory {entity.id} waiting for aether drill to be built")
            
            # Set vehicle factory to produce ATVs (vehicle factory unit ID is 3797798415)
            elif proto_id == 3797798415 and entity.Recipe is None:
                # Check if we have enough resources for ATV production (2 metal per ATV)
                metal_count = 0
                for resource_entity in uw_world.entities().values():
                    if resource_entity.own() and resource_entity.Amount is not None and resource_entity.Proto:
                        if resource_entity.Proto.proto == 3637378061:  # Metal
                            metal_count += resource_entity.Amount.amount
                
                if metal_count >= 4:  # Need at least 4 metal to produce 2 ATVs
                    uw_game.log_info(f">>> SETTING VEHICLE FACTORY {entity.id} to produce ATVs (recipe {self.RECIPE_ATV})")
                    uw_commands.set_recipe(entity.id, self.RECIPE_ATV)
                else:
                    uw_game.log_info(f"  Vehicle factory {entity.id} waiting for metal (have {metal_count}, need 4)")
            
            # Set bots factory to produce units (bots factory unit ID is 3126591205)
            elif proto_id == 3126591205:
                # First factory produces Tripods (fast, cheap), rest produce Juggernauts (heavy)
                if actual_factory_count == 0:
                    # This is the first factory - produce Tripods for rapid defense
                    desired_recipe = self.RECIPE_TRIPOD
                    unit_type = "TRIPODS (fast response)"
                else:
                    # Subsequent factories produce Juggernauts for heavy assault
                    desired_recipe = self.RECIPE_JUGGERNAUT
                    unit_type = "JUGGERNAUTS (heavy assault)"
                
                actual_factory_count += 1
                
                if entity.Recipe is None or entity.Recipe.recipe != desired_recipe:
                    uw_game.log_info(f">>> SETTING BOTS FACTORY #{actual_factory_count} (entity {entity.id}) to produce {unit_type} (recipe {desired_recipe})")
                    uw_commands.set_recipe(entity.id, desired_recipe)
            
            # Count combat units
            # Juggernaut unit ID is 2187484756
            # Tripod unit ID is 3778674520
            elif proto_id == 2187484756:
                uw_game.log_info(f">>> JUGGERNAUT UNIT {entity.id} at position {entity.pos()}")
                self.has_combat_units = True  # Mark that we have combat units
            elif proto_id == 3778674520:
                uw_game.log_info(f">>> TRIPOD UNIT {entity.id} at position {entity.pos()}")
                self.has_combat_units = True  # Mark that we have combat units
        
        # Only update factory count if we see MORE factories than we thought we had
        # (Don't decrease it, as that would allow placing more)
        if actual_factory_count > self.built_bots_factory_count:
            uw_game.log_info(f"  Factory count updated: {self.built_bots_factory_count} -> {actual_factory_count}")
            self.built_bots_factory_count = actual_factory_count
        elif actual_factory_count < self.built_bots_factory_count:
            uw_game.log_info(f"  Waiting for factories to be built: {actual_factory_count} built, {self.built_bots_factory_count} placed")
        
        uw_game.log_info(f"Total owned buildings: {own_building_count}")
        uw_game.log_info("=== END MANAGE PRODUCTION CHECK ===")
    
    def analyze_threats(self):
        """Analyze enemy units and log threat assessment"""
        current_tick = uw_game.game_tick()
        
        # Reset enemy counts
        self.enemy_unit_counts.clear()
        enemy_units_near_base = []
        
        # Find our control core
        control_core_pos = None
        CONTROL_CORE_ID = 3805195479
        for entity in uw_world.entities().values():
            if entity.own() and entity.Proto and entity.Proto.proto == CONTROL_CORE_ID:
                control_core_pos = entity.pos()
                break
        
        if not control_core_pos:
            return
        
        # Count enemy units
        for entity in uw_world.entities().values():
            if entity.enemy() and entity.Unit is not None and entity.Proto:
                proto_name = entity.proto().name
                proto_id = entity.Proto.proto
                
                # Count by type
                if proto_name not in self.enemy_unit_counts:
                    self.enemy_unit_counts[proto_name] = 0
                self.enemy_unit_counts[proto_name] += 1
                
                # Check if near our base
                distance = uw_map.distance_estimate(control_core_pos, entity.pos())
                if distance < 1000:  # Within 1000 units of base
                    enemy_units_near_base.append((proto_name, entity.id, distance))
        
        # Log every 200 ticks (10 seconds)
        if current_tick - self.last_enemy_log > 200:
            self.last_enemy_log = current_tick
            uw_game.log_info("=== THREAT ASSESSMENT ===")
            uw_game.log_info(f"Enemy unit types detected:")
            for unit_type, count in sorted(self.enemy_unit_counts.items(), key=lambda x: x[1], reverse=True):
                uw_game.log_info(f"  {unit_type}: {count}")
            
            if enemy_units_near_base:
                uw_game.log_info(f"ENEMIES NEAR BASE (within 1000 units):")
                for name, eid, dist in sorted(enemy_units_near_base, key=lambda x: x[2]):
                    uw_game.log_info(f"  {name} (ID: {eid}) at distance {dist:.0f}")
            
            # Log our forces for comparison
            our_units = {}
            for entity in uw_world.entities().values():
                if entity.own() and entity.Unit is not None and entity.Proto:
                    proto_name = entity.proto().name
                    if proto_name not in ['ATV', 'control core']:  # Skip workers and base
                        if proto_name not in our_units:
                            our_units[proto_name] = 0
                        our_units[proto_name] += 1
            
            uw_game.log_info(f"Our combat units:")
            for unit_type, count in sorted(our_units.items(), key=lambda x: x[1], reverse=True):
                uw_game.log_info(f"  {unit_type}: {count}")
            
            uw_game.log_info("=== END THREAT ASSESSMENT ===")
    
    def log_resources(self):
        """Log current resource amounts"""
        # Resource IDs from CLAUDE.md
        RESOURCE_IDS = {
            2364352315: "Biomass",
            3637378061: "Metal",
            3626035542: "Oil", 
            2338948473: "Fuel rods",
            2595104821: "Plasma cells",
            2951452234: "Refined metal",
            3005410251: "Aether",
            3145327874: "Ore"
        }
        
        uw_game.log_info("=== RESOURCE STATUS ===")
        # Resources are stored as entities with Amount component
        resource_counts = {}
        for entity in uw_world.entities().values():
            if entity.own() and entity.Amount is not None:
                # This is a resource pile owned by us
                proto_id = entity.Proto.proto if entity.Proto else None
                if proto_id in RESOURCE_IDS:
                    resource_name = RESOURCE_IDS[proto_id]
                    amount = entity.Amount.amount
                    if resource_name not in resource_counts:
                        resource_counts[resource_name] = 0
                    resource_counts[resource_name] += amount
        
        # Log the totals
        for resource_name, total in resource_counts.items():
            uw_game.log_info(f"  {resource_name}: {total}")
        
        if not resource_counts:
            uw_game.log_info("  No resources yet")
        
        uw_game.log_info("=== END RESOURCE STATUS ===")
    
    def control_juggernauts(self):
        """Control existing juggernaut units - make them dance and stay safe!"""
        import math
        
        # Find control core position
        control_core_pos = None
        CONTROL_CORE_ID = 3805195479
        for entity in uw_world.entities().values():
            if entity.own() and entity.Proto and entity.Proto.proto == CONTROL_CORE_ID:
                control_core_pos = entity.pos()
                break
        
        if control_core_pos is None:
            return
        
        juggernauts = []  # Heavy units - stay close for defense
        tripods = []  # Ranged units - can roam and kite
        enemies = []
        enemy_bases = []  # Track enemy control cores
        
        JUGGERNAUT_ID = 2187484756
        TRIPOD_ID = 3778674520
        
        for entity in uw_world.entities().values():
            if entity.Unit is None:
                continue
                
            # Check if it's our combat unit
            if entity.own() and entity.Proto:
                if entity.Proto.proto == JUGGERNAUT_ID:
                    juggernauts.append(entity)
                elif entity.Proto.proto == TRIPOD_ID:
                    tripods.append(entity)
            elif entity.enemy():
                enemies.append(entity)
                # Check if it's an enemy control core
                if entity.Proto and entity.Proto.proto == CONTROL_CORE_ID:
                    enemy_bases.append(entity)
        
        # Combine units for processing but with different behaviors
        all_combat_units = []
        for unit in juggernauts:
            all_combat_units.append(('juggernaut', unit))
        for unit in tripods:
            all_combat_units.append(('tripod', unit))
        
        if not all_combat_units:
            return
        
        # Movement parameters for JUGGERNAUTS - aggressive base defense
        JUGG_MIN_DISTANCE = 50.0   # Stay close to base core
        JUGG_MAX_DISTANCE = 300.0  # Patrol wide area to intercept threats
        JUGG_RECALL_DISTANCE = 400.0  # Allow longer excursions to chase threats
        
        # Movement parameters for TRIPODS - can roam and kite with range
        TRIPOD_MIN_DISTANCE = 100.0  # Can move further from base
        TRIPOD_MAX_DISTANCE = 400.0  # Extended range for kiting
        TRIPOD_RECALL_DISTANCE = 500.0  # Can operate at longer range
        TRIPOD_KITE_DISTANCE = 250.0  # Keep this distance from enemies while shooting
        
        ENEMY_BASE_DANGER_DISTANCE = 600.0  # Don't get too close to enemy bases
        ENGAGE_DISTANCE = 300.0  # Defense perimeter matching base size (deposits ~260 units from core)
        
        current_tick = uw_game.game_tick()
        
        # Log every 100 ticks to avoid spam
        should_log = current_tick % 100 == 0
        
        for i, (unit_type, unit) in enumerate(all_combat_units):
            unit_pos = unit.pos()
            distance_from_base = uw_map.distance_estimate(control_core_pos, unit_pos)
            
            # Set parameters based on unit type
            if unit_type == 'juggernaut':
                MIN_DISTANCE = JUGG_MIN_DISTANCE
                MAX_DISTANCE = JUGG_MAX_DISTANCE
                RECALL_DISTANCE = JUGG_RECALL_DISTANCE
                DANCE_RADIUS = 100.0
            else:  # tripod
                MIN_DISTANCE = TRIPOD_MIN_DISTANCE
                MAX_DISTANCE = TRIPOD_MAX_DISTANCE
                RECALL_DISTANCE = TRIPOD_RECALL_DISTANCE
                DANCE_RADIUS = 300.0
            
            # Calculate distance to nearest enemy base
            min_enemy_base_distance = float('inf')
            nearest_enemy_base = None
            for enemy_base in enemy_bases:
                dist = uw_map.distance_estimate(unit_pos, enemy_base.pos())
                if dist < min_enemy_base_distance:
                    min_enemy_base_distance = dist
                    nearest_enemy_base = enemy_base
            
            # Log distances periodically
            if should_log:
                log_msg = f"{unit_type.capitalize()} {unit.id}: Base dist={distance_from_base:.0f}"
                if nearest_enemy_base:
                    log_msg += f", Nearest enemy base dist={min_enemy_base_distance:.0f}"
                uw_game.log_info(log_msg)
            
            # Check if there are existing orders
            if len(uw_commands.orders(unit.id)) > 0:
                continue  # Skip if already has orders
            
            # PRIORITY 0: Emergency retreat if damaged or outnumbered
            # Check unit health
            is_damaged = False
            health_percent = 100
            if unit.Life and unit.proto().data.get("life", 0) > 0:
                max_life = unit.proto().data.get("life")
                current_life = unit.Life.life
                health_percent = (current_life / max_life) * 100
                is_damaged = health_percent < 50
            
            # Check if outnumbered (enemies within 200 units)
            nearby_enemies = []
            nearby_allies = []
            CHECK_RADIUS = 200.0
            
            for e in enemies:
                if uw_map.distance_estimate(unit_pos, e.pos()) < CHECK_RADIUS:
                    nearby_enemies.append(e)
            
            for other_type, other_unit in all_combat_units:
                if other_unit.id != unit.id:
                    if uw_map.distance_estimate(unit_pos, other_unit.pos()) < CHECK_RADIUS:
                        nearby_allies.append(other_unit)
            
            is_outnumbered = len(nearby_enemies) > len(nearby_allies) + 1
            
            # Retreat if damaged or badly outnumbered
            if is_damaged or (is_outnumbered and len(nearby_enemies) >= 3):
                retreat_reason = f"HP: {health_percent:.0f}%" if is_damaged else f"Outnumbered {len(nearby_enemies)}v{len(nearby_allies)+1}"
                uw_game.log_warning(f">>> RETREATING {unit_type} {unit.id} - {retreat_reason}")
                # Run directly back to base
                retreat_tiles = uw_map.area_neighborhood(control_core_pos, 50)
                if retreat_tiles:
                    uw_commands.order(unit.id, uw_commands.run_to_position(retreat_tiles[0]))
                continue
            
            # PRIORITY 1: Recall if too far from base or too close to enemy base
            if distance_from_base > RECALL_DISTANCE:
                uw_game.log_warning(f">>> RECALLING {unit_type} {unit.id} - too far from base ({distance_from_base:.0f} > {RECALL_DISTANCE})")
                # Move back toward base
                recall_tiles = uw_map.area_neighborhood(control_core_pos, DANCE_RADIUS)
                if recall_tiles:
                    target_pos = recall_tiles[0]
                    uw_commands.order(unit.id, uw_commands.run_to_position(target_pos))
                continue
            
            if min_enemy_base_distance < ENEMY_BASE_DANGER_DISTANCE:
                uw_game.log_warning(f">>> RECALLING {unit_type} {unit.id} - too close to enemy base ({min_enemy_base_distance:.0f} < {ENEMY_BASE_DANGER_DISTANCE})")
                # Move back toward base
                recall_tiles = uw_map.area_neighborhood(control_core_pos, DANCE_RADIUS)
                if recall_tiles:
                    target_pos = recall_tiles[0]
                    uw_commands.order(unit.id, uw_commands.run_to_position(target_pos))
                continue
            
            # PRIORITY 2: Attack enemies ONLY if they're threatening our base
            # Find enemies close to OUR base, not close to the juggernaut
            base_threatening_enemies = []
            for e in enemies:
                enemy_dist_to_base = uw_map.distance_estimate(control_core_pos, e.pos())
                if enemy_dist_to_base < ENGAGE_DISTANCE:  # Enemy is near our base
                    base_threatening_enemies.append((e, enemy_dist_to_base))
            
            if base_threatening_enemies:
                # Attack the closest enemy to our base
                target, dist = min(base_threatening_enemies, key=lambda x: x[1])
                uw_commands.order(unit.id, uw_commands.fight_to_entity(target.id))
                uw_game.log_warning(f"DEFENDING: {unit_type} {unit.id} attacking enemy {target.id} at {dist:.0f} from base")
                continue
            
            # PRIORITY 3: Patrol/Dance logic with individual tracking
            jugg_id = unit.id
            
            # Initialize state for new juggernauts
            if jugg_id not in self.juggernaut_states:
                self.juggernaut_states[jugg_id] = {
                    'angle': i * math.pi / 2,  # Start at different angles
                    'last_pos': unit_pos,
                    'patrol_index': i * 4,  # Offset patrol points
                    'direction': 1  # 1 for clockwise, -1 for counter-clockwise
                }
            
            state = self.juggernaut_states[jugg_id]
            
            # Update angle for smooth circular movement (individual speed per juggernaut)
            angle_speed = 0.02 + (i * 0.005)  # Slightly different speeds to avoid clustering
            state['angle'] += angle_speed * state['direction']
            state['angle'] = state['angle'] % (2 * math.pi)
            
            # Get positions at the target radius from control core
            area_tiles = uw_map.area_neighborhood(control_core_pos, DANCE_RADIUS)
            if not area_tiles:
                continue
            
            # Use angle to select position around the circle
            # Divide the available tiles into segments based on angle
            num_tiles = len(area_tiles)
            # Select tile based on current angle
            tile_index = int((state['angle'] / (2 * math.pi)) * num_tiles) % num_tiles
            
            # Sort tiles by their angle relative to base for consistent circular movement
            # This is approximate but should give smoother movement
            target_pos = area_tiles[tile_index]
            
            # Adjust based on distance
            if distance_from_base < MIN_DISTANCE:
                # Too close, move away
                uw_game.log_info(f"{unit_type.capitalize()} {unit.id} too close ({distance_from_base:.0f}), moving away")
                # Pick a position further out
                far_tiles = uw_map.area_neighborhood(control_core_pos, DANCE_RADIUS * 1.2)
                if far_tiles:
                    # Use angle-based selection
                    idx = int((state['angle'] / (2 * math.pi)) * len(far_tiles)) % len(far_tiles)
                    target_pos = far_tiles[idx]
            elif distance_from_base > MAX_DISTANCE:
                # Too far, come back
                uw_game.log_info(f"{unit_type.capitalize()} {unit.id} too far ({distance_from_base:.0f}), returning")
                # Pick a position closer
                close_tiles = uw_map.area_neighborhood(control_core_pos, DANCE_RADIUS * 0.8)
                if close_tiles:
                    # Use angle-based selection
                    idx = int((state['angle'] / (2 * math.pi)) * len(close_tiles)) % len(close_tiles)
                    target_pos = close_tiles[idx]
            
            # Issue movement order
            uw_commands.order(unit.id, uw_commands.run_to_position(target_pos))
            
            # Update last position
            state['last_pos'] = unit_pos
            
            # Log movement with angle for debugging
            if should_log or distance_from_base < MIN_DISTANCE or distance_from_base > MAX_DISTANCE:
                uw_game.log_info(f"{unit_type.capitalize()} {unit.id} moving to {target_pos} (dist: {distance_from_base:.0f}, angle: {state['angle']:.2f})")
    
    def on_update(self, stepping: bool):
        # Configure during session state
        if uw_game.game_state() == GameState.Session:
            self.configure()
            
            # Admin setup no longer needed - map is set via connect_new_server
            # if not self.admin_setup_done and uw_world.is_admin():
            #     self.admin_setup_done = True
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
        
        # Log resources every 200 ticks
        if self.work_step % 200 == 0:
            self.log_resources()
        
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
            case 15:
                # Analyze threats
                self.analyze_threats()
            case 20:
                # Control units
                self.control_juggernauts()
    
    def run(self):
        uw_game.log_info("Juggernaut bot start")
        
        # Try to reconnect first, then fallback to new server
        if not uw_game.try_reconnect():
            # Enable admin commands and observer mode for better game setup
            uw_game.set_connect_start_gui(True, "--observer 2")
            if not uw_game.connect_environment():
                # Create new server with admin privileges to set map and AI
                uw_game.log_info("Creating new server with admin privileges")
                uw_game.connect_new_server(0, "Juggernaut vs AI Test", "--allowUwApiAdmin 1")
            else:
                # Connect to existing environment
                uw_game.log_info("Connected to existing environment")
        
        uw_game.log_info("Juggernaut bot done")
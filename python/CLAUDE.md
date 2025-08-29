# CLAUDE.md - Important Instructions for Claude

## Critical Rules

### NEVER GUESS - Always Check Existing Code
- **NEVER improvise or guess at API usage, enum names, or function signatures**
- **ALWAYS check the existing bot.py and uwapi library code for the correct patterns**
- **ALWAYS verify enum names, class names, and method signatures before using them**
- When implementing new features, follow the exact patterns used in bot.py
- If unsure about an API call, search the codebase first with grep/read tools

### Example of What NOT to Do
- ❌ Guessing enum names like `MapState.Loaded` when it's actually `UwMapStateEnum.Loaded`
- ❌ Making up patterns that don't exist in the codebase
- ❌ Assuming how the API works without checking bot.py first

### Example of What TO Do
- ✅ Check bot.py for initialization patterns
- ✅ Verify exact enum names in uwapi/__init__.py or interop.py
- ✅ Copy working patterns from existing code
- ✅ Use grep to find correct usage examples

## Project Structure
- `bot/bot.py` - Reference implementation showing correct API usage
- `uwapi/` - The game API library (DO NOT modify, only read for reference)
- `main.py` - Entry point that shows proper initialization

## Common Patterns from bot.py
1. Event handling: `uw_events.on_update(self.on_update)`
2. Game state checking: `if uw_game.game_state() == GameState.Session:`
3. Stepping check: `if not stepping: return`
4. Connection sequence: `try_reconnect() -> set_connect_start_gui(True) -> connect_environment() -> connect_new_server()`

## Game Mechanics

### Resource System
The game uses numeric IDs for resources. Common resources include:
- **2364352315**: Biomass (organic base resource)
- **3637378061**: Metal (mineral base resource)  
- **3626035542**: Oil (extracted resource)
- **2338948473**: Fuel rods (processed from oil)
- **2595104821**: Plasma cells (advanced resource)
- **2951452234**: Refined metal
- **3005410251**: Aether (special resource)
- **3145327874**: Ore (raw form, needs smelting)

### Resource Deposits & placeOver Mechanic
Buildings that extract resources must be placed on specific deposit types using the `placeOver` field:
- **2702889254**: Metal deposit (for extracting metal)
- **3984569945**: Oil deposit (for extracting oil/deep oil)
- **2535003968**: Aether deposit (for extracting aether)
- **0**: No placement requirement (can build anywhere)

Example: A Drill can produce different resources depending on where it's built:
- Drill on metal deposit (2702889254) → produces Metal
- Drill on oil deposit (3984569945) → produces Oil
- Drill on aether deposit (2535003968) → produces Aether

### Recipe Structure
Recipes in the game have these key fields:
- `inputs`: Resources consumed (ID: amount pairs)
- `outputs`: Resources produced (ID: amount pairs)
- `duration`: Time in game ticks (20 ticks per second)
- `placeOver`: Required deposit type (0 = anywhere)

### Production Chain Example (Juggernaut)
1. Drill on metal deposit → Metal (1/60 ticks)
2. Drill on oil deposit → Oil (1/60 ticks)
3. Refinery: Oil → Fuel rods (1:1, 60 ticks)
4. Bots Factory: 1 fuel rod + 12 metal → Juggernaut (1440 ticks)

### Building & Recipe Management
- **Buildings must be placed with `uw_commands.place_construction(proto_id, position, yaw, recipe_id, priority)`**
- **Buildings are entities** - check `uw_world.entities()` for owned buildings
- **Recipes are set on existing buildings** with `uw_commands.set_recipe(entity_id, recipe_id)`
- **Building IDs (from recipes.md):**
  - Drill: 2910644843
  - Refinery: 2183816954
  - Bots Factory: 3126591205
- **Recipe assignment**: Buildings can only use recipes from their `recipes` list in prototype data

### Finding Resources (from docs)
- **Resource deposits ARE entities** - neutral units like ore deposits, oil wells, etc.
- **Place-over requirement**: Extractors (drills) must be placed ON the deposit entity position
- **Finding deposits**: Loop through `uw_world.entities()` and check for neutral entities that are resource deposits
- **Deposit identification**: Check entity proto name or tags for "ore", "oil", "deposit", etc.
- **Actions are async**: Buildings won't appear immediately after placement - wait several ticks

### Race Setting
- Use `uw_game.set_force_race(race_proto_id)` during configuration
- Get race ID with `uw_prototypes.hashString("technocracy")` or use direct ID if known
- Must be called during Session state configuration

### Map & Tiles (from docs)
- **Tiles**: Discrete positions, indexed 0..N-1, ~10 meters apart
- **Clusters**: Groups of tiles with same terrain type
- **Overview**: Use `uw_world.overview_flags(position)` to check what's on a tile
- **Overview entities**: `uw_world.overview_entities(position)` returns entity IDs at that position
- **Terrain types**: Each tile has a terrain type index

### Entity Components (from docs)
- **Proto Component**: Defines the prototype (immutable type)
- **Owner Component**: Which force owns it (immutable)
- **Position Component**: Tile index where entity is placed
- **Unit Component**: State info (shooting, processing, damaged, etc.)
- **Recipe Component**: Current recipe being processed
- **Amount Component**: Resource count (for resource entities)

### Prototype Tags (from docs)
Important tags for identifying entities:
- `miner`: generates resources from deposits
- `production`: produces units
- `research`: produces upgrades
- `worker`: carries resources
- `nonprogression`: alternative prototype
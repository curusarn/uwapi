from uwapi import *
import json
import time
import os

# Save the original working directory before UwapiLibrary changes it
ORIGINAL_CWD = os.getcwd()

class RecipeExtractorBot:
    is_configured: bool = False
    recipes_extracted: bool = False
    
    def __init__(self):
        uw_events.on_update(self.on_update)
    
    def configure(self):
        if self.is_configured:
            return
        self.is_configured = True
        
        uw_game.log_info("Configuring recipe extractor bot...")
        uw_game.set_player_name("recipe-extractor")
        uw_game.player_join_force(0)  # create new force
        uw_game.set_force_color(0, 1, 0)  # green
    
    def on_update(self, stepping: bool):
        # Configure during session state like the bot does
        if uw_game.game_state() == GameState.Session:
            self.configure()
            return
        
        if not stepping:
            return
        
        # Only extract recipes once when stepping and prototypes are available
        if not self.recipes_extracted and len(uw_prototypes._all) > 0:
            self.recipes_extracted = True
            uw_game.log_info("Prototypes loaded, extracting recipes...")
            self.extract_and_save_recipes()
    
    def extract_and_save_recipes(self):
        """Extract all recipes from the game and save them as markdown."""
        uw_game.log_info("Extracting recipes...")
        
        # Collect all recipes
        recipes = {}
        units_with_recipes = []
        races = {}
        
        # Get all prototypes
        for proto_id, prototype in uw_prototypes._all.items():
            # Check if this prototype has recipes
            if "recipes" in prototype.data:
                unit_recipes = prototype.data["recipes"]
                if unit_recipes:
                    units_with_recipes.append({
                        "name": prototype.name,
                        "id": proto_id,
                        "type": str(prototype.type).split(".")[-1],
                        "recipes": unit_recipes
                    })
            
            # Check if this is a recipe prototype itself
            if prototype.type == PrototypeType.Recipe:
                recipes[proto_id] = {
                    "name": prototype.name,
                    "id": proto_id,
                    "data": prototype.data
                }
            
            # Check if this is a race prototype
            if prototype.type == PrototypeType.Race:
                races[proto_id] = {
                    "name": prototype.name,
                    "id": proto_id,
                    "data": prototype.data
                }
        
        # Create markdown output
        md_output = "# Game Recipes\n\n"
        md_output += f"*Extracted from game on {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        # Section 1: All Recipe Prototypes
        md_output += "## Recipe Prototypes\n\n"
        md_output += f"Total recipes found: {len(recipes)}\n\n"
        
        if recipes:
            for recipe_id, recipe_info in sorted(recipes.items(), key=lambda x: x[1]['name']):
                md_output += f"### {recipe_info['name']} (ID: {recipe_id})\n\n"
                
                # Format recipe data nicely
                data = recipe_info['data']
                
                # Basic info
                if 'description' in data:
                    md_output += f"**Description:** {data['description']}\n\n"
                
                # Cost/requirements
                if 'cost' in data:
                    md_output += "**Cost:**\n"
                    for resource, amount in data['cost'].items():
                        md_output += f"- {resource}: {amount}\n"
                    md_output += "\n"
                
                # Production info
                if 'produces' in data:
                    md_output += f"**Produces:** {data['produces']}\n\n"
                
                if 'productionTime' in data:
                    md_output += f"**Production Time:** {data['productionTime']} ticks\n\n"
                
                # All other properties
                other_props = {k: v for k, v in data.items() 
                             if k not in ['name', 'description', 'cost', 'produces', 'productionTime']}
                if other_props:
                    md_output += "**Other Properties:**\n```json\n"
                    md_output += json.dumps(other_props, indent=2)
                    md_output += "\n```\n\n"
                
                md_output += "---\n\n"
        else:
            md_output += "*No recipe prototypes found*\n\n"
        
        # Section 2: Units with Recipes
        md_output += "## Units/Buildings with Recipes\n\n"
        md_output += f"Total units/buildings with recipes: {len(units_with_recipes)}\n\n"
        
        for unit in sorted(units_with_recipes, key=lambda x: x['name']):
            md_output += f"### {unit['name']} ({unit['type']}, ID: {unit['id']})\n\n"
            md_output += "**Available Recipes:**\n"
            
            for recipe_id in unit['recipes']:
                # Look up recipe name if we have it
                recipe_name = recipes.get(recipe_id, {}).get('name', f'Unknown Recipe')
                md_output += f"- {recipe_name} (ID: {recipe_id})\n"
            
            md_output += "\n---\n\n"
        
        # Section 3: Races
        md_output += "## Races\n\n"
        md_output += f"Total races found: {len(races)}\n\n"
        
        for race_id, race_info in sorted(races.items(), key=lambda x: x[1]['name']):
            md_output += f"### {race_info['name']} (ID: {race_id})\n\n"
            md_output += "```json\n"
            md_output += json.dumps(race_info['data'], indent=2)
            md_output += "\n```\n\n"
        
        # Section 4: Raw Definitions (if available)
        definitions = uw_prototypes.definitions()
        if definitions:
            md_output += "## Game Definitions\n\n"
            md_output += "```json\n"
            md_output += json.dumps(definitions, indent=2)
            md_output += "\n```\n\n"
        
        # Save to file in the original working directory
        output_file = os.path.join(ORIGINAL_CWD, "recipes.md")
        with open(output_file, "w") as f:
            f.write(md_output)
        
        uw_game.log_info(f"Recipes extracted and saved to {output_file}")
        print(f"\nRecipes successfully saved to {output_file}")
        print(f"- Found {len(recipes)} recipe prototypes")
        print(f"- Found {len(units_with_recipes)} units/buildings with recipes")
        
        # Disconnect after extraction
        uw_game.disconnect()
    
    def run(self):
        uw_game.log_info("recipe-extractor start")
        if not uw_game.try_reconnect():
            uw_game.set_connect_start_gui(True)
            if not uw_game.connect_environment():
                uw_game.connect_new_server()
        uw_game.log_info("recipe-extractor done")

if __name__ == "__main__":
    with UwapiLibrary():
        RecipeExtractorBot().run()
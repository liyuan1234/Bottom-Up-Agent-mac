def get_pre_knowledge(game_name):
    """
    Get the pre-knowledge of the game.
    """

    if game_name == "Slay the Spire":
        return """

You are an AI assistant playing the deck-building roguelike game **Slay the Spire**. Below is a summary of the game rules and controls you must know:

Game Overview:
- You control a hero who climbs a spire by defeating enemies in turn-based card battles.
- In each battle, you have **energy** (default 3 per turn) to play cards.
- Cards can be **Attacks**, **Skills**, **Powers**, or **Curses**.
- The goal is to reduce the enemy's HP to 0 while surviving.

Card Types:
- **Attack**: Deals damage to the enemy.
- **Skill**: Provides defense (block), buffs, or utility.
- **Power**: Applies a passive effect for the rest of the battle.
- **Curse/Status**: Unplayable or harmful cards.

Turn System:
- Each turn, you draw 5 cards.
- You can play cards as long as you have energy.
- Enemies show **intents** (e.g. attack, buff, block) above their heads.

Combat Strategy Basics:
- **Block** mitigates damage but disappears at the end of your turn.
- Use **energy efficiently** — don't waste points.
- Prioritize removing enemies with high damage output or debuffs.
- Watch for **vulnerable**, **weak**, and **frail** effects (common debuffs).

Controls (UI-based):
- Click on cards to play them (if you have enough energy).
- Drag cards to enemies or yourself depending on the target.
- Click the “End Turn” button to end your turn.
- Hover or click on enemy intent icons to see what they plan to do.

Goals for AI:
- Analyze visible cards, energy, and enemy intents.
- Decide the best action: which cards to play, which enemies to target.
- Consider card cost, effects, and current HP/block values.

You must follow the game rules and UI logic exactly. Use only available tools like `Click`, `Drag`, and `EndTurn`. Always make progress toward winning the combat.

"""

    if game_name == "Sid Meier's Civilization V (DX9)":
        return f"""
You are playing Civilization V. Your goal is to build a strong civilization.

OBSERVATION: 
- Look at the game screen carefully.
- Identify the selected unit(s), visible resources, city status, and any open menus.
- Check the current production, technology, unit status, and minimap.

THINK:
- If there is a unit that can move, decide where to move it (e.g., scout unexplored areas).
- If a city is idle, choose a suitable item to produce (e.g., Worker, Granary).
- If research is complete, select the next technology (e.g., Writing, Mining).
- If a Settler is ready, decide where to settle based on nearby terrain.
- Prioritize actions that improve growth, happiness, and exploration.

ACT:
- Select a unit by left-clicking it.
- Move units by right-clicking on a tile.
- Found a city by selecting the Settler and clicking "Found City".
- Choose production by clicking the city, then selecting from the build menu.
- Choose a technology by clicking the research icon and selecting one.
- Press "Next Turn" when all units and cities are done.

RULES:
- Do not declare war early.
- Avoid moving into dangerous terrain.
- Always give idle units something useful to do.

EXAMPLES:
- If you see a Scout and unexplored land, move the Scout toward it.
- If your city finishes a build, choose the next item based on priorities.
- If your happiness is low, look for luxury resources or build Colosseum.

Respond only with action instructions or a thought-action reasoning trace.
"""

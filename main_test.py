import json
import pygame
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from openrouter import generate_response

# =====================================================================
# GLOBAL CUSTOMISATION & SETTINGS (Edit everything here!)
# =====================================================================

# --- 1. WINDOW & DISPLAY SETTINGS ---
WINDOW_TITLE = "THIS IS A SCREEN"
SCALE = 450                          # Scales the 3:2 window (1350 x 900 at 450)
ASPECT_W, ASPECT_H = 3, 2
WIDTH = ASPECT_W * SCALE
HEIGHT = ASPECT_H * SCALE
FPS = 60
AI_RESPONSE_LOG = Path(__file__).with_name("ai_responses.log")

# --- 2. COLOUR SCHEME (RGB Tuples) ---
COLOUR_SCREEN_BG      = (18, 20, 25)
COLOUR_PANEL_BG       = (32, 36, 46)
COLOUR_PANEL_BORDER   = (75, 85, 105)

# Wireframe-matched accent borders
COLOUR_INV_BORDER     = (0, 162, 232)    # Blue border for INV / ACTIONS panel
COLOUR_MAP_BG         = (22, 24, 32)     # Dark background inside the mini-map
COLOUR_MAP_BORDER     = (150, 25, 35)    # Crimson border for MAP box (matches wireframe)

# Map Grid Tile Colours
COLOUR_TILE_EMPTY     = (30, 33, 42)     # Wall / No room (None in 2D array)
COLOUR_TILE_ROOM      = (75, 85, 108)    # Discovered / Walkable room
COLOUR_TILE_PLAYER    = (255, 190, 80)   # Player's current (x, y) tile
COLOUR_TILE_GOAL      = (145, 95, 190)   # Goal destination

# Interactive Button & Slot Colours
COLOUR_BTN_BG         = (24, 28, 36)
COLOUR_BTN_HOVER      = (50, 60, 80)
COLOUR_BTN_BORDER     = (180, 190, 210)
COLOUR_SLOT_BG        = (20, 22, 28)
COLOUR_SLOT_BORDER    = (90, 100, 125)

# Text Colours
COLOUR_TEXT_MAIN      = (240, 235, 245)
COLOUR_TEXT_TITLE     = (255, 190, 80)
COLOUR_TEXT_ACCENT    = (100, 200, 255)
COLOUR_TEXT_HP        = (120, 230, 140)

# Item Icon Placeholder Colours
COLOUR_ICON_SWORD     = (180, 190, 205)
COLOUR_ICON_POTION    = (220, 60, 80)
COLOUR_ICON_KEY       = (230, 180, 50)

# --- 3. FONTS & TYPOGRAPHY ---
FONT_NAME             = "consolas"
FONT_SIZE_BASE        = 20
FONT_SIZE_TITLE       = 18
FONT_TITLE_BOLD       = True

# --- 4. WIREFRAME LAYOUT PROPORTIONS (Matches your diagram!) ---
UI_MARGIN             = 12    # Gap around screen edges and between main panels
PANEL_PADDING         = 20    # Inner padding inside panels
PANEL_BORDER_WIDTH    = 2
PANEL_CORNER_RADIUS   = 6

STATS_WIDTH_RATIO     = 0.25  # Left STATS column takes 25% of total width
INV_HEIGHT_RATIO      = 0.25  # Bottom-right INV / ACTIONS takes 25% of total height

# --- 5. COMPONENT SIZING & OFFSETS ---
TITLE_OFFSET_X        = 15
TITLE_OFFSET_Y        = 12
CONTENT_START_Y       = 52
TEXT_LINE_SPACING     = 34

# Mini-Map Child Component Settings (Inside top-right of GAME VIEW)
MAP_BOX_SIZE          = 210   # Width & Height of the square MAP display
MAP_BOX_MARGIN        = 20    # Distance from top-right edges of GAME VIEW
MAP_INNER_PADDING     = 14    # Padding around the 2D tile grid inside the map box
MAP_TILE_GAP          = 5     # Pixel gap between tiles in the mini-map

# Action / Choice Boxes (The 3 black rectangles inside GAME VIEW)
ACTION_BTN_W          = 145
ACTION_BTN_H          = 46
ACTION_BTN_GAP        = 20
ACTION_BTN_BOTTOM_PAD = 30    # Distance from the bottom of GAME VIEW

# Inventory Slot Settings (Horizontal row inside INV / ACTIONS)
SLOT_WIDTH            = 260
SLOT_HEIGHT           = 60
SLOT_SPACING          = 20
SLOT_CORNER_RADIUS    = 4
SLOT_BORDER_WIDTH     = 1
SLOT_ICON_SIZE        = 44
SLOT_ICON_PADDING     = 8
SLOT_TEXT_OFFSET_X    = 62
SLOT_TEXT_OFFSET_Y    = 19

# --- 6. AUTO-CALCULATED WIREFRAME GEOMETRY ---
USABLE_W = WIDTH - (UI_MARGIN * 3)
USABLE_H = HEIGHT - (UI_MARGIN * 3)

# 1. STATS Panel (Left 25% width, Full 100% height)
STATS_PANEL_X = UI_MARGIN
STATS_PANEL_Y = UI_MARGIN
STATS_PANEL_W = int(USABLE_W * STATS_WIDTH_RATIO)
STATS_PANEL_H = HEIGHT - (UI_MARGIN * 2)

# Right Column X & Width (Remaining 75% width)
RIGHT_COL_X   = STATS_PANEL_X + STATS_PANEL_W + UI_MARGIN
RIGHT_COL_W   = WIDTH - RIGHT_COL_X - UI_MARGIN

# 2. GAME VIEW Panel (Top-Right: 75% width, 75% height)
GAME_VIEW_X   = RIGHT_COL_X
GAME_VIEW_Y   = UI_MARGIN
GAME_VIEW_W   = RIGHT_COL_W
GAME_VIEW_H   = int(USABLE_H * (1.0 - INV_HEIGHT_RATIO))

# 3. INV / ACTIONS Panel (Bottom-Right: 75% width, 25% height)
INV_PANEL_X   = RIGHT_COL_X
INV_PANEL_Y   = GAME_VIEW_Y + GAME_VIEW_H + UI_MARGIN
INV_PANEL_W   = RIGHT_COL_W
INV_PANEL_H   = HEIGHT - INV_PANEL_Y - UI_MARGIN

# 4. MAP Child Box Local Coordinates (Anchored to Top-Right of GAME VIEW)
MAP_LOCAL_X   = GAME_VIEW_W - MAP_BOX_SIZE - MAP_BOX_MARGIN
MAP_LOCAL_Y   = MAP_BOX_MARGIN

# 5. Action Buttons Local Y (Near bottom of GAME VIEW)
ACTION_BTN_LOCAL_Y = GAME_VIEW_H - ACTION_BTN_H - ACTION_BTN_BOTTOM_PAD


# =====================================================================
# PYGAME INITIALISATION
# =====================================================================
pygame.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(WINDOW_TITLE)
CLOCK = pygame.time.Clock()

FONT_BASE = pygame.font.SysFont(FONT_NAME, FONT_SIZE_BASE)
FONT_TITLE = pygame.font.SysFont(FONT_NAME, FONT_SIZE_TITLE, bold=FONT_TITLE_BOLD)


# =====================================================================
# 1. MAP DATA OBJECT (2D Array of Rooms + Movement Functions)
# =====================================================================
class GAME_MAP:
    """Stores the 2D grid of rooms."""
    def __init__(self, grid_2d):
        self.grid = grid_2d
        self.rows = len(grid_2d)
        self.cols = len(grid_2d[0]) if self.rows > 0 else 0

    def get_room_at(self, x, y):
        """Returns the room dict at (x, y), or None if out of bounds or a wall."""
        if 0 <= y < self.rows and 0 <= x < self.cols:
            return self.grid[y][x]
        return None


@dataclass
class PlayerState:
    name: str
    hp: int
    max_hp: int
    attack: int
    attack_name: str
    x: int
    y: int
    inventory: list[str] = field(default_factory=list)


@dataclass
class GameGoal:
    description: str
    target: tuple[int, int]


@dataclass
class GameState:
    world_map: GAME_MAP
    player: PlayerState
    goal: GameGoal
    starting_position: tuple[int, int]
    status_message: str = "Use WASD / arrows or click actions to move."
    narrative: str = ""
    goal_completed: bool = False


@dataclass
class GameAction:
    kind: str
    target: str


def parse_initial_game_state(response_text):
    """Validate AI-generated starting data before creating the game state."""
    data = json.loads(response_text)
    if not isinstance(data, dict) or set(data) != {"narrative", "goal", "map", "player"}:
        raise ValueError("AI response must contain exactly narrative, goal, map, and player.")

    narrative = data["narrative"]
    if not isinstance(narrative, str) or not narrative.strip():
        raise ValueError("AI narrative must be a non-empty string.")
    narrative = narrative.strip()
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", narrative)]
    if len(paragraphs) != 2 or any(not paragraph for paragraph in paragraphs):
        raise ValueError("AI narrative must contain exactly two non-empty paragraphs.")
    if any(
        phrase in narrative.casefold()
        for phrase in ("an opening narrative", "two short paragraphs", "describe the setting")
    ):
        raise ValueError("AI narrative contains prompt instructions instead of in-world prose.")
    if len(narrative.split()) > 80:
        raise ValueError("AI narrative must be no more than 80 words.")

    map_data = data["map"]
    if not isinstance(map_data, dict) or set(map_data) != {"grid"}:
        raise ValueError("AI map must contain only a grid.")
    grid = map_data["grid"]
    if not isinstance(grid, list) or not 5 <= len(grid) <= 15:
        raise ValueError("AI map must have between 5 and 15 rows.")
    if any(not isinstance(row, list) for row in grid):
        raise ValueError("Every AI map row must be a list.")
    cols = len(grid[0])
    if not 5 <= cols <= 15 or any(len(row) != cols for row in grid):
        row_lengths = [len(row) for row in grid]
        raise ValueError(
            "AI map must be rectangular with between 5 and 15 columns; "
            f"received row lengths {row_lengths}."
        )

    for row_index, row in enumerate(grid):
        for col_index, room in enumerate(row):
            if room is None:
                continue
            if (
                not isinstance(room, dict)
                or set(room) != {"name", "desc", "purpose"}
                or not isinstance(room["name"], str)
                or not room["name"].strip()
                or not isinstance(room["desc"], str)
                or not room["desc"].strip()
                or not isinstance(room["purpose"], str)
                or not room["purpose"].strip()
            ):
                raise ValueError(
                    f"AI map tile ({col_index}, {row_index}) must be null or a room with name, desc, and purpose."
                )

    walkable_tiles = {
        (col_index, row_index)
        for row_index, row in enumerate(grid)
        for col_index, room in enumerate(row)
        if room is not None
    }
    if not walkable_tiles:
        raise ValueError("AI map must contain at least one walkable room.")
    connected_tiles = set()
    pending_tiles = [next(iter(walkable_tiles))]
    while pending_tiles:
        x, y = pending_tiles.pop()
        if (x, y) in connected_tiles:
            continue
        connected_tiles.add((x, y))
        pending_tiles.extend(
            (x + dx, y + dy)
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))
            if (x + dx, y + dy) in walkable_tiles
        )
    if connected_tiles != walkable_tiles:
        raise ValueError("All AI map rooms must be connected by walkable tiles.")

    goal_data = data["goal"]
    if not isinstance(goal_data, dict) or set(goal_data) != {"description", "target"}:
        raise ValueError("AI goal must contain exactly description and target.")
    goal_description = goal_data["description"]
    target_data = goal_data["target"]
    if not isinstance(goal_description, str) or not goal_description.strip():
        raise ValueError("AI goal description must be a non-empty string.")
    if not isinstance(target_data, dict) or set(target_data) != {"x", "y"}:
        raise ValueError("AI goal target must contain integer x and y coordinates.")
    target_x = target_data["x"]
    target_y = target_data["y"]
    if type(target_x) is not int or type(target_y) is not int:
        raise ValueError("AI goal target coordinates must be integers.")
    if not (0 <= target_y < len(grid) and 0 <= target_x < cols):
        raise ValueError("AI goal target coordinates are outside the map.")
    if grid[target_y][target_x] is None:
        raise ValueError("AI goal target must be a walkable room.")

    player_data = data["player"]
    player_fields = {"name", "hp", "max_hp", "attack", "attack_name", "x", "y", "inventory"}
    if not isinstance(player_data, dict) or set(player_data) != player_fields:
        raise ValueError("AI player must contain exactly the required player fields.")

    for field_name in ("name", "attack_name"):
        value = player_data[field_name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"AI player {field_name} must be a non-empty string.")
    for field_name in ("hp", "max_hp", "attack", "x", "y"):
        if type(player_data[field_name]) is not int:
            raise ValueError(f"AI player {field_name} must be an integer.")
    if player_data["max_hp"] <= 0 or not 0 <= player_data["hp"] <= player_data["max_hp"]:
        raise ValueError("AI player health must be between zero and a positive max_hp.")
    if player_data["attack"] < 0:
        raise ValueError("AI player attack cannot be negative.")

    inventory = player_data["inventory"]
    if not isinstance(inventory, list) or any(
        not isinstance(item, str) or not item.strip() for item in inventory
    ):
        raise ValueError("AI player inventory must be a list of non-empty strings.")

    player_x = player_data["x"]
    player_y = player_data["y"]
    if not (0 <= player_y < len(grid) and 0 <= player_x < cols):
        raise ValueError("AI player coordinates are outside the map.")
    if grid[player_y][player_x] is None:
        raise ValueError("AI player must start on a walkable map tile.")
    if (player_x, player_y) == (target_x, target_y):
        raise ValueError("AI goal target must be a different room from the starting room.")

    return GameState(
        world_map=GAME_MAP(grid),
        player=PlayerState(
            name=player_data["name"],
            hp=player_data["hp"],
            max_hp=player_data["max_hp"],
            attack=player_data["attack"],
            attack_name=player_data["attack_name"],
            x=player_x,
            y=player_y,
            inventory=inventory,
        ),
        goal=GameGoal(
            description=goal_description.strip(),
            target=(target_x, target_y),
        ),
        starting_position=(player_x, player_y),
        narrative=narrative,
    )


def log_ai_response(response_text, attempt, validation_result):
    """Append a raw AI response and its validation result to the debug log."""
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with AI_RESPONSE_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"\n{'=' * 80}\n"
            f"Timestamp: {timestamp}\n"
            f"Attempt: {attempt}\n"
            f"Validation: {validation_result}\n"
            "Raw response:\n"
            f"{response_text}\n"
        )


def create_initial_game_state():
    """Read the prompt, generate a starting state, and retry once if invalid."""
    prompt_path = Path(__file__).with_name("start_prompt.txt")
    prompt = prompt_path.read_text(encoding="utf-8")
    for attempt in range(1, 3):
        response_text = generate_response(prompt)
        try:
            state = parse_initial_game_state(response_text)
        except ValueError as error:
            log_ai_response(response_text, attempt, f"rejected: {error}")
            if attempt == 2:
                raise ValueError(
                    f"AI response failed validation twice: {error}. "
                    f"See {AI_RESPONSE_LOG} for both raw responses."
                ) from error
            prompt = (
                f"{prompt}\n\nYour previous response failed validation: {error}\n"
                "Generate a complete corrected JSON object. The map grid must be "
                "exactly 5 rows with exactly 5 cells in every row. Count the cells "
                "in each row before responding. Include a goal with a walkable target "
                "different from the player's starting room. Every walkable room must "
                "include name, desc, and purpose. Return only the corrected JSON."
            )
        else:
            log_ai_response(response_text, attempt, "accepted")
            return state
    raise RuntimeError("AI startup generation ended without a state.")


def apply_action(state, action):
    """Validate and apply one gameplay action, updating the authoritative state."""
    if action.kind == "move":
        directions = {
            "north": (0, -1),
            "south": (0, 1),
            "west": (-1, 0),
            "east": (1, 0),
        }
        direction = action.target.lower()
        if direction not in directions:
            state.status_message = "Unknown direction."
            return

        dx, dy = directions[direction]
        next_x = state.player.x + dx
        next_y = state.player.y + dy
        room = state.world_map.get_room_at(next_x, next_y)
        if room is None:
            state.status_message = "Blocked! Solid stone blocks that direction."
            return

        state.player.x = next_x
        state.player.y = next_y
        if (next_x, next_y) == state.goal.target:
            state.goal_completed = True
            state.status_message = f"Goal complete: {state.goal.description}"
        elif state.goal_completed:
            state.status_message = f"Goal complete: {state.goal.description}"
        else:
            state.status_message = f"Moved to {room['name']}."
    elif action.kind == "use_item":
        if action.target not in state.player.inventory:
            state.status_message = f"You don't have {action.target}."
            return
        state.status_message = f"You used the {action.target}."
    else:
        state.status_message = "Unknown action."


# =====================================================================
# 2. BASE & CHILD UI CLASSES
# =====================================================================
class BASE_UI:
    def __init__(self, x, y, width, height):
        self.local_rect = pygame.Rect(x, y, width, height)
        self.parent = None
        self.children = []

    def add_children(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def get_screen_rect(self):
        screen_x, screen_y = self.local_rect.x, self.local_rect.y
        curr = self.parent
        while curr is not None:
            screen_x += curr.local_rect.x
            screen_y += curr.local_rect.y
            curr = curr.parent
        return pygame.Rect(screen_x, screen_y, self.local_rect.width, self.local_rect.height)

    def draw(self, surface):
        for child in self.children:
            child.draw(surface)


class CHILD_UI(BASE_UI):
    def __init__(self, x, y, width, height, title="", bg_colour=COLOUR_PANEL_BG, border_colour=COLOUR_PANEL_BORDER):
        super().__init__(x, y, width, height)
        self.bg_colour = bg_colour
        self.border_colour = border_colour

        if title:
            self.add_children(UI_LABEL(TITLE_OFFSET_X, TITLE_OFFSET_Y, title, colour=COLOUR_TEXT_TITLE, is_title=True))

    def draw(self, surface):
        s_rect = self.get_screen_rect()
        pygame.draw.rect(surface, self.bg_colour, s_rect, border_radius=PANEL_CORNER_RADIUS)
        pygame.draw.rect(surface, self.border_colour, s_rect, PANEL_BORDER_WIDTH, border_radius=PANEL_CORNER_RADIUS)
        super().draw(surface)


class UI_LABEL(BASE_UI):
    def __init__(self, x, y, text, colour=COLOUR_TEXT_MAIN, is_title=False, wrap_width=None):
        super().__init__(x, y, 0, 0)
        self.text = text
        self.colour = colour
        self.used_font = FONT_TITLE if is_title else FONT_BASE
        self.wrap_width = wrap_width

    def get_wrapped_lines(self):
        if not self.text:
            return []
        if self.wrap_width is None:
            return self.text.split("\n")

        lines = []
        for paragraph in self.text.split("\n"):
            if not paragraph:
                lines.append("")
                continue
            current_line = ""
            for word in paragraph.split():
                candidate = f"{current_line} {word}".strip()
                if current_line and self.used_font.size(candidate)[0] > self.wrap_width:
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line = candidate
            lines.append(current_line)
        return lines

    def draw(self, surface):
        s_rect = self.get_screen_rect()
        for line_index, line in enumerate(self.get_wrapped_lines()):
            if line:
                text_surf = self.used_font.render(line, True, self.colour)
                surface.blit(text_surf, (s_rect.x, s_rect.y + line_index * self.used_font.get_linesize()))
        super().draw(surface)


class UI_MAP_DISPLAY(BASE_UI):
    """Visual 2D grid map component that lives inside GAME VIEW."""
    def __init__(self, x, y, size, game_state):
        super().__init__(x, y, size, size)
        self.game_state = game_state
        self.add_children(UI_LABEL(12, 8, "MAP", colour=COLOUR_TEXT_TITLE, is_title=True))

    def draw(self, surface):
        s_rect = self.get_screen_rect()

        # 1. Draw the Map container box (crimson border from wireframe)
        pygame.draw.rect(surface, COLOUR_MAP_BG, s_rect, border_radius=PANEL_CORNER_RADIUS)
        pygame.draw.rect(surface, COLOUR_MAP_BORDER, s_rect, PANEL_BORDER_WIDTH + 1, border_radius=PANEL_CORNER_RADIUS)

        # 2. Calculate tile size to fit the 2D array cleanly inside the box
        grid_top_offset = 34
        grid_area_w = s_rect.width - (MAP_INNER_PADDING * 2)
        grid_area_h = s_rect.height - grid_top_offset - MAP_INNER_PADDING

        game_map = self.game_state.world_map
        player = self.game_state.player
        tile_w = (grid_area_w - (MAP_TILE_GAP * (game_map.cols - 1))) // game_map.cols
        tile_h = (grid_area_h - (MAP_TILE_GAP * (game_map.rows - 1))) // game_map.rows
        tile_size = min(tile_w, tile_h)

        # Center the grid inside the map box
        total_grid_w = (tile_size * game_map.cols) + (MAP_TILE_GAP * (game_map.cols - 1))
        start_x = s_rect.x + (s_rect.width - total_grid_w) // 2
        start_y = s_rect.y + grid_top_offset

        # 3. Loop through the 2D array and draw each room tile
        for row_idx in range(game_map.rows):
            for col_idx in range(game_map.cols):
                room = game_map.get_room_at(col_idx, row_idx)
                tile_x = start_x + col_idx * (tile_size + MAP_TILE_GAP)
                tile_y = start_y + row_idx * (tile_size + MAP_TILE_GAP)
                tile_rect = pygame.Rect(tile_x, tile_y, tile_size, tile_size)

                if col_idx == player.x and row_idx == player.y:
                    colour = COLOUR_TILE_PLAYER  # Highlight player's current room
                elif (col_idx, row_idx) == self.game_state.goal.target:
                    colour = COLOUR_TILE_GOAL
                elif room is not None:
                    colour = COLOUR_TILE_ROOM    # Valid room in 2D array
                else:
                    colour = COLOUR_TILE_EMPTY   # Wall / Empty space (None)

                pygame.draw.rect(surface, colour, tile_rect, border_radius=3)

        super().draw(surface)


class UI_ACTION_BUTTON(BASE_UI):
    """Clickable action/command boxes inside the bottom of GAME VIEW."""
    def __init__(self, x, y, width, height, label_text, action_id):
        super().__init__(x, y, width, height)
        self.action_id = action_id
        self.add_children(UI_LABEL(16, 12, label_text, colour=COLOUR_TEXT_MAIN))

    def draw(self, surface):
        s_rect = self.get_screen_rect()
        mouse_hovered = s_rect.collidepoint(pygame.mouse.get_pos())
        bg = COLOUR_BTN_HOVER if mouse_hovered else COLOUR_BTN_BG

        pygame.draw.rect(surface, bg, s_rect, border_radius=4)
        pygame.draw.rect(surface, COLOUR_BTN_BORDER, s_rect, 2, border_radius=4)
        super().draw(surface)


class UI_ITEM_SLOT(BASE_UI):
    def __init__(self, x, y, width, height, item_name, icon_colour):
        super().__init__(x, y, width, height)
        self.item_name = item_name
        self.icon_colour = icon_colour
        self.add_children(UI_LABEL(SLOT_TEXT_OFFSET_X, SLOT_TEXT_OFFSET_Y, item_name))

    def draw(self, surface):
        s_rect = self.get_screen_rect()
        pygame.draw.rect(surface, COLOUR_SLOT_BG, s_rect, border_radius=SLOT_CORNER_RADIUS)
        pygame.draw.rect(surface, COLOUR_SLOT_BORDER, s_rect, SLOT_BORDER_WIDTH, border_radius=SLOT_CORNER_RADIUS)

        icon_rect = pygame.Rect(
            s_rect.x + SLOT_ICON_PADDING,
            s_rect.y + SLOT_ICON_PADDING,
            SLOT_ICON_SIZE,
            SLOT_ICON_SIZE
        )
        pygame.draw.rect(surface, self.icon_colour, icon_rect, border_radius=SLOT_CORNER_RADIUS)
        super().draw(surface)


# =====================================================================
# 3. CREATE THE 2D ROOM ARRAY & MAP OBJECT
# =====================================================================
# None = Solid wall/unreachable tile. Dict = Walkable Room in the 2D grid.
WORLD_GRID_2D = [
    [
        None,
        {"name": "Watchtower", "desc": "Cold wind howls through the broken stone battlements.", "purpose": "Its height offers a view toward the citadel's inner halls."},
        {"name": "Armoury",    "desc": "Racks of rusted halberds line the damp walls.", "purpose": "A passage here leads toward the citadel's central chamber."},
        None
    ],
    [
        {"name": "Citadel Gate", "desc": "You stand before the iron gates of the Sunken Citadel.", "purpose": "The open gate is your route into the citadel."},
        {"name": "Courtyard",    "desc": "Cracked flagstones surround a dry, mossy fountain.", "purpose": "Several paths converge here on the way to the inner chamber."},
        {"name": "Great Hall",   "desc": "Long banquet tables rot beneath tattered banners.", "purpose": "The hall's far arch leads deeper into the citadel."},
        {"name": "Sanctum",      "desc": "A crimson brazier illuminates an ancient serpent altar.", "purpose": "This inner sanctum is the destination you seek."}
    ],
    [
        None,
        {"name": "Damp Cellar",  "desc": "Water drips steadily onto mossy cobblestones.", "purpose": "A narrow stair offers another route toward the inner chamber."},
        {"name": "Crypt",        "desc": "Stone sarcophagi rest in eerie silence.", "purpose": "A stone passage continues toward the sanctum."},
        None
    ]
]

# The game state is the single source of truth for gameplay data.
game_state = GameState(
    world_map=GAME_MAP(WORLD_GRID_2D),
    player=PlayerState(
        name="Player",
        hp=85,
        max_hp=100,
        attack=14,
        attack_name="Sword",
        x=0,
        y=1,
        inventory=["Iron Sword", "Crimson Potion", "Serpent Key"],
    ),
    goal=GameGoal(
        description="Reach the Sanctum.",
        target=(3, 1),
    ),
    starting_position=(0, 1),
)


# =====================================================================
# 4. SET UP YOUR 3 SCREEN COMPONENTS (MATCHING WIREFRAME)
# =====================================================================

# --- COMPONENT 1: STATS PANEL (Left 25% Width, Full Height) ---
stats_panel = CHILD_UI(STATS_PANEL_X, STATS_PANEL_Y, STATS_PANEL_W, STATS_PANEL_H, title="STATS")
hp_label    = stats_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y, "", colour=COLOUR_TEXT_HP))
atk_label   = stats_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y + TEXT_LINE_SPACING, ""))
loc_label   = stats_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y + (TEXT_LINE_SPACING * 2), "", colour=COLOUR_TEXT_ACCENT))
coord_label = stats_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y + (TEXT_LINE_SPACING * 3), ""))
goal_label = stats_panel.add_children(
    UI_LABEL(
        PANEL_PADDING,
        CONTENT_START_Y + (TEXT_LINE_SPACING * 4),
        "",
        colour=COLOUR_TEXT_TITLE,
        wrap_width=STATS_PANEL_W - (PANEL_PADDING * 2),
    )
)


# --- COMPONENT 2: GAME VIEW (Top-Right 75% Width, 75% Height) ---
game_view_panel = CHILD_UI(GAME_VIEW_X, GAME_VIEW_Y, GAME_VIEW_W, GAME_VIEW_H, title="GAME VIEW")

# Story text lines (Representing the red squiggly text lines in your wireframe)
story_text_width = MAP_LOCAL_X - (PANEL_PADDING * 2)
story_line_1 = game_view_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y, "", colour=COLOUR_TEXT_TITLE))
story_narrative = game_view_panel.add_children(
    UI_LABEL(
        PANEL_PADDING,
        CONTENT_START_Y + TEXT_LINE_SPACING,
        "",
        wrap_width=story_text_width,
    )
)
story_line_2 = game_view_panel.add_children(
    UI_LABEL(PANEL_PADDING, CONTENT_START_Y + TEXT_LINE_SPACING, "", wrap_width=story_text_width)
)
story_line_3 = game_view_panel.add_children(
    UI_LABEL(PANEL_PADDING, CONTENT_START_Y + TEXT_LINE_SPACING, "", wrap_width=story_text_width)
)
story_line_4 = game_view_panel.add_children(
    UI_LABEL(
        PANEL_PADDING,
        CONTENT_START_Y + TEXT_LINE_SPACING,
        "",
        wrap_width=story_text_width,
    )
)

# Child MAP Display (Top-Right inside GAME VIEW)
map_display = game_view_panel.add_children(UI_MAP_DISPLAY(MAP_LOCAL_X, MAP_LOCAL_Y, MAP_BOX_SIZE, game_state))

# Child Action Boxes (The black boxes along the bottom of GAME VIEW)
btn_step = ACTION_BTN_W + ACTION_BTN_GAP
btn_north = game_view_panel.add_children(UI_ACTION_BUTTON(PANEL_PADDING, ACTION_BTN_LOCAL_Y, ACTION_BTN_W, ACTION_BTN_H, "Go North", "north"))
btn_south = game_view_panel.add_children(UI_ACTION_BUTTON(PANEL_PADDING + btn_step, ACTION_BTN_LOCAL_Y, ACTION_BTN_W, ACTION_BTN_H, "Go South", "south"))
btn_west  = game_view_panel.add_children(UI_ACTION_BUTTON(PANEL_PADDING + (btn_step * 2), ACTION_BTN_LOCAL_Y, ACTION_BTN_W, ACTION_BTN_H, "Go West", "west"))
btn_east  = game_view_panel.add_children(UI_ACTION_BUTTON(PANEL_PADDING + (btn_step * 3), ACTION_BTN_LOCAL_Y, ACTION_BTN_W, ACTION_BTN_H, "Go East", "east"))
action_buttons = [btn_north, btn_south, btn_west, btn_east]


# --- COMPONENT 3: INV / ACTIONS PANEL (Bottom-Right 75% Width, 25% Height) ---
inventory_panel = CHILD_UI(INV_PANEL_X, INV_PANEL_Y, INV_PANEL_W, INV_PANEL_H, title="INV / ACTIONS", border_colour=COLOUR_INV_BORDER)

slot_x_step = SLOT_WIDTH + SLOT_SPACING
item_icon_colours = {
    "Iron Sword": COLOUR_ICON_SWORD,
    "Crimson Potion": COLOUR_ICON_POTION,
    "Serpent Key": COLOUR_ICON_KEY,
}
item_slots = []

root_panels = [stats_panel, game_view_panel, inventory_panel]


# =====================================================================
# 5. RENDER GAME STATE IN THE UI
# =====================================================================
def update_inventory_ui(state):
    if [slot.item_name for slot in item_slots] == state.player.inventory:
        return

    for slot in item_slots:
        inventory_panel.children.remove(slot)
    item_slots.clear()

    for index, item_name in enumerate(state.player.inventory):
        item_slot = inventory_panel.add_children(
            UI_ITEM_SLOT(
                PANEL_PADDING + (slot_x_step * index),
                CONTENT_START_Y,
                SLOT_WIDTH,
                SLOT_HEIGHT,
                item_name,
                item_icon_colours.get(item_name, COLOUR_SLOT_BORDER),
            )
        )
        item_slots.append(item_slot)


def update_game_ui(state):
    update_inventory_ui(state)
    player = state.player
    room = state.world_map.get_room_at(player.x, player.y)
    hp_label.text = f"HP: {player.hp} / {player.max_hp}"
    atk_label.text = f"ATK: {player.attack} ({player.attack_name})"
    loc_label.text = f"LOC: {room['name']}"
    coord_label.text = f"POS: ({player.x}, {player.y})"
    goal_prefix = "GOAL COMPLETE: " if state.goal_completed else "GOAL: "
    goal_label.text = goal_prefix + state.goal.description
    story_line_1.text = f"=== {room['name'].upper()} ==="
    is_starting_tile = (player.x, player.y) == state.starting_position
    story_narrative.text = state.narrative if is_starting_tile else ""
    narrative_y = CONTENT_START_Y + TEXT_LINE_SPACING
    narrative_line_count = len(story_narrative.get_wrapped_lines())
    description_y = narrative_y
    if narrative_line_count:
        description_y += narrative_line_count * FONT_BASE.get_linesize() + 8
    story_line_2.text = room["desc"]
    story_line_2.local_rect.y = description_y
    description_line_count = len(story_line_2.get_wrapped_lines())
    purpose_y = description_y + description_line_count * FONT_BASE.get_linesize() + 8
    story_line_3.text = room["purpose"]
    story_line_3.local_rect.y = purpose_y
    purpose_line_count = len(story_line_3.get_wrapped_lines())
    story_line_4.text = state.status_message
    story_line_4.local_rect.y = (
        purpose_y + purpose_line_count * FONT_BASE.get_linesize() + 8
    )


update_game_ui(game_state)


# =====================================================================
# 6. MAIN LOOP
# =====================================================================
def main():
    global game_state
    game_state = create_initial_game_state()
    map_display.game_state = game_state
    update_game_ui(game_state)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Move around the 2D Map using WASD or Arrow Keys
            elif event.type == pygame.KEYDOWN:
                key_dirs = {
                    pygame.K_w: "north", pygame.K_UP: "north",
                    pygame.K_s: "south", pygame.K_DOWN: "south",
                    pygame.K_a: "west",  pygame.K_LEFT: "west",
                    pygame.K_d: "east",  pygame.K_RIGHT: "east"
                }
                if event.key in key_dirs:
                    apply_action(game_state, GameAction("move", key_dirs[event.key]))
                    update_game_ui(game_state)

            # Mouse Clicks on Action Buttons or Inventory Slots
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in action_buttons:
                    if btn.get_screen_rect().collidepoint(event.pos):
                        apply_action(game_state, GameAction("move", btn.action_id))
                        update_game_ui(game_state)

                for slot in item_slots:
                    if slot.get_screen_rect().collidepoint(event.pos):
                        apply_action(game_state, GameAction("use_item", slot.item_name))
                        update_game_ui(game_state)

        SCREEN.fill(COLOUR_SCREEN_BG)

        for panel in root_panels:
            panel.draw(SCREEN)

        pygame.display.flip()
        CLOCK.tick(FPS)

    pygame.quit()
    sys.exit()

"""
@dataclass
class Decision:
    decision_name=""
    type=None#??? MOVE, ACT, USE
    item_used=None #ITEM
"""




if __name__ == "__main__":
    main()
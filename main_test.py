import pygame
import sys
from dataclasses import dataclass

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
    """Stores a 2D grid of rooms and handles player movement across coordinates."""
    def __init__(self, grid_2d, start_x=0, start_y=0):
        self.grid = grid_2d
        self.rows = len(grid_2d)
        self.cols = len(grid_2d[0]) if self.rows > 0 else 0
        self.player_x = start_x
        self.player_y = start_y

    def get_room_at(self, x, y):
        """Returns the room dict at (x, y), or None if out of bounds or a wall."""
        if 0 <= y < self.rows and 0 <= x < self.cols:
            return self.grid[y][x]
        return None

    def get_current_room(self):
        """Returns the room dictionary where the player is currently standing."""
        return self.get_room_at(self.player_x, self.player_y)

    def can_move(self, dx, dy):
        """Checks if (player_x + dx, player_y + dy) is a valid room in the 2D array."""
        return self.get_room_at(self.player_x + dx, self.player_y + dy) is not None

    def move(self, dx, dy):
        """Moves the player by (dx, dy) if valid. Returns (success_bool, message)."""
        if self.can_move(dx, dy):
            self.player_x += dx
            self.player_y += dy
            room = self.get_current_room()
            return True, f"Moved to {room['name']}."
        return False, "Blocked! Solid stone blocks that direction."

    def move_direction(self, direction_name):
        """Helper to move using 'north', 'south', 'east', or 'west'."""
        dirs = {
            "north": (0, -1),
            "south": (0, 1),
            "west":  (-1, 0),
            "east":  (1, 0)
        }
        dx, dy = dirs.get(direction_name.lower(), (0, 0))
        return self.move(dx, dy)


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
    def __init__(self, x, y, text, colour=COLOUR_TEXT_MAIN, is_title=False):
        super().__init__(x, y, 0, 0)
        self.text = text
        self.colour = colour
        self.used_font = FONT_TITLE if is_title else FONT_BASE

    def draw(self, surface):
        s_rect = self.get_screen_rect()
        text_surf = self.used_font.render(self.text, True, self.colour)
        surface.blit(text_surf, (s_rect.x, s_rect.y))
        super().draw(surface)


class UI_MAP_DISPLAY(BASE_UI):
    """Visual 2D grid map component that lives inside GAME VIEW."""
    def __init__(self, x, y, size, game_map):
        super().__init__(x, y, size, size)
        self.game_map = game_map
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

        tile_w = (grid_area_w - (MAP_TILE_GAP * (self.game_map.cols - 1))) // self.game_map.cols
        tile_h = (grid_area_h - (MAP_TILE_GAP * (self.game_map.rows - 1))) // self.game_map.rows
        tile_size = min(tile_w, tile_h)

        # Center the grid inside the map box
        total_grid_w = (tile_size * self.game_map.cols) + (MAP_TILE_GAP * (self.game_map.cols - 1))
        start_x = s_rect.x + (s_rect.width - total_grid_w) // 2
        start_y = s_rect.y + grid_top_offset

        # 3. Loop through the 2D array and draw each room tile
        for row_idx in range(self.game_map.rows):
            for col_idx in range(self.game_map.cols):
                room = self.game_map.get_room_at(col_idx, row_idx)
                tile_x = start_x + col_idx * (tile_size + MAP_TILE_GAP)
                tile_y = start_y + row_idx * (tile_size + MAP_TILE_GAP)
                tile_rect = pygame.Rect(tile_x, tile_y, tile_size, tile_size)

                if col_idx == self.game_map.player_x and row_idx == self.game_map.player_y:
                    colour = COLOUR_TILE_PLAYER  # Highlight player's current room
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
        {"name": "Watchtower", "desc": "Cold wind howls through the broken stone battlements."},
        {"name": "Armoury",    "desc": "Racks of rusted halberds line the damp walls."},
        None
    ],
    [
        {"name": "Citadel Gate", "desc": "You stand before the iron gates of the Sunken Citadel."},
        {"name": "Courtyard",    "desc": "Cracked flagstones surround a dry, mossy fountain."},
        {"name": "Great Hall",   "desc": "Long banquet tables rot beneath tattered banners."},
        {"name": "Sanctum",      "desc": "A crimson brazier illuminates an ancient serpent altar."}
    ],
    [
        None,
        {"name": "Damp Cellar",  "desc": "Water drips steadily onto mossy cobblestones."},
        {"name": "Crypt",        "desc": "Stone sarcophagi rest in eerie silence."},
        None
    ]
]

# Start player at (x=0, y=1) -> "Citadel Gate"
world_map = GAME_MAP(WORLD_GRID_2D, start_x=0, start_y=1)


# =====================================================================
# 4. SET UP YOUR 3 SCREEN COMPONENTS (MATCHING WIREFRAME)
# =====================================================================

# --- COMPONENT 1: STATS PANEL (Left 25% Width, Full Height) ---
stats_panel = CHILD_UI(STATS_PANEL_X, STATS_PANEL_Y, STATS_PANEL_W, STATS_PANEL_H, title="STATS")
hp_label    = stats_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y, "HP:  85 / 100", colour=COLOUR_TEXT_HP))
atk_label   = stats_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y + TEXT_LINE_SPACING, "ATK: 14 (Sword)"))
loc_label   = stats_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y + (TEXT_LINE_SPACING * 2), "", colour=COLOUR_TEXT_ACCENT))
coord_label = stats_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y + (TEXT_LINE_SPACING * 3), ""))


# --- COMPONENT 2: GAME VIEW (Top-Right 75% Width, 75% Height) ---
game_view_panel = CHILD_UI(GAME_VIEW_X, GAME_VIEW_Y, GAME_VIEW_W, GAME_VIEW_H, title="GAME VIEW")

# Story text lines (Representing the red squiggly text lines in your wireframe)
story_line_1 = game_view_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y, "", colour=COLOUR_TEXT_TITLE))
story_line_2 = game_view_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y + TEXT_LINE_SPACING, ""))
story_line_3 = game_view_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y + (TEXT_LINE_SPACING * 2), ""))
story_line_4 = game_view_panel.add_children(UI_LABEL(PANEL_PADDING, CONTENT_START_Y + (TEXT_LINE_SPACING * 3), "Use WASD / Arrows or click actions below to move.", colour=COLOUR_TEXT_ACCENT))

# Child MAP Display (Top-Right inside GAME VIEW)
map_display = game_view_panel.add_children(UI_MAP_DISPLAY(MAP_LOCAL_X, MAP_LOCAL_Y, MAP_BOX_SIZE, world_map))

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
slot1 = inventory_panel.add_children(UI_ITEM_SLOT(PANEL_PADDING, CONTENT_START_Y, SLOT_WIDTH, SLOT_HEIGHT, "Iron Sword", COLOUR_ICON_SWORD))
slot2 = inventory_panel.add_children(UI_ITEM_SLOT(PANEL_PADDING + slot_x_step, CONTENT_START_Y, SLOT_WIDTH, SLOT_HEIGHT, "Crimson Potion", COLOUR_ICON_POTION))
slot3 = inventory_panel.add_children(UI_ITEM_SLOT(PANEL_PADDING + (slot_x_step * 2), CONTENT_START_Y, SLOT_WIDTH, SLOT_HEIGHT, "Serpent Key", COLOUR_ICON_KEY))

root_panels = [stats_panel, game_view_panel, inventory_panel]


# =====================================================================
# 5. HELPER TO REFRESH UI TEXT WHEN MOVING ROOMS
# =====================================================================
def update_room_ui(status_msg="You survey your surroundings."):
    room = world_map.get_current_room()
    loc_label.text = f"LOC: {room['name']}"
    coord_label.text = f"POS: ({world_map.player_x}, {world_map.player_y})"
    story_line_1.text = f"=== {room['name'].upper()} ==="
    story_line_2.text = room["desc"]
    story_line_3.text = status_msg

update_room_ui()


# =====================================================================
# 6. MAIN LOOP
# =====================================================================
def main():
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
                    _, msg = world_map.move_direction(key_dirs[event.key])
                    update_room_ui(msg)

            # Mouse Clicks on Action Buttons or Inventory Slots
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in action_buttons:
                    if btn.get_screen_rect().collidepoint(event.pos):
                        _, msg = world_map.move_direction(btn.action_id)
                        update_room_ui(msg)

                for slot in [slot1, slot2, slot3]:
                    if slot.get_screen_rect().collidepoint(event.pos):
                        hp_label.text = f"Used: {slot.item_name}!"
                        story_line_3.text = f"You used the {slot.item_name}."

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
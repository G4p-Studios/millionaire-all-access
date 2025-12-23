# settings.py

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
# 1. Renamed Game
SCREEN_TITLE = "All Access Millionaire"

# --- Color Palettes ---
# Standard (Blue Theme)
STD_BG = (0, 0, 200)       
STD_TEXT = (255, 255, 255) 
STD_HL = (255, 255, 0)     

# High Contrast (Black/White/Green)
HC_BG = (0, 0, 0)          
HC_TEXT = (255, 255, 255)  
HC_HL = (0, 255, 0)        

# --- Font Sizes (Base) ---
BASE_FONT_TITLE = 80
BASE_FONT_MAIN = 48
BASE_FONT_SMALL = 36
BASE_FONT_HUGE = 100 

# Frame rate
FPS = 60

# Network Settings
SERVER_PORT = 50550

# Lobby Spy Service URL
LOBBY_SPY_URL = "http://lobbies.seedy.cc:1945/lobbies"

# 2. Money Trees (GBP and USD)
MONEY_TREE_GBP = [
    "£100", "£200", "£300", "£500", "£1,000",
    "£2,000", "£4,000", "£8,000", "£16,000", "£32,000",
    "£64,000", "£125,000", "£250,000", "£500,000", "£1 Million"
]

MONEY_TREE_USD = [
    "$100", "$200", "$300", "$500", "$1,000",
    "$2,000", "$4,000", "$8,000", "$16,000", "$32,000",
    "$64,000", "$125,000", "$250,000", "$500,000", "$1 Million"
]
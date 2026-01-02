# settings.py

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SCREEN_TITLE = "All Access Millionaire"

# --- Color Palettes ---
STD_BG = (0, 0, 200)       
STD_TEXT = (255, 255, 255) 
STD_HL = (255, 255, 0)     

HC_BG = (0, 0, 0)          
HC_TEXT = (255, 255, 255)  
HC_HL = (0, 255, 0)        

# --- Font Sizes ---
BASE_FONT_TITLE = 80
BASE_FONT_MAIN = 48
BASE_FONT_SMALL = 36
BASE_FONT_HUGE = 100 

FPS = 60
SERVER_PORT = 50550
LOBBY_SPY_URL = "http://lobbies.seedy.cc:1945/lobbies"

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

# --- SOUND CONFIGURATION ---
SOUND_FILES = {
    # --- Background Music ---
    "theme": "theme.mp3",
    "q1_5": "q1_5.mp3",
    "q6_10": "q6_10.mp3",
    "q11_14": "q11_14.mp3",
    "q15": "q15.mp3",
    "final_answer": "final_answer.mp3",
    "walk_away": "walk_away.mp3",
    "lifeline": "lifeline.wav",

    # --- WIN STINGS ---
    "win_0": "027 $100-$500 Yes.flac",             # $100
    "win_1": "027 $100-$500 Yes.flac",             # $200
    "win_2": "027 $100-$500 Yes.flac",             # $300
    "win_3": "027 $100-$500 Yes.flac",             # $500
    "win_4": "$1000 Win & $2000 Lights Down.flac", # $1,000 (Milestone)
    "win_5": "058 $2000 Win.flac",                 # $2,000
    "win_6": "063 $4000 Win.flac",                 # $4,000
    "win_7": "068 $8000 Win.flac",                 # $8,000
    "win_8": "073 $16000 Win.flac",                # $16,000 (UPDATED)
    "win_9": "078 $32000 Win.flac",                # $32,000 (Milestone)
    "win_10": "082 $64000 Win.flac",               # $64,000
    "win_11": "085 $125000 Win.flac",              # $125,000
    "win_12": "088 $250000 Win.flac",              # $250,000
    "win_13": "091 $500000 Win.flac",              # $500,000
    "win_14": "094 $1000000 Win.flac",             # $1 Million

    # --- LOSE STINGS ---
    "lose_0": "028 $100-$1000 No.flac",
    "lose_1": "028 $100-$1000 No.flac",
    "lose_2": "028 $100-$1000 No.flac",
    "lose_3": "028 $100-$1000 No.flac",
    "lose_4": "028 $100-$1000 No.flac",
    "lose_5": "057 $2000 Lose.flac",
    "lose_6": "062 $4000 Lose.flac",
    "lose_7": "067 $8000 Lose.flac",
    "lose_8": "072 $16000 Lose.flac",
    "lose_9": "077 $32000 Lose.flac",
    "lose_10": "081 $64000 Lose.flac",
    "lose_11": "084 $125000 Lose.flac",
    "lose_12": "087 $250000 Lose.flac",
    "lose_13": "090 $500000 Lose.flac",
    "lose_14": "093 $1000000 Lose.flac",
}
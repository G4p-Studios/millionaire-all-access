# settings.py

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SCREEN_TITLE = "All Access Millionaire"

# --- Color Palettes ---
STD_BG = (0, 0, 200)       
STD_TEXT = (255, 255, 255) 
STD_HL = (255, 255, 0)     
STD_SEL = (255, 165, 0)    

HC_BG = (0, 0, 0)          
HC_TEXT = (255, 255, 255)  
HC_HL = (0, 255, 0)        
HC_SEL = (255, 255, 0)     

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
    # --- Background Music (Question Beds) ---
    "q_bed_1_5": "026 $100-$1000 Questions.flac",
    "q_bed_6": "055 $2000 Question.flac",
    "q_bed_7": "060 $4000 Question.flac",
    "q_bed_8": "065 $8000 Question.flac",
    "q_bed_9": "070 $16000 Question.flac",
    "q_bed_10": "075 $32000 Question.flac",
    "q_bed_11": "080 $64000 Question.flac",
    "q_bed_12": "083 $125000 Question.flac",
    "q_bed_13": "086 $250000 Question.flac",
    "q_bed_14": "089 $500000 Question.flac",
    "q_bed_15": "092 $1000000 Question.flac",

    # --- Other Sounds ---
    "theme": "theme.mp3",
    "walk_away": "walk_away.mp3",
    "lifeline": "lifeline.wav",

    # --- FINAL ANSWER SOUNDS ---
    "final_answer": "final_answer.mp3", 
    "final_answer_5": "056 $2000 Final Answer.flac",
    "final_answer_6": "061 $4000 Final Answer.flac",
    "final_answer_7": "066 $8000 Final Answer.flac",
    "final_answer_8": "071 $16000 Final Answer.flac",
    "final_answer_9": "076 $32000 Final Answer.flac",

    # --- WIN STINGS ---
    "win_0": "027 $100-$500 Yes.flac",             
    "win_1": "027 $100-$500 Yes.flac",             
    "win_2": "027 $100-$500 Yes.flac",             
    "win_3": "027 $100-$500 Yes.flac",             
    "win_4": "$1000 Win & $2000 Lights Down.flac", 
    "win_5": "058 $2000 Win.flac",                 
    "win_6": "063 $4000 Win.flac",                 
    "win_7": "068 $8000 Win.flac",                 
    "win_8": "073 $16000 Win.flac",                
    "win_9": "078 $32000 Win.flac",                
    "win_10": "082 $64000 Win.flac",               
    "win_11": "085 $125000 Win.flac",              
    "win_12": "088 $250000 Win.flac",              
    "win_13": "091 $500000 Win.flac",              
    "win_14": "094 $1000000 Win.flac",             

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
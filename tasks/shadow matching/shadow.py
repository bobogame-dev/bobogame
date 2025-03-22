import pygame
import sys
import random
import cv2
import mediapipe as mp
import math
import time
from datetime import datetime
import os
import json

# Print the current working directory
print("Current Working Directory:", os.getcwd())

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize the mixer module
pygame.display.set_caption("Jungle Shadow Matcher")
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

# Load background image with error handling
try:
    background = pygame.image.load("assets/background2.jpg")  # Create jungle background
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
except FileNotFoundError:
    print("Background image not found. Using a default color instead.")
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background.fill((0, 0, 0))  # Fallback to a black background

# Create a background surface with animals and shadows pre-rendered
def create_game_background(animals, shadows):
    bg_surface = background.copy()
    
    # Draw shadows on the background
    for shadow in shadows:
        if not shadow.matched:
            bg_surface.blit(shadow.shadow, shadow.rect.topleft)
    
    # Draw animals on the background
    for animal in animals:
        if not animal.matched:
            bg_surface.blit(animal.image, animal.rect.topleft)
    
    return bg_surface

# Sound effects
try:
    correct_sound = pygame.mixer.Sound("assets/catch_sound.ogg")
except FileNotFoundError:
    print("Sound file not found. Please add sound file to the 'assets' folder.")
    correct_sound = None

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_hands=1  # Track only one hand for simplicity
)
mp_drawing = mp.solutions.drawing_utils

# Initialize webcam
cap = cv2.VideoCapture(0)

# Colors
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Font
font_large = pygame.font.Font(None, 74)
font_medium = pygame.font.Font(None, 50)
font_small = pygame.font.Font(None, 36)
font_title = pygame.font.Font(None, 100)  # Larger font for game over screen

# Animal class
class Animal:
    def __init__(self, name, position):
        self.name = name
        self.position = position
        self.width = 150
        self.height = 150
        self.matched = False
        
        # Load animal image
        self.image = pygame.image.load(f"assets/{name}.png")
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        
        # Load animal shadow
        self.shadow = pygame.image.load(f"assets/{name}_shadow.png")
        self.shadow = pygame.transform.scale(self.shadow, (self.width, self.height))
        
        # Create a rectangle for collision detection
        self.rect = pygame.Rect(position[0], position[1], self.width, self.height)
        
        # Animation variables
        self.is_selected = False
        self.scale_factor = 1.0
        self.scaling_up = True
        self.original_size = (self.width, self.height)

    def draw(self, surface):
        # Draw the animal image normally
        surface.blit(self.image, self.rect.topleft)

        # If the animal is matched, draw a green outline
        if self.matched:
            outline_rect = pygame.Rect(self.rect.x - 5, self.rect.y - 5, self.rect.width + 10, self.rect.height + 10)
            pygame.draw.rect(surface, (0, 255, 0), outline_rect, 3, border_radius=15)

    def draw_shadow(self, surface):
        if self.matched:
            # Instead of the shadow, display the original image
            surface.blit(self.image, self.rect.topleft)
        else:
            # Draw the normal shadow
            surface.blit(self.shadow, self.rect.topleft)

        # Always draw a green outline if the animal is matched
        if self.matched:
            outline_rect = pygame.Rect(self.rect.x - 5, self.rect.y - 5, self.rect.width + 10, self.rect.height + 10)
            pygame.draw.rect(surface, (0, 255, 0), outline_rect, 3, border_radius=15)

# HandCursor class
class HandCursor:
    def __init__(self):
        self.image = pygame.image.load("assets/hand.png")
        self.image = pygame.transform.scale(self.image, (100, 100))
        self.rect = self.image.get_rect()
        self.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.is_grabbing = False
        self.selected_animal = None  # Track the currently selected animal
        self.previous_y = None
        self.previous_x = None
        self.is_moving = False
        self.hand_stopped_moving = False
        self.movement_threshold = 0.01  # Adjust this value for sensitivity
        self.stop_moving_timer = 0
        self.stop_moving_duration = 0.5  # Half a second threshold to consider the hand as "stopped moving"
        self.is_grab_confirmed = False
        self.grab_timer = 0
        self.grab_threshold = 1.0  # Seconds to hold grab to confirm selection
        self.confirm_timer = 0  # Timer to confirm match
        self.confirm_threshold = 1.0  # Seconds to hold over the matching shadow to confirm

    def update(self, pos, is_grabbing, current_y):
        # Calculate movement
        if self.previous_x is not None and self.previous_y is not None:
            x_change = abs(pos[0] - self.previous_x)
            y_change = abs(current_y - self.previous_y)
            
            # If movement is detected above the threshold, reset stop timer
            if x_change > self.movement_threshold or y_change > self.movement_threshold:
                self.is_moving = True
                self.stop_moving_timer = time.time()
            else:
                # If the hand hasn't moved for the duration, mark as stopped
                if time.time() - self.stop_moving_timer > self.stop_moving_duration:
                    self.is_moving = False
                    self.hand_stopped_moving = True
                else:
                    self.hand_stopped_moving = False

        # Update position
        self.position = pos
        self.rect.center = pos
        self.previous_x = pos[0]
        self.previous_y = current_y
        
        # Handle grabbing state
        if is_grabbing:
            if not self.is_grabbing:  # Just started grabbing
                self.is_grabbing = True
                self.grab_timer = time.time()
                self.is_grab_confirmed = False  # Reset confirmation when starting a new grab
            else:  # Continuing to grab
                if time.time() - self.grab_timer >= self.grab_threshold and not self.is_grab_confirmed:
                    self.is_grab_confirmed = True  # Only set to True once
        else:  # Not grabbing
            if self.is_grabbing:  # Just released grab
                self.is_grabbing = False
                # Only reset confirmation if not in the middle of matching
                if self.selected_animal is None:
                    self.is_grab_confirmed = False
                self.grab_timer = 0
            # If no animal is selected, make sure grab confirmed is always false when not grabbing
            if self.selected_animal is None:
                self.is_grab_confirmed = False

    def draw(self, surface):
        # Draw hand cursor
        if self.is_grabbing:
            # Change cursor to grabbing image or animation
            grab_progress = min(1.0, (time.time() - self.grab_timer) / self.grab_threshold)
            # Draw a progress circle around cursor
            radius = 55
            angle = 360 * grab_progress
            pygame.draw.arc(surface, (0, 255, 0), 
                           (self.position[0] - radius, self.position[1] - radius, 
                            radius * 2, radius * 2), 
                           0, math.radians(angle), 5)
        
        surface.blit(self.image, (self.position[0] - 50, self.position[1] - 50))

# Function to detect if hand is in a closed fist position (grabbing)
def is_grabbing(hand_landmarks):
    # Get fingertip y-coordinates (except thumb)
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y
    ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y
    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y
    
    # Get finger base and pip (middle joint) y-coordinates for comparison
    index_pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
    middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
    ring_pip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP].y
    pinky_pip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP].y
    
    # Determine if fingertips are below their respective pip joints (folded fingers)
    index_folded = index_tip > index_pip
    middle_folded = middle_tip > middle_pip
    ring_folded = ring_tip > ring_pip
    pinky_folded = pinky_tip > pinky_pip
    
    # If all fingers are folded, it's a closed fist
    return index_folded and middle_folded and ring_folded and pinky_folded

# Add a global variable to track if the session has ended
session_ended = False

# Function to save player level and score to JSON file
def save_player_data(score, is_game_end=False):
    global current_level, cognitive_tasks, session_ended
    try:
        with open("player_data.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}  # If the file doesn't exist, create a new dictionary

    # Save the current level the player was playing
    data["cognitive-level"] = current_level

    # Increment cognitive tasks only when the game ends naturally and the session hasn't already been counted
    if is_game_end and not session_ended:
        data["cognitive-tasks"] += 1
        session_ended = True  # Mark the session as ended to prevent multiple increments

    # Save the updated data
    with open("player_data.json", "w") as file:
        json.dump(data, file, indent=4)

    # Update global variables
    current_level = data["cognitive-level"]
    cognitive_tasks = data["cognitive-tasks"]

    print(f"Cognitive Level: {current_level}, Cognitive Tasks: {cognitive_tasks}")

# Function to load player level from JSON file
def load_player_data():
    try:
        with open("player_data.json", "r") as file:
            data = json.load(file)
            # Load cognitive level and tasks (default to 2 and 0 if not found)
            cognitive_level = data.get("cognitive-level", 2)
            cognitive_tasks = data.get("cognitive-tasks", 0)
            return cognitive_level, cognitive_tasks
    except FileNotFoundError:
        # If the file doesn't exist, create it with default values
        data = {"cognitive-level": 2, "cognitive-tasks": 0}
        with open("player_data.json", "w") as file:
            json.dump(data, file)
        return 2, 0  # Return the default values

# Function to update game parameters based on the current level
def update_game_parameters():
    global matches_needed, game_duration, current_level
    if current_level == 1:  # Easy Level
        matches_needed = 2  # Only 2 matches required
        game_duration = 40  # 30 seconds
    elif current_level == 2:  # Medium Level
        matches_needed = 4  # 4 matches required
        game_duration = 60  # 40 seconds
    elif current_level == 3:  # Hard Level
        matches_needed = 6  # 6 matches required
        game_duration = 80  # 60 seconds

# Function to set up a new game
def setup_game():
    global animals, shadows, animal_positions, shadow_positions, matches_needed, game_background
    
    animals = []
    shadows = []
    
    # Define animal types
    animal_types = ["elephant", "lion", "monkey", "giraffe", "rabbit", "bird"]
    
    # Set matches_needed based on the current level
    update_game_parameters()
    
    # Define grid positions for animals (left side)
    if current_level == 2:
        # For level 2, arrange in a 2x2 grid
        rows = 2
        cols = 2
        animal_grid_width = SCREEN_WIDTH * 0.4
        animal_grid_height = SCREEN_HEIGHT * 0.6
        animal_horizontal_spacing = animal_grid_width / cols
        animal_vertical_spacing = animal_grid_height / rows
        
        animal_positions = []
        for i in range(rows):
            for j in range(cols):
                x = 150 + (j * animal_horizontal_spacing)
                y = 150 + (i * animal_vertical_spacing)
                animal_positions.append((x, y))
    else:
        # For other levels, use the existing layout
        rows = 3
        animal_grid_height = SCREEN_HEIGHT * 0.9
        animal_vertical_spacing = animal_grid_height / rows
        
        animal_positions = []
        for i in range(matches_needed):
            row = i % rows
            col = i // rows
            x = 150 + (col * 200)
            y = 100 + (row * animal_vertical_spacing)
            animal_positions.append((x, y))
    
    # Shuffle animal positions
    random.shuffle(animal_positions)
    
    # Define grid positions for shadows (right side)
    if current_level == 2:
        # For level 2, arrange in a 2x2 grid
        shadow_positions = []
        for i in range(rows):
            for j in range(cols):
                x = SCREEN_WIDTH - 550 + (j * animal_horizontal_spacing)
                y = 150 + (i * animal_vertical_spacing)
                shadow_positions.append((x, y))
    else:
        # For other levels, use the existing layout
        shadow_positions = []
        for i in range(matches_needed):
            row = i % rows
            col = i // rows
            x = SCREEN_WIDTH - 550 + (col * 200)
            y = 100 + (row * animal_vertical_spacing)
            shadow_positions.append((x, y))
    
    # Shuffle shadow positions
    random.shuffle(shadow_positions)
    
    # Create animal objects
    for i, animal_type in enumerate(animal_types[:matches_needed]):
        animal = Animal(animal_type, animal_positions[i])
        animals.append(animal)
    
    # Create shadow objects (same animals but in shadow form)
    for i, animal_type in enumerate(animal_types[:matches_needed]):
        shadow = Animal(animal_type, shadow_positions[i])
        shadows.append(shadow)
    
    # Create initial game background with animals and shadows
    game_background = create_game_background(animals, shadows)

def restart_game():
    global score, matches, start_time, current_selection, game_state, game_background, session_ended
    score = 0
    matches = 0
    start_time = datetime.now()
    current_selection = None
    session_ended = False  # Reset session_ended when restarting the game
    setup_game()
    return "playing"

# Function to display a pop-up message
def show_message(message, duration=2000):  # duration in milliseconds
    font = pygame.font.Font(None, 74)
    text_surf = font.render(message, True, (255, 255, 0))
    text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    SCREEN.blit(text_surf, text_rect)
    pygame.display.update()
    pygame.time.delay(duration)  # Display the message for the specified duration

# Add a global variable to track rounds played
rounds_played = 0

def check_performance_and_adjust_level():
    global current_level, matches, start_time, game_duration, game_state, rounds_played, session_ended
    elapsed_time = (datetime.now() - start_time).seconds

    # In the second round, do not count level up or down when time is up
    if rounds_played >= 1:
        return

    # Check if all matches are completed within the required time for each level
    if current_level == 3 and matches >= matches_needed:
        # Player is in level 3 and matches all 6 images
        game_state = "game_over"
        save_player_data(score, is_game_end=True)  # Save cognitive level and tasks, increment task counter
        return
    elif current_level == 3 and elapsed_time >= 70 and matches < 4:
        # Level Down from Level 3 to Level 2 if not enough matches are completed
        current_level -= 1
        save_player_data(score, is_game_end=False)  # Do not increment task count here
        show_message("Level Down!")
        update_game_parameters()
        rounds_played += 1
        if rounds_played >= 2:
            game_state = "game_over"
        else:
            restart_game()
    elif current_level == 2 and matches >= matches_needed and elapsed_time <= 50:
        # Level Up from Level 2 to Level 3
        current_level += 1
        save_player_data(score, is_game_end=False)  # Do not increment task count here
        show_message("Level Up!")
        update_game_parameters()
        rounds_played += 1
        if rounds_played >= 2:
            game_state = "game_over"
        else:
            restart_game()
    elif current_level == 2 and elapsed_time >= 50 and matches < 2:
        # Level Down from Level 2 to Level 1 if not enough matches are completed
        current_level -= 1
        save_player_data(score, is_game_end=False)  # Do not increment task count here
        show_message("Level Down!")
        update_game_parameters()
        rounds_played += 1
        if rounds_played >= 2:
            game_state = "game_over"
        else:
            restart_game()
    elif current_level == 1 and matches >= matches_needed and elapsed_time <= 30:
        # Level Up from Level 1 to Level 2
        current_level += 1
        save_player_data(score, is_game_end=False)  # Do not increment task count here
        show_message("Level Up!")
        update_game_parameters()
        rounds_played += 1
        if rounds_played >= 2:
            game_state = "game_over"
        else:
            restart_game()
            
# Create hand cursor
hand_cursor = HandCursor()

# Game variables
score = 0
matches = 0
# Load cognitive data at the start of the game
current_level, cognitive_tasks = load_player_data()
game_duration = 60  # Default duration for Medium level
start_time = datetime.now()
game_state = "playing"  # Possible states: "playing", "game_over"
current_selection = None
show_tutorial = True
tutorial_timer = 5  # Display tutorial for 5 seconds
tutorial_start = time.time()
game_background = None  # Will store the background with animals and shadows

# Set up first game
setup_game()

# Add this function to create a button
def draw_button(screen, text, x, y, width, height, inactive_color, active_color, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    # Check if the mouse is over the button
    if x + width > mouse[0] > x and y + height > mouse[1] > y:
        pygame.draw.rect(screen, active_color, (x, y, width, height))
        if click[0] == 1 and action is not None:
            action()
    else:
        pygame.draw.rect(screen, inactive_color, (x, y, width, height))

    # Render the text on the button
    font = pygame.font.Font(None, 36)
    text_surf = font.render(text, True, (0, 0, 0))
    text_rect = text_surf.get_rect(center=(x + width / 2, y + height / 2))
    screen.blit(text_surf, text_rect)
    
# Add this function to quit the game
def quit_game():
    global running
    running = False

# Main loop
clock = pygame.time.Clock()
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get frame from webcam
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally for a mirror effect
    frame = cv2.flip(frame, 1)

    # Convert the frame from BGR (OpenCV default) to RGB (MediaPipe requires RGB)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame with MediaPipe Hands to detect hand landmarks
    results = hands.process(rgb_frame)

    # Draw hand landmarks on the frame (for visual feedback)
    is_grabbing_detected = False
    hand_position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)  # Default position
    hand_y = 0
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks on the frame
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )
            
            # Check if hand is in a grabbing position
            is_grabbing_detected = is_grabbing(hand_landmarks)
            
            # Get wrist position
            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
            hand_x = int(wrist.x * SCREEN_WIDTH)
            hand_y = int(wrist.y * SCREEN_HEIGHT)
            hand_position = (hand_x, hand_y)
    
    # Update hand cursor
    hand_cursor.update(hand_position, is_grabbing_detected, hand_y / SCREEN_HEIGHT)
    
    # Draw the game background
    SCREEN.blit(background, (0, 0))
    
    # Check game state and update accordingly
    if game_state == "playing":
        # Draw tutorial message for first few seconds
        if show_tutorial:
            tutorial_text = [
                "Match the animals with their shadows!",
                "1. Move your hand to the animal",
                "2. Hold your fist closed to grab it",
                "3. Move to the matching shadow",
                "4. Hold closed fist again to confirm the match"
            ]
            
            # Increase the size of the tutorial background box
            tutorial_bg_width = 800  # Increased width
            tutorial_bg_height = 300  # Increased height
            tutorial_bg = pygame.Surface((tutorial_bg_width, tutorial_bg_height), pygame.SRCALPHA)
            tutorial_bg.fill((0, 0, 0, 180))  # Semi-transparent black
            
            # Position the background box
            SCREEN.blit(tutorial_bg, (SCREEN_WIDTH // 2 - tutorial_bg_width // 2, SCREEN_HEIGHT // 2 - tutorial_bg_height // 2))
            
            # Render and position the tutorial text
            for i, line in enumerate(tutorial_text):
                text = font_medium.render(line, True, WHITE)
                SCREEN.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 
                                  SCREEN_HEIGHT // 2 - 140 + i * 40))  # Adjusted vertical spacing
            
            if time.time() - tutorial_start > tutorial_timer:
                show_tutorial = False
        else:
            # Draw the game background (with animals and shadows)
            SCREEN.blit(game_background, (0, 0))
            
            # Update elapsed time
            elapsed_time = (datetime.now() - start_time).seconds
            time_left = max(0, game_duration - elapsed_time)
            
            # Game Over Logic
            if time_left <= 0 and game_state == "playing":
                game_state = "game_over"
                save_player_data(score, is_game_end=True)  # Save cognitive level and tasks, increment task counter
                # Display game over message for 2 seconds
                font = pygame.font.Font(None, 100)
                game_over_text = font.render("Game Over!", True, (255, 0, 0))
                score_final_text = font.render(f"Final Score: {score}", True, (255, 255, 0))
                SCREEN.blit(game_over_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50))
                SCREEN.blit(score_final_text, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 + 50))
                pygame.display.update()
                pygame.time.delay(2000)  # Wait for 2 seconds
                running = False  # Exit the game loop
                continue

            # Check if all matches are complete
            if matches >= matches_needed:
                # Game complete
                game_state = "game_over"
                score = 100  # Ensure the score is 100 when all matches are complete
                save_player_data(score, is_game_end=True)  # Ensure the final score is saved
                # Check for level-up immediately after completing all matches
                check_performance_and_adjust_level()
            
            # Draw any selected animal or highlight effects that need to be on top of background
            if hand_cursor.selected_animal is not None:
                # Highlight selected animal
                glow_rect = pygame.Rect(
                    hand_cursor.selected_animal.rect.x - 15, 
                    hand_cursor.selected_animal.rect.y - 15, 
                    hand_cursor.selected_animal.rect.width + 30, 
                    hand_cursor.selected_animal.rect.height + 30
                )
                pygame.draw.rect(SCREEN, YELLOW, glow_rect, 3, border_radius=15)
            
            # Draw matched animals and shadows with green glow
            for animal in animals:
                if animal.matched:
                    glow_rect = pygame.Rect(
                        animal.rect.x - 10, 
                        animal.rect.y - 10, 
                        animal.rect.width + 20, 
                        animal.rect.height + 20
                    )
                    pygame.draw.rect(SCREEN, GREEN, glow_rect, border_radius=15)
            
            for shadow in shadows:
                if shadow.matched:
                    glow_rect = pygame.Rect(
                        shadow.rect.x - 10, 
                        shadow.rect.y - 10, 
                        shadow.rect.width + 20, 
                        shadow.rect.height + 20
                    )
                    pygame.draw.rect(SCREEN, GREEN, glow_rect, 5, border_radius=15)
            
            # Handle animal selection and matching logic
            if hand_cursor.is_grab_confirmed:
                if hand_cursor.selected_animal is None:
                    # Try to select an animal
                    for animal in animals:
                        if not animal.matched and animal.rect.collidepoint(hand_cursor.position):
                            hand_cursor.selected_animal = animal
                            animal.is_selected = True
                            # Reset grab confirmation after selecting an animal
                            hand_cursor.is_grab_confirmed = False
                            hand_cursor.grab_timer = 0
                            break
                else:
                    # Try to match with a shadow
                    for shadow in shadows:
                        if not shadow.matched and shadow.rect.collidepoint(hand_cursor.position):
                            if hand_cursor.selected_animal.name == shadow.name:
                                # Start confirmation timer
                                if hand_cursor.confirm_timer == 0:
                                    hand_cursor.confirm_timer = time.time()
                                elif time.time() - hand_cursor.confirm_timer >= hand_cursor.confirm_threshold:
                                    # Correct match!
                                    hand_cursor.selected_animal.matched = True
                                    shadow.matched = True
                                    hand_cursor.selected_animal.is_selected = False
                                    matches += 1
                                    score += 17  # 17 points per correct match (100 / 6 ≈ 16.67)
                                    
                                    # Ensure the score does not exceed 100
                                    if matches == matches_needed:
                                        score = 100  # Set score to 100 if all matches are complete
                                    
                                    # Update game background with matched items
                                    game_background = create_game_background(animals, shadows)
                                    
                                    # Play correct sound
                                    if correct_sound:
                                        correct_sound.play()
                                    
                                    # Reset confirmation timer and hand cursor state
                                    hand_cursor.confirm_timer = 0
                                    hand_cursor.selected_animal = None
                                    hand_cursor.is_grab_confirmed = False
                                    hand_cursor.grab_timer = 0
                                    
                                    # Check for level-up immediately after a successful match
                                    check_performance_and_adjust_level()
                            else:
                                # Wrong match
                                hand_cursor.selected_animal.is_selected = False
                                score = max(0, score - 5)  # Penalty of 5 points
                                hand_cursor.confirm_timer = 0  # Reset confirmation timer
                                hand_cursor.selected_animal = None
                                hand_cursor.is_grab_confirmed = False
                                hand_cursor.grab_timer = 0
                            
                            break
                    
                    # If not colliding with any shadow, just keep the animal selected
                    
            # Handle the case when grabbing is released (important for resetting states)
            elif not hand_cursor.is_grabbing and hand_cursor.is_grab_confirmed:
                hand_cursor.is_grab_confirmed = False
                hand_cursor.grab_timer = 0
                hand_cursor.confirm_timer = 0
            
            # Check if all matches are complete
            if matches >= matches_needed:
                # Game complete
                game_state = "game_over"
                score = 100  # Ensure the score is 100 when all matches are complete
                # Check for level-up immediately after completing all matches
                check_performance_and_adjust_level()
                
            # Draw score and timer
            score_text = font_large.render(f"Score: {score}/100", True, YELLOW)
            timer_text = font_large.render(f"Time: {time_left}", True, YELLOW)  # Yellow timer text
            matches_text = font_medium.render(f"Matches: {matches}/{matches_needed}", True, YELLOW)
            
            # Display only score and time at the top
            SCREEN.blit(score_text, (10, 10))
            SCREEN.blit(timer_text, (SCREEN_WIDTH - 250, 10))
            SCREEN.blit(matches_text, (SCREEN_WIDTH // 2 - 100, 10))
            
            # Draw the quit button
            draw_button(SCREEN, "Quit", SCREEN_WIDTH - 180, 60, 140, 50, (255, 0, 0), (200, 0, 0), quit_game)
            
            # Check performance and adjust level dynamically
            check_performance_and_adjust_level()
            
    elif game_state == "game_over":
        # Save the player's level and final score when the game ends
        save_player_data(score, is_game_end=True)
        
        # Draw game over screen - use semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        SCREEN.blit(overlay, (0, 0))
        
        # Use the larger font_title for the main message
        game_over_text = font_title.render("Game Over!", True, RED)
        score_final_text = font_title.render(f"Final Score: {score}/100", True, YELLOW)  # Yellow score text
        
        SCREEN.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 150))
        SCREEN.blit(score_final_text, (SCREEN_WIDTH // 2 - score_final_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        
        # Wait for 2 seconds before closing
        pygame.display.update()
        pygame.time.delay(2000)
        running = False  # Exit the game loop
    
    # Draw the hand cursor
    hand_cursor.draw(SCREEN)
    
    # Update the display
    pygame.display.update()
    clock.tick(60)  # Limit to 60 FPS
    
    # Display the webcam feed in a separate window (with hand landmarks)
    cv2.imshow("Jungle Shadow Matcher", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()
import pygame
import sys
import random
import cv2
import mediapipe as mp
from datetime import datetime
import json

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize the mixer module
pygame.display.set_caption("Fish Catcher Game")
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

# Load background image
background = pygame.image.load("assets/background.jpg")  # Replace with your background image
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Constants for fish
FISH_SIZE_RANDOMIZE = (0.7, 1.3)
FISH_SIZES = (50, 50)

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

# Fish class
class Fish:
    def __init__(self, fish_type, speed_range):
        # Randomize the size of the fish
        random_size_value = random.uniform(FISH_SIZE_RANDOMIZE[0], FISH_SIZE_RANDOMIZE[1])
        size = (int(FISH_SIZES[0] * random_size_value), int(FISH_SIZES[1] * random_size_value))
        
        # Define the spawn position and direction based on fish type
        self.fish_type = fish_type
        self.moving_direction, self.pos = self.define_spawn_pos(size)
        
        # Create a rectangle for collision detection
        self.rect = pygame.Rect(self.pos[0], self.pos[1], size[0] // 1.4, size[1] // 1.4)
        
        # Load and resize the fish image based on fish type
        if self.fish_type == "fish1":
            self.image = pygame.transform.scale(pygame.image.load("assets/fish1.png"), size)  # Replace with your fish1 image
        elif self.fish_type == "fish2":
            self.image = pygame.transform.scale(pygame.image.load("assets/fish2.png"), size)  # Replace with your fish2 image
        
        # Set a random speed for the fish
        self.speed = random.randint(speed_range[0], speed_range[1])  # Random speed within the range

    def define_spawn_pos(self, size):
        # Fish1 moves to the right, Fish2 moves to the left
        if self.fish_type == "fish1":
            moving_direction = "right"
            pos = (random.randint(0, SCREEN_WIDTH // 2), random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT - size[1]))  # Spawn in the left half
        elif self.fish_type == "fish2":
            moving_direction = "left"
            pos = (random.randint(SCREEN_WIDTH // 2, SCREEN_WIDTH - size[0]), random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT - size[1]))  # Spawn in the right half
        return moving_direction, pos

    def move(self):
        # Move the fish based on its direction
        if self.moving_direction == "right":
            self.rect.x += self.speed
            if self.rect.x > SCREEN_WIDTH:  # Reset position if it goes off-screen
                self.rect.x = -self.rect.width
        elif self.moving_direction == "left":
            self.rect.x -= self.speed
            if self.rect.x < -self.rect.width:  # Reset position if it goes off-screen
                self.rect.x = SCREEN_WIDTH

# Hand class (represents the child's hand)
class Hand:
    def __init__(self):
        # Load and resize the hand image (larger size for easier catching)
        self.image = pygame.transform.scale(pygame.image.load("assets/catcher.png"), (150, 150))  # Increased size
        
        # Create a rectangle for the hand and center it on the screen
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        # Track if hand is in closed fist position
        self.is_closed_fist = False
        
        # Track if hand is moving upward
        self.previous_y = None
        self.is_moving_up = False
        self.movement_threshold = 0.02  # Minimum vertical movement to consider

    def update(self, pos, is_closed_fist, current_y):
        # Update the hand's position based on the input coordinates
        self.rect.center = pos
        self.is_closed_fist = is_closed_fist
        
        # Determine if hand is moving upward
        if self.previous_y is not None:
            y_change = current_y - self.previous_y
            self.is_moving_up = y_change < -self.movement_threshold
        
        self.previous_y = current_y

# Function to detect if hand is in a closed fist position
def is_closed_fist(hand_landmarks):
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

# Function to load player level from JSON file
def load_player_data():
    try:
        with open("player_data.json", "r") as file:
            data = json.load(file)
            return data.get("playerLevel", 2)  # Default to level 2 if missing
    except FileNotFoundError:
        return 2  # Default to level 2 if file doesn't exist

# Function to save player level to JSON file
def save_player_data(level):
    with open("player_data.json", "w") as file:
        json.dump({"playerLevel": level}, file)

# Function to restart the game
def restart_game():
    global fishes, score, start_time, current_level
    fishes = [Fish("fish1", fish_speed_range) for _ in range(MAX_FISH // 2)] + [Fish("fish2", fish_speed_range) for _ in range(MAX_FISH // 2)]
    score = 0
    start_time = datetime.now()
    return "playing"

# Function to update player level without saving to JSON
def update_player_level(score, current_level):
    new_level = current_level  # Default to the current level
    if score >= 60 and current_level < 3:
        new_level = current_level + 1  # Level up
    elif score < 10 and current_level > 1:
        new_level = current_level - 1  # Level down
    return new_level

def save_player_data(level, final_score=None):
    # Load existing data if the file exists
    try:
        with open("player_data.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    # Update the level
    data["playerLevel"] = level

    # Add the final score if provided
    if final_score is not None:
        data["finalScore"] = final_score

    # Save the updated data to the JSON file
    with open("player_data.json", "w") as file:
        json.dump(data, file)

# Load player level
current_level = load_player_data()

# Function to display a pop-up message
def show_message(message, duration=2000):  # duration in milliseconds
    font = pygame.font.Font(None, 74)
    text_surf = font.render(message, True, (255, 255, 0))
    text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    SCREEN.blit(text_surf, text_rect)
    pygame.display.update()
    pygame.time.delay(duration)  # Display the message for the specified duration

# Function to update game parameters based on the current level
def update_game_parameters():
    global MAX_FISH, SPAWN_INTERVAL, fish_speed_range, game_duration
    if current_level == 1:  # Easy Level
        MAX_FISH = 15  # More fish
        game_duration = 60  # 1 minute
        SPAWN_INTERVAL = (300, 1000)  # fatser spawn
        fish_speed_range = (3, 5)  # faster movement
    elif current_level == 2:  # Medium Level
        MAX_FISH = 10
        game_duration = 60  # 1 minute
        SPAWN_INTERVAL = (500, 2000)
        fish_speed_range = (1, 3)
    elif current_level == 3:  # Hard Level
        MAX_FISH = 5  # Fewer fish
        game_duration = 60  # 1 minute
        SPAWN_INTERVAL = (1000, 3000)  # slower spawn
        fish_speed_range = (1, 2)  # slower movement

def check_performance_and_adjust_level():
    global current_level, fishes, score, start_time
    elapsed_time = (datetime.now() - start_time).seconds

    # Level Down Criteria: If the child fails to catch 30 fishes within 30 seconds
    if elapsed_time % 40 == 0 and elapsed_time > 0:  # Check every 10 seconds
        if score < 30 * (elapsed_time // 40) and current_level > 1:  # Level Down
            current_level -= 1
            save_player_data(current_level)
            show_message("Level Down!")
            update_game_parameters()  # Update game parameters for the new level
            # Reset fish list for the new level
            fishes = [Fish("fish1", fish_speed_range) for _ in range(MAX_FISH // 2)] + [Fish("fish2", fish_speed_range) for _ in range(MAX_FISH // 2)]

    # Level Up Criteria: If the child catches 60 fishes within 40 seconds
    if elapsed_time == 40:  # Check at 40 seconds
        if score >= 60 and current_level < 3:  # Level Up
            current_level += 1
            save_player_data(current_level)
            show_message("Level Up!")
            update_game_parameters()  # Update game parameters for the new level
            # Reset fish list for the new level
            fishes = [Fish("fish1", fish_speed_range) for _ in range(MAX_FISH // 2)] + [Fish("fish2", fish_speed_range) for _ in range(MAX_FISH // 2)]
# Initialize game parameters
update_game_parameters()

# Create instances
fishes = [Fish("fish1", fish_speed_range) for _ in range(MAX_FISH // 2)] + [Fish("fish2", fish_speed_range) for _ in range(MAX_FISH // 2)]  # Half fish1, half fish2
hand = Hand()  # Create the hand

# Game variables
score = 0
start_time = datetime.now()
game_state = "playing"  # Possible states: "playing", "game_over"

# Main loop
clock = pygame.time.Clock()
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Normal game logic when playing
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
    hand_closed = False
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
            
            # Check if hand is in a closed fist position
            hand_closed = is_closed_fist(hand_landmarks)
            
            # Get wrist position
            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
            hand_x = int(wrist.x * SCREEN_WIDTH)
            hand_y = int(wrist.y * SCREEN_HEIGHT)
            hand_position = (hand_x, hand_y)
    
    # Update hand position and closed status
    hand.update(hand_position, hand_closed, hand_y / SCREEN_HEIGHT)
    
    # Check for fish catching
    # Only catch fish if the hand is in a closed fist position AND moving upwards
    if hand.is_closed_fist and hand.is_moving_up:
        for fish in fishes[:]:  # Iterate over a copy of the fishes list
            if hand.rect.colliderect(fish.rect):  # If the hand collides with a fish
                try:
                    pygame.mixer.Sound("assets/catch_sound.ogg").play()  # Play sound
                except FileNotFoundError:
                    print("Sound file not found. Please add 'catch_sound.ogg' to the 'assets' folder.")
                fishes.remove(fish)  # Remove the fish from the list
                score += 1  # Increase the score
                # Add a new fish of the same type to maintain the count
                if fish.fish_type == "fish1":
                    fishes.append(Fish("fish1", fish_speed_range))
                elif fish.fish_type == "fish2":
                    fishes.append(Fish("fish2", fish_speed_range))

    # Move all fish
    for fish in fishes:
        fish.move()

    # Draw the background
    SCREEN.blit(background, (0, 0))

    # Draw all fish
    for fish in fishes:
        SCREEN.blit(fish.image, fish.rect.topleft)

    # Draw the hand
    SCREEN.blit(hand.image, hand.rect.topleft)

    # Draw the score
    font = pygame.font.Font(None, 74)
    score_text = font.render(f"Fish Caught: {score}", True, (255, 255, 0))
    SCREEN.blit(score_text, (10, 10))

    # Draw the timer
    elapsed_time = (datetime.now() - start_time).seconds
    time_left = max(0, game_duration - elapsed_time)
    timer_text = font.render(f"Time: {time_left}", True, (255, 255, 0))
    SCREEN.blit(timer_text, (SCREEN_WIDTH - 200, 10))

    # Check performance and adjust level dynamically
    check_performance_and_adjust_level()

    # Check if time is up
    if time_left <= 0 and game_state == "playing":
        game_state = "game_over"
        # Save the player's level and final score when the game ends naturally
        save_player_data(current_level , score)
        # Display game over message
        font = pygame.font.Font(None, 100)
        game_over_text = font.render("Game Over!", True, (255, 0, 0))
        score_final_text = font.render(f"Final Score: {score}", True, (255, 255, 0))
        SCREEN.blit(game_over_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50))
        SCREEN.blit(score_final_text, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 + 50))
        pygame.display.update()
        pygame.time.delay(2000)  # Wait for 2 seconds
        running = False  # Exit the game loop

    # Update the display
    pygame.display.update()
    clock.tick(60)  # Limit the frame rate to 60 FPS

    # Display the webcam feed in a separate window (with hand landmarks)
    cv2.imshow("Fish Catcher Game", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit (keeping this as an emergency exit)
        break

# Release resources
cap.release()  # Release the webcam
cv2.destroyAllWindows()  # Close all OpenCV windows
pygame.quit()  # Quit Pygame
sys.exit()  # Exit the program
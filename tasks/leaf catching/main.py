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
pygame.display.set_caption("Leaf Catching Game")
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

# Load images
background = pygame.image.load("assets/background.jpeg")
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
leaf_image = pygame.image.load("assets/leaf.png")
hand_image = pygame.image.load("assets/hand1.png")

# Constants for leaves
LEAF_SIZE = (50, 50)
LEAF_SPEED_RANGE = (1, 5)  # Speed range for leaves
LEAF_SPAWN_RATE = (500, 1000)  # Spawn interval range in milliseconds

# Hand state
HAND_OPEN = 0
HAND_CLOSED = 1

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Initialize webcam
cap = cv2.VideoCapture(0)

# Leaf class
class Leaf:
    def __init__(self, speed_range):
        self.image = pygame.transform.scale(leaf_image, LEAF_SIZE)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - LEAF_SIZE[0])
        self.rect.y = -LEAF_SIZE[1]  # Start above the screen
        self.speed = random.randint(speed_range[0], speed_range[1])  # Random speed

    def move(self):
        self.rect.y += self.speed

    def is_off_screen(self):
        return self.rect.y > SCREEN_HEIGHT

# Hand class
class Hand:
    def __init__(self):
        self.image = pygame.transform.scale(hand_image, (100, 100))  # Resized hand
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.state = HAND_OPEN

    def update(self, pos):
        self.rect.center = pos

    def set_state(self, state):
        self.state = state

# Function to load motor progress (Level & Tasks) from the primary JSON file
def load_motor_data():
    try:
        with open("player_data.json", "r") as file:
            data = json.load(file)
            # Check for the new format (motor-level and motor-tasks as separate keys)
            if "motor-level" in data and "motor-tasks" in data:
                return data["motor-level"], data["motor-tasks"]
            # Fallback to the old format (nested under "motor")
            elif "motor" in data:
                return data["motor"].get("level", 2), data["motor"].get("tasks", 0)
            else:
                return 2, 0  # Default to Level 2, tasks start at 0
    except FileNotFoundError:
        return 2, 0  # Default to Level 2, tasks start at 0 if file doesn't exist

# Function to save motor level and task count to the primary JSON file
def save_motor_data(score):
    global current_level, motor_tasks
    try:
        with open("player_data.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}  # If file doesn't exist, create a new dictionary

    # Initialize motor data if not present (using the new format)
    if "motor-level" not in data:
        data["motor-level"] = 2  # First-time default: Level 2
    if "motor-tasks" not in data:
        data["motor-tasks"] = 0  # First-time default: Tasks 0

    # Update motor level based on final game performance
    if score >= 20 and data["motor-level"] < 3:  # Level Up
        data["motor-level"] += 1
    elif score < 5 and data["motor-level"] > 1:  # Level Down
        data["motor-level"] -= 1

    # Increment motor tasks only when the game session ends
    data["motor-tasks"] += 1

    # Save the updated data
    with open("player_data.json", "w") as file:
        json.dump(data, file, indent=4)

    # Update global variables
    current_level = data["motor-level"]
    motor_tasks = data["motor-tasks"]

    print(f"Motor Level: {current_level}, Motor Tasks: {motor_tasks}")
    

# Function to update game parameters based on the current level
def update_game_parameters():
    global LEAF_SPEED_RANGE, LEAF_SPAWN_RATE, game_duration, MAX_LEAVES
    if current_level == 1:  # Easy Level
        LEAF_SPEED_RANGE = (1, 3)  # Slower leaves
        LEAF_SPAWN_RATE = (500, 1000)  # Faster spawn
        game_duration = 120  # 1 minute
        MAX_LEAVES = 10  # Only 1 leaf on the screen at a time
    elif current_level == 2:  # Medium Level
        LEAF_SPEED_RANGE = (2, 4)
        LEAF_SPAWN_RATE = (300, 800)
        game_duration = 120
        MAX_LEAVES = 8  # Up to 2 leaves on the screen
    elif current_level == 3:  # Hard Level
        LEAF_SPEED_RANGE = (3, 5)  # Faster leaves
        LEAF_SPAWN_RATE = (100, 500)  # Slower spawn
        game_duration = 120
        MAX_LEAVES = 6  # Up to 3 leaves on the screen

# Function to check performance and adjust level dynamically
def check_performance_and_adjust_level():
    global current_level, leaves, score, start_time
    elapsed_time = (datetime.now() - start_time).seconds

    # Level Down Criteria: If the child fails to catch 5 leaves within 80 seconds
    if elapsed_time % 80 == 0 and elapsed_time > 0:  # Check every 80 seconds
        if score < 5 * (elapsed_time // 80) and current_level > 1:  # Level Down
            current_level -= 1
            show_message("Level Down!")
            update_game_parameters()  # Update game parameters for the new level
            # Reset leaves list for the new level
            leaves = [Leaf(LEAF_SPEED_RANGE) for _ in range(MAX_LEAVES)]

    # Level Up Criteria: If the child catches 20 leaves within 80 seconds
    if elapsed_time == 80:  # Check at 80 seconds
        if score >= 20 and current_level < 3:  # Level Up
            current_level += 1
            show_message("Level Up!")
            update_game_parameters()  # Update game parameters for the new level
            # Reset leaves list for the new level
            leaves = [Leaf(LEAF_SPEED_RANGE) for _ in range(MAX_LEAVES)]

# Load motor data (level and tasks) from the primary JSON file
current_level, motor_tasks = load_motor_data()

# Initialize game parameters
update_game_parameters()

# Create instances
leaves = [Leaf(LEAF_SPEED_RANGE) for _ in range(MAX_LEAVES)]
hand = Hand()

# Game variables
score = 0
start_time = datetime.now()
game_state = "playing"  # Possible states: "playing", "game_over"


# Function to display a pop-up message
def show_message(message, duration=2000):  # duration in milliseconds
    font = pygame.font.Font(None, 74)
    text_surf = font.render(message, True, (255, 255, 0))
    text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    SCREEN.blit(text_surf, text_rect)
    pygame.display.update()
    pygame.time.delay(duration)  # Display the message for the specified duration



# Main loop
clock = pygame.time.Clock()
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Capture webcam frame
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally for a mirror effect
    frame = cv2.flip(frame, 1)

    # Convert the frame from BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame with MediaPipe Hands
    results = hands.process(rgb_frame)

    # Reset hand state to OPEN
    hand.set_state(HAND_OPEN)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get hand landmarks
            landmarks = hand_landmarks.landmark

            # Check if hand is closed (thumb tip is close to index tip)
            thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
            index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            distance = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) ** 0.5

            if distance < 0.05:  # Threshold for closed hand
                hand.set_state(HAND_CLOSED)

            # Map hand position to screen coordinates
            hand_x = int(landmarks[mp_hands.HandLandmark.WRIST].x * SCREEN_WIDTH)
            hand_y = int(landmarks[mp_hands.HandLandmark.WRIST].y * SCREEN_HEIGHT)
            hand.update((hand_x, hand_y))

    # Move leaves
    for leaf in leaves:
        leaf.move()

    # Check for collisions and count caught leaves
    if hand.state == HAND_CLOSED:
        for leaf in leaves[:]:
            # Only catch the leaf if the hand is overlapping with it
            if hand.rect.colliderect(leaf.rect):
                leaves.remove(leaf)
                score += 1
                # Spawn a new leaf to maintain the count
                if len(leaves) < MAX_LEAVES:
                    leaves.append(Leaf(LEAF_SPEED_RANGE))

    # Remove leaves that are off-screen
    for leaf in leaves[:]:
        if leaf.is_off_screen():
            leaves.remove(leaf)
            # Spawn a new leaf to maintain the count
            if len(leaves) < MAX_LEAVES:
                leaves.append(Leaf(LEAF_SPEED_RANGE))

    # Draw the background
    SCREEN.blit(background, (0, 0))

    # Draw the leaves
    for leaf in leaves:
        SCREEN.blit(leaf.image, leaf.rect.topleft)

    # Draw the hand
    SCREEN.blit(hand.image, hand.rect.topleft)

    # Draw the score
    font = pygame.font.Font(None, 74)
    score_text = font.render(f"Leaves: {score}", True, (255, 255, 0))
    SCREEN.blit(score_text, (10, 10))

    # Draw the timer
    elapsed_time = (datetime.now() - start_time).seconds
    time_left = max(0, game_duration - elapsed_time)
    timer_text = font.render(f"Time: {time_left}", True, (255, 255, 0))
    SCREEN.blit(timer_text, (SCREEN_WIDTH - 250, 10))

    # Check performance and adjust level dynamically
    check_performance_and_adjust_level()

    # End game if time is up
    if time_left <= 0 and game_state == "playing":
        game_state = "game_over"
        save_motor_data(score)  # Save final score and level
        font = pygame.font.Font(None, 100)
        game_over_text = font.render("Game Over!", True, (255, 0, 0))
        score_final_text = font.render(f"Final Score: {score}", True, (255, 255, 0))
        SCREEN.blit(game_over_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50))
        SCREEN.blit(score_final_text, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 + 50))
        pygame.display.update()
        pygame.time.delay(3000)  # Wait for 3 seconds
        running = False  # Exit the game loop

    # Update the display
    pygame.display.update()
    clock.tick(60)  # Limit the frame rate to 60 FPS

    # Display the webcam feed in a separate window
    cv2.imshow("Leaf Catching Game", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()
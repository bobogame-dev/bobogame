import pygame
import random
import sys
import cv2
import mediapipe as mp
import time

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spot the Odd One!")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Fonts
font = pygame.font.Font(None, 36)

# Box dimensions
BOX_WIDTH = 100
BOX_HEIGHT = 100
BOX_MARGIN = 20

# Game states
START_SCREEN = 0
LEVEL_1 = 1
LEVEL_2 = 2
LEVEL_3 = 3
GAME_OVER = 4

# Game variables
current_level = START_SCREEN
odd_one_index = 0
correct_guesses = 0
attempts = 0
level_start_time = 0
level_time_limit = 0

# Load images
try:
    same_image = pygame.image.load("assets/sameimage.jpeg")  
    odd_image = pygame.image.load("assets/oddimage.jpeg")    
    # Resize images to fit the box dimensions
    same_image = pygame.transform.scale(same_image, (BOX_WIDTH, BOX_HEIGHT))
    odd_image = pygame.transform.scale(odd_image, (BOX_WIDTH, BOX_HEIGHT))
except FileNotFoundError as e:
    print(f"Error loading images: {e}")
    pygame.quit()
    sys.exit()

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# OpenCV video capture
cap = cv2.VideoCapture(0)

def draw_text(text, x, y, color):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def draw_button(text, x, y, width, height, color, hover_color):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x + width > mouse[0] > x and y + height > mouse[1] > y:
        pygame.draw.rect(screen, hover_color, (x, y, width, height))
        if click[0] == 1:
            return True
    else:
        pygame.draw.rect(screen, color, (x, y, width, height))

    draw_text(text, x + 10, y + 10, WHITE)
    return False

def start_screen():
    global current_level, level_start_time, level_time_limit
    screen.fill(WHITE)
    draw_text("Spot the Odd One!", 250, 200, BLACK)
    if draw_button("Play", 350, 300, 100, 50, GREEN, RED):
        current_level = LEVEL_1
        level_start_time = time.time()
        level_time_limit = 60  # 1 minute for Level 1
    pygame.display.update()

def level_1():
    global current_level, odd_one_index, attempts, level_start_time, level_time_limit
    screen.fill(WHITE)
    draw_text("Level 1", 350, 50, BLACK)

    # Randomly select which box is the odd one
    odd_one_index = random.randint(0, 3)

    # Draw 4 boxes with images
    for i in range(4):
        x = 100 + i * (BOX_WIDTH + BOX_MARGIN)
        y = 200
        if i == odd_one_index:
            screen.blit(odd_image, (x, y))  # Odd image
        else:
            screen.blit(same_image, (x, y))  # Same image

    # Display timer
    elapsed_time = int(time.time() - level_start_time)
    remaining_time = max(0, level_time_limit - elapsed_time)
    draw_text(f"Time: {remaining_time}s", 350, 500, BLACK)

    # Check if time is up
    if remaining_time <= 0:
        draw_text("Time's up! Try again.", 250, 550, RED)
        pygame.display.update()
        pygame.time.delay(2000)  # Pause for 2 seconds
        reset_level()

    pygame.display.update()

def level_2():
    global current_level, odd_one_index, attempts, level_start_time, level_time_limit
    screen.fill(WHITE)
    draw_text("Level 2", 350, 50, BLACK)

    # Randomly select which box is the odd one
    odd_one_index = random.randint(0, 5)

    # Draw 6 boxes with images
    for i in range(6):
        x = 50 + i * (BOX_WIDTH + BOX_MARGIN)
        y = 200
        if i == odd_one_index:
            screen.blit(odd_image, (x, y))  # Odd image
        else:
            screen.blit(same_image, (x, y))  # Same image

    # Display timer
    elapsed_time = int(time.time() - level_start_time)
    remaining_time = max(0, level_time_limit - elapsed_time)
    draw_text(f"Time: {remaining_time}s", 350, 500, BLACK)

    # Check if time is up
    if remaining_time <= 0:
        draw_text("Time's up! Try again.", 250, 550, RED)
        pygame.display.update()
        pygame.time.delay(2000)  # Pause for 2 seconds
        reset_level()

    pygame.display.update()

def level_3():
    global current_level, odd_one_index, attempts, level_start_time, level_time_limit
    screen.fill(WHITE)
    draw_text("Level 3", 350, 50, BLACK)

    # Randomly select which box is the odd one
    odd_one_index = random.randint(0, 8)

    # Draw 9 boxes in a 3x3 grid with images
    for i in range(9):
        x = 50 + (i % 3) * (BOX_WIDTH + BOX_MARGIN)
        y = 150 + (i // 3) * (BOX_HEIGHT + BOX_MARGIN)
        if i == odd_one_index:
            screen.blit(odd_image, (x, y))  # Odd image
        else:
            screen.blit(same_image, (x, y))  # Same image

    # Display timer
    elapsed_time = int(time.time() - level_start_time)
    remaining_time = max(0, level_time_limit - elapsed_time)
    draw_text(f"Time: {remaining_time}s", 350, 500, BLACK)

    # Check if time is up
    if remaining_time <= 0:
        draw_text("Time's up! Try again.", 250, 550, RED)
        pygame.display.update()
        pygame.time.delay(2000)  # Pause for 2 seconds
        reset_level()

    pygame.display.update()

def game_over():
    screen.fill(WHITE)
    draw_text("Congratulations! You completed the task!", 150, 250, BLACK)
    pygame.display.update()

def reset_level():
    global current_level, attempts, level_start_time, level_time_limit
    attempts += 1
    if attempts >= 3:
        current_level = START_SCREEN
        attempts = 0
    else:
        level_start_time = time.time()

def check_hand_gesture():
    global current_level, correct_guesses, odd_one_index, attempts, level_start_time, level_time_limit
    ret, frame = cap.read()
    if not ret:
        return

    # Flip the frame horizontally for a later selfie-view display
    frame = cv2.flip(frame, 1)

    # Convert the BGR image to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame with MediaPipe Hands
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get the index finger tip coordinates
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            x = int(index_finger_tip.x * SCREEN_WIDTH)
            y = int(index_finger_tip.y * SCREEN_HEIGHT)

            # Check if the index finger is pointing at a box
            if current_level == LEVEL_1:
                for i in range(4):
                    box_x = 100 + i * (BOX_WIDTH + BOX_MARGIN)
                    box_y = 200
                    if box_x < x < box_x + BOX_WIDTH and box_y < y < box_y + BOX_HEIGHT:
                        if i == odd_one_index:
                            correct_guesses += 1
                            current_level = LEVEL_2
                            level_start_time = time.time()
                            level_time_limit = 120  # 2 minutes for Level 2
                        else:
                            reset_level()
            elif current_level == LEVEL_2:
                for i in range(6):
                    box_x = 50 + i * (BOX_WIDTH + BOX_MARGIN)
                    box_y = 200
                    if box_x < x < box_x + BOX_WIDTH and box_y < y < box_y + BOX_HEIGHT:
                        if i == odd_one_index:
                            correct_guesses += 1
                            current_level = LEVEL_3
                            level_start_time = time.time()
                            level_time_limit = 180  # 3 minutes for Level 3
                        else:
                            reset_level()
            elif current_level == LEVEL_3:
                for i in range(9):
                    box_x = 50 + (i % 3) * (BOX_WIDTH + BOX_MARGIN)
                    box_y = 150 + (i // 3) * (BOX_HEIGHT + BOX_MARGIN)
                    if box_x < x < box_x + BOX_WIDTH and box_y < y < box_y + BOX_HEIGHT:
                        if i == odd_one_index:
                            correct_guesses += 1
                            current_level = GAME_OVER
                        else:
                            reset_level()

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if current_level == START_SCREEN:
        start_screen()
    elif current_level == LEVEL_1:
        level_1()
        check_hand_gesture()
    elif current_level == LEVEL_2:
        level_2()
        check_hand_gesture()
    elif current_level == LEVEL_3:
        level_3()
        check_hand_gesture()
    elif current_level == GAME_OVER:
        game_over()

    pygame.time.delay(100)

cap.release()
pygame.quit()
sys.exit()
import cv2
import random
import mediapipe as mp
import numpy as np
import time

# Set up MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# Game settings
balloon_radius = 40
score = 0
game_duration = 60  # Game time in seconds
start_time = time.time()  # Record the start time

# Initialize the webcam
cap = cv2.VideoCapture(0)

# Get the screen resolution (optional to set your screen size)
screen_res = (640, 480)  # Use default webcam resolution (you can change this)

# Function to detect pinch gesture
def is_pinch(landmarks):
    # Checking distance between index tip (8) and thumb tip (4)
    index_finger = landmarks[8]
    thumb = landmarks[4]
    distance = ((index_finger.x - thumb.x) ** 2 + (index_finger.y - thumb.y) ** 2) ** 0.5
    return distance < 0.05  # Threshold for pinch gesture detection

# Function to draw a more realistic balloon
def draw_balloon(x, y, color):
    # Create an elliptical balloon shape (a simple gradient fill effect to mimic shine)
    overlay = frame.copy()
    cv2.ellipse(overlay, (x, y), (balloon_radius, int(balloon_radius * 1.3)), 0, 0, 360, color, -1)  # Elliptical shape
    # Add a shine effect with a lighter color on top
    shine_color = (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))
    cv2.ellipse(overlay, (x - 10, y - 20), (balloon_radius // 2, balloon_radius // 2), 0, 0, 360, shine_color, -1)
    alpha = 0.7  # Transparency of the overlay
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

# Function to show score
def show_score(score):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, f"Score: {score}", (10, 30), font, 1, (0, 255, 0), 2, cv2.LINE_AA)

# Balloons list and game loop
balloons = [{'x': random.randint(balloon_radius, screen_res[0] - balloon_radius), 
             'y': screen_res[1], 
             'color': (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
             'speed': random.randint(3, 7)}]  # Random speed for each balloon

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally
    frame = cv2.flip(frame, 1)

    # Convert the frame to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Move balloons up with varying speeds
    for balloon in balloons:
        balloon['y'] -= balloon['speed']  # Move the balloon at its assigned speed
        balloon['x'] += random.randint(-2, 2)  # Slight horizontal movement for randomness
        if balloon['y'] < 0:  # If balloon goes out of screen, regenerate it at the bottom
            balloon['y'] = screen_res[1]
            balloon['x'] = random.randint(balloon_radius, screen_res[0] - balloon_radius)
            balloon['color'] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            balloon['speed'] = random.randint(3, 7)  # Assign a new random speed to the balloon

    # Draw the balloons
    for balloon in balloons:
        draw_balloon(balloon['x'], balloon['y'], balloon['color'])

    # Check if a pinch gesture is detected and pop balloons
    if results.multi_hand_landmarks:
        for landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)

            if is_pinch(landmarks.landmark):
                for balloon in balloons:
                    # Pop the balloon if it's within a certain area around the fingers
                    if abs(balloon['x'] - landmarks.landmark[8].x * screen_res[0]) < balloon_radius and \
                       abs(balloon['y'] - landmarks.landmark[8].y * screen_res[1]) < balloon_radius:
                        score += 1
                        balloons.remove(balloon)
                        balloons.append({'x': random.randint(balloon_radius, screen_res[0] - balloon_radius),
                                         'y': screen_res[1],
                                         'color': (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
                                         'speed': random.randint(3, 7)})  # New balloon with random speed
    
    # Show the current score
    show_score(score)

    # Check if the game time has expired (120 seconds)
    elapsed_time = time.time() - start_time
    if elapsed_time > game_duration:
        # Display final score with a balloon background
        final_score_text = f"Game Over! Final Score: {score}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, final_score_text, (screen_res[0] // 4, screen_res[1] // 2), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow("Balloon Popping Game", frame)
        cv2.waitKey(3000)  # Display the final score for 3 seconds before exiting
        break  # End the game

    # Display the frame without zoom
    cv2.imshow("Balloon Popping Game", frame)

    # Break the loop if the user presses 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

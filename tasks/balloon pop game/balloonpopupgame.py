import cv2
import random
import mediapipe as mp
import numpy as np
import time
import os

# Set up MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Game settings
balloon_radius = 200
score = 0
game_duration = 100  # Game time in seconds
start_time = time.time()

# Initialize webcam
cap = cv2.VideoCapture(0)

# Screen resolution for game window
screen_res = (1280, 720)

# Load images with relative paths
script_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script directory

bg_image_path = os.path.join(script_dir, "bgimage.jpg")
balloon_img_path = os.path.join(script_dir, "balloon.png")

bg_image = cv2.imread(bg_image_path)
balloon_img = cv2.imread(balloon_img_path, cv2.IMREAD_UNCHANGED)

if bg_image is None or balloon_img is None:
    print("Error: Background or balloon image not found. Make sure both images are in the same folder as this script.")
    exit()

bg_image = cv2.resize(bg_image, screen_res)  # Resize to screen resolution
balloon_img = cv2.resize(balloon_img, (175, 175))  # Resize balloon image

# Function to detect pinch gesture
def is_pinch(landmarks):
    index_finger = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb = landmarks[mp_hands.HandLandmark.THUMB_TIP]

    # Calculate Euclidean distance
    distance = np.sqrt((index_finger.x - thumb.x) ** 2 + (index_finger.y - thumb.y) ** 2)

    return distance < 0.08  # Adjust threshold if needed

# Balloons list
balloons = [{'x': random.randint(balloon_radius, screen_res[0] - balloon_radius), 
             'y': screen_res[1], 
             'speed': random.randint(3, 7)}]

# Function to overlay balloon image on the game frame
def overlay_image(background, overlay, position):
    h, w = overlay.shape[:2]

    if position[1] + h <= background.shape[0] and position[0] + w <= background.shape[1]:
        alpha_mask = overlay[:, :, 3] / 255.0
        balloon_rgb = overlay[:, :, :3]
        roi = background[position[1]:position[1] + h, position[0]:position[0] + w]

        for c in range(0, 3):
            roi[:, :, c] = (alpha_mask * balloon_rgb[:, :, c] + (1 - alpha_mask) * roi[:, :, c])

        background[position[1]:position[1] + h, position[0]:position[0] + w] = roi

    return background

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip frame horizontally for natural hand movement
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Use the background image
    game_frame = bg_image.copy()

    # Move balloons up
    for balloon in balloons:
        balloon['y'] -= balloon['speed']
        if balloon['y'] < 0:
            balloon['y'] = screen_res[1]
            balloon['x'] = random.randint(balloon_radius, screen_res[0] - balloon_radius)
            balloon['speed'] = random.randint(3, 7)

    # Draw balloons on the game window
    for balloon in balloons:
        balloon_position = (balloon['x'], balloon['y'])
        game_frame = overlay_image(game_frame, balloon_img, balloon_position)

    # Hand tracking
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(game_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            index_x = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * screen_res[0])
            index_y = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * screen_res[1])

            if is_pinch(hand_landmarks.landmark):
                for balloon in balloons:
                    balloon_position = (balloon['x'], balloon['y'])
                    if abs(balloon_position[0] - index_x) < balloon_radius and abs(balloon_position[1] - index_y) < balloon_radius:
                        score += 1
                        balloons.remove(balloon)
                        balloons.append({'x': random.randint(balloon_radius, screen_res[0] - balloon_radius),
                                         'y': screen_res[1],
                                         'speed': random.randint(3, 7)})

    # Display score
    cv2.putText(game_frame, f"Score: {score}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Display timer
    elapsed_time = int(time.time() - start_time)
    remaining_time = game_duration - elapsed_time
    cv2.putText(game_frame, f"Time: {remaining_time}s", (screen_res[0] // 2 - 50, screen_res[1] // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Check game time
    if elapsed_time > game_duration:
        cv2.putText(game_frame, f"Game Over! Final Score: {score}", (screen_res[0] // 4, screen_res[1] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Balloon Popping Game", game_frame)
        cv2.waitKey(3000)
        break

    cv2.imshow("Balloon Popping Game", game_frame)

    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

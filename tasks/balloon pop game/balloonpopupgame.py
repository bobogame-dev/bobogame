import cv2
import random
import mediapipe as mp
import numpy as np
import time

# Set up MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Game settings
balloon_radius = 40
score = 0
game_duration = 60  # Game time in seconds
start_time = time.time()

# Initialize webcam
cap = cv2.VideoCapture(0)

# Screen resolution for game window
screen_res = (1280, 720)

# Function to detect pinch gesture
def is_pinch(landmarks):
    index_finger = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb = landmarks[mp_hands.HandLandmark.THUMB_TIP]

    # Calculate Euclidean distance
    distance = ((index_finger.x - thumb.x) ** 2 + (index_finger.y - thumb.y) ** 2) ** 0.5

    return distance < 0.08  # Adjust threshold if needed

# Balloons list
balloons = [{'x': random.randint(balloon_radius, screen_res[0] - balloon_radius), 
             'y': screen_res[1], 
             'color': (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
             'speed': random.randint(3, 7)}]

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip frame horizontally for natural hand movement
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Create a blue background for the game window
    game_frame = np.zeros((screen_res[1], screen_res[0], 3), dtype=np.uint8)
    game_frame[:] = (255, 0, 0)  # Blue background

    # Move balloons up
    for balloon in balloons:
        balloon['y'] -= balloon['speed']
        if balloon['y'] < 0:
            balloon['y'] = screen_res[1]
            balloon['x'] = random.randint(balloon_radius, screen_res[0] - balloon_radius)
            balloon['color'] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            balloon['speed'] = random.randint(3, 7)

    # Draw realistic balloons on the game window
    for balloon in balloons:
        center = (balloon['x'], balloon['y'])
        axes = (balloon_radius, int(balloon_radius * 1.5))  # Oval shape
        cv2.ellipse(game_frame, center, axes, 0, 0, 360, balloon['color'], -1)

        # Balloon string (knot)
        cv2.line(game_frame, (balloon['x'], balloon['y'] + int(balloon_radius * 1.5)), 
                 (balloon['x'], balloon['y'] + int(balloon_radius * 1.8)), (0, 0, 0), 2)

    # Hand tracking
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks
            mp_drawing.draw_landmarks(game_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Convert hand tracking coordinates to game coordinates
            index_x = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * screen_res[0])
            index_y = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * screen_res[1])

            if is_pinch(hand_landmarks.landmark):
                for balloon in balloons:
                    if abs(balloon['x'] - index_x) < balloon_radius and abs(balloon['y'] - index_y) < balloon_radius:
                        score += 1
                        balloons.remove(balloon)
                        balloons.append({'x': random.randint(balloon_radius, screen_res[0] - balloon_radius),
                                         'y': screen_res[1],
                                         'color': (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
                                         'speed': random.randint(3, 7)})

    # Display score
    cv2.putText(game_frame, f"Score: {score}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Check game time
    if time.time() - start_time > game_duration:
        cv2.putText(game_frame, f"Game Over! Final Score: {score}", (screen_res[0] // 4, screen_res[1] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Balloon Popping Game", game_frame)
        cv2.waitKey(3000)
        break

    # Show only one window (game window now includes hand tracking)
    cv2.imshow("Balloon Popping Game", game_frame)

    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

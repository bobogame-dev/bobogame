import cv2
import mediapipe as mp
import time
import socket
import json

cap = cv2.VideoCapture(0)

mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

pTime = 0
cTime = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
serverAddressPort = ("127.0.0.1", 5052)

# Function to detect if all fingers are extended (STOP gesture)
def fingers_extended(hand_landmarks):
    tip_ids = [4, 8, 12, 16, 20]
    fingers = []
    
    for tip_id in tip_ids:
        if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
            fingers.append(1)  # Finger is up
        else:
            fingers.append(0)  # Finger is down
    
    return sum(fingers) == 5  # True if all fingers are extended

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    all_hands_data = []
    send_stop = False

    if results.multi_hand_landmarks:
        for hand_idx, handLms in enumerate(results.multi_hand_landmarks):
            if fingers_extended(handLms):
                send_stop = True  # If any hand shows STOP, send the STOP signal
            
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                if id in [4, 8, 12, 16, 20]:
                    cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)
            
            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

            landmarks = []
            for id, lm in enumerate(handLms.landmark):
                landmarks.append({'x': lm.x, 'y': lm.y, 'z': lm.z})

            all_hands_data.append({'hand_index': hand_idx, 'landmarks': landmarks})

    # Prepare the data to send
    if send_stop:
        data = json.dumps({'command': 'STOP'})
    else:
        data = json.dumps({'hands': all_hands_data})
    
    # Send data to server
    print("Sending data:", data)  # For debugging
    sock.sendto(data.encode(), serverAddressPort)

    # Calculate FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    # Display FPS
    cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
    cv2.imshow("Image", img)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
sock.close()
cv2.destroyAllWindows()

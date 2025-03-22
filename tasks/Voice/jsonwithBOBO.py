import argparse
import queue
import sys
import json
import time
from PySide6.QtGui import QBrush,QGuiApplication, QPalette, QPixmap
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtCore import QThread, QTimer, Qt, Signal, Slot, QSize
import random

#Queue to store audio data from sounddevice
q = queue.Queue()

#To convert input text to integer or String
def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text

#Callback function for sounddevice to capture audio input
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

#To load words dictionary from words.jason
with open("words.json", "r") as f:
    words_dict = json.load(f)

#Load players data from player.jason or creat error handeling
try:
    with open("player.json", "r") as f:
        player_data = json.load(f)
except FileNotFoundError:
    player_data = {
        "communication-level": 1,
        "communication-tasks": 0,
    }

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--device", type=int_or_str, help="input device")
parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument("-m", "--model", type=str, help="language model")
args = parser.parse_args()

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        args.samplerate = int(device_info["default_samplerate"])

    #Load the Vosk model
    model = Model(lang=args.model if args.model else "en-in")

    #GameThread class to handle the game logic in a separate thread
    class GameThread(QThread):
        update_word = Signal(str)
        update_result = Signal(str)
        update_score = Signal(int, int)
        update_level = Signal(str)
        game_finished = Signal(str)
        level_finished = Signal(int, bool)

        def __init__(self, parent=None):
            super().__init__(parent)

        def run(self):
            #open audio input Stream
            with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device,
                                    dtype="int16", channels=1, callback=callback):

                difficulty_levels = ["Easy", "Medium", "Hard"]
                current_level = player_data["communication-level"] - 1

                #Validate the loaded Communication Level
                if current_level < 0 or current_level >= len(difficulty_levels):
                    print("Invalid communication level in player.json. Resetting to 0.")
                    current_level = 0
                    player_data["communication-level"] = 1

                correct_attempts = 0
                words_per_level = 3

                #Main Game Loop
                while True:
                    words_list = words_dict[difficulty_levels[current_level]]
                    random.shuffle(words_list)  # Shuffle words list for randomness

                    #Get Words for the Current Level 
                    for i in range(words_per_level):
                        word_to_match = words_list[i % len(words_list)]
                        self.update_word.emit(f"Say the word: '{word_to_match}'")

                        #Initialize Vosk Recognizer
                        rec = KaldiRecognizer(model, args.samplerate)
                        start_time = time.time()

                        #Set time to 1 minute for one word
                        while time.time() - start_time < 60:
                            data = q.get()
                            if rec.AcceptWaveform(data):
                                result = rec.Result()
                                spoken_word = result.split(':')[-1].strip(' "}\n.,!?').lower()

                                #Check the spoken word matches the target word
                                if spoken_word == word_to_match.lower():
                                    self.update_result.emit("Correct word spoken!")
                                    correct_attempts += 1
                                    q.queue.clear()
                                    break
                                else:
                                    self.update_result.emit("Try again...")
                                    q.queue.clear()
                            q.queue.clear()

                    #Level Progression Logic
                    if correct_attempts >= 3 and current_level < 2:
                        current_level += 1
                        player_data["communication-level"] += 1
                        player_data["communication-tasks"] += 1
                        correct_attempts = 0
                        self.update_level.emit("Level Up!")
                        self.level_finished.emit(current_level, True)
                        return
                    elif correct_attempts < 3 and current_level > 0:
                        current_level -= 1
                        player_data["communication-level"] -= 1
                        player_data["communication-tasks"] += 1 #increment task count when downgrading
                        correct_attempts = 0
                        self.update_level.emit(f"Level Down!")
                        self.level_finished.emit(current_level, False)
                        return
                    elif correct_attempts < 3 and current_level == 0:
                        player_data["communication-tasks"] += 1 #increment task count when staying at the lowest level
                        self.level_finished.emit(current_level, False)
                        return

                    #Game win Condition
                    if current_level == 2 and correct_attempts == 3:
                        player_data["communication-tasks"] += 1
                        self.game_finished.emit("Congratulations! You Won the Game !")
                        break
                    correct_attempts = 0

                #Save Player Data to player.jason
                with open("player.json", "w") as f:
                    json.dump(player_data, f, indent=4)

    #GameWindo Class to handle the GUI
    class GameWindow(QWidget):
        def __init__(self):
            super().__init__()

            #Remove title bar and frame
            self.setWindowFlags(Qt.FramelessWindowHint)
            
            #Set background image
            self.set_scaled_background_image("background.jpg")

        #Initialize Labels

            #Label For Say the word 
            self.word_label = QLabel()
            self.word_label.setAlignment(Qt.AlignCenter)  # Center the text
            self.word_label.setStyleSheet("color: white; font-size: 90px; font-weight: bold;") #set styles
            
            #Label For Try Again
            self.result_label = QLabel()
            self.result_label.setAlignment(Qt.AlignCenter)  # Center result label
            self.result_label.setStyleSheet("color: white; font-size: 60px; font-weight: bold;") #set styles

            #Label For Communication Level
            self.score_label = QLabel(f"Communication Level: {player_data['communication-level']}")
            self.score_label.setAlignment(Qt.AlignCenter) # Center score label
            self.score_label.setStyleSheet("color: white; font-size: 50px; font-weight: bold;") #set styles

            #Label For Communication Tasks
            self.attempts_label = QLabel(f"Communication Tasks: {player_data['communication-tasks']}")
            self.attempts_label.setAlignment(Qt.AlignCenter) # Center attempts label
            self.attempts_label.setStyleSheet("color: white; font-size: 50px; font-weight: bold;") #set styles

            #Label For Level Up and Level Down
            self.level_label = QLabel()
            self.level_label.setAlignment(Qt.AlignCenter) # Center level label
            self.level_label.setStyleSheet("color: white; font-size: 50px; font-weight: bold;") #set styles

            self.image_label = QLabel()  # Add an image label
            self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # set image label to expand

            #Layout Setup
            layout = QVBoxLayout()
            layout.setSpacing(0) # Remove spacing between widgets
            layout.addWidget(self.word_label)
            layout.addWidget(self.image_label) # add the image label to the layout under the word label.
            layout.addWidget(self.result_label)
            layout.addWidget(self.score_label)
            layout.addWidget(self.attempts_label)
            layout.addWidget(self.level_label)
            self.setLayout(layout)

            # Get the screen geometry and set the window size
            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry() # or screen.geometry()
            self.setGeometry(screen_geometry)

            #Start the Game
            self.start_game()

        #Set the Background Image
        def set_scaled_background_image(self, image_path):
            """Sets the background image of the window, scaled to fit."""
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Get the screen size
                screen = QGuiApplication.primaryScreen()
                screen_geometry = screen.availableGeometry()
                window_size = screen_geometry.size()

                # Scale the pixmap to the window size
                scaled_pixmap = pixmap.scaled(window_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                palette = self.palette()
                palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
                self.setPalette(palette)
                self.setAutoFillBackground(True)
            else:
                print(f"Error: Could not load background image from {image_path}")

        def start_game(self):
            """
            Starts the game by initializing and running the GameThread.
            Connects the GameThread signals to the GameWindow slots for UI updates.
            """
            self.game_thread = GameThread()
            self.game_thread.update_word.connect(self.update_word)
            self.game_thread.update_result.connect(self.update_result)
            self.game_thread.update_score.connect(self.update_score)
            self.game_thread.update_level.connect(self.update_level)
            self.game_thread.game_finished.connect(self.game_finished)
            self.game_thread.level_finished.connect(self.level_finished)
            self.game_thread.start()

        #Update the word label and display the valid image
        @Slot(str) 
        def update_word(self, word):
            self.word_label.setText(word)
            self.display_image(word.split("'")[1]) #extract the word from the string.
            
        #Update the result label with correct message
        @Slot(str)
        def update_result(self, result):
            self.result_label.setText(result)
            
        #Update the Player communication level and Communication Tasks 
        @Slot(int, int)
        def update_score(self, score, attempts):
            self.score_label.setText(f"Communication Level: {player_data['communication-level']}")
            self.attempts_label.setText(f"Communication Tasks: {player_data['communication-tasks']}")

        #Update the level up Label message ("Level up")
        @Slot(str)
        def update_level(self, level):
            self.level_label.setText(level)

        #Display the Level Finish message and clos the window after 2 seconds
        @Slot(str)
        def game_finished(self, message):
            self.result_label.setText(message)
            self.game_thread.quit()
            # Add this line to close the window
            QTimer.singleShot(3000, self.close)

        #Display the level finish message according to the level increased or dicreased
        @Slot(int, bool)
        def level_finished(self, level, level_change):
            if level_change:
                if level == 1:
                    self.result_label.setText("Congratulations! You won Level 1!")
                elif level == 2:
                    self.result_label.setText("Congratulations! You won Level 2!")
            else:
                
                self.result_label.setText("Don't give up! You can do it.")

            with open("player.json", "w") as f: #open player.jason file for write
                player_data["communication-level"] = level + 1 #Update the player Communication level by 1
                json.dump(player_data, f, indent=4) #Save the updated player data to player.json
            
            #Quit the GameThread
            self.game_thread.quit()
            
            # Close the window after 3 seconds
            QTimer.singleShot(3000, self.close)

        #Display the image according to the word
        def display_image(self, word):
            image_path = f"images/{word.lower()}.png" #Construct the image path (JPG only)
            pixmap = QPixmap(image_path) #Load the image
            if pixmap.isNull(): #if JPG image dosen't exist
                self.image_label.clear()# Clear the image label
                return #Exit the Function
                
            fixed_size = QSize(200, 200) # Define a fixed size
            scaled_pixmap = pixmap.scaled(fixed_size, Qt.KeepAspectRatio, Qt.SmoothTransformation) #Scale the Image
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setAlignment(Qt.AlignCenter) #Align the image to the Center
    
    app = QApplication(sys.argv) # Create a QApplication instance, which is necessary for any Qt GUI application.
    window = GameWindow()  # Create an instance of the GameWindow class
    window.show() # Display the GameWindow on the screen.
    sys.exit(app.exec()) #Makes the application responsive to user interactions and handles events.

except KeyboardInterrupt:
    print("Program interrupted by user.") # Print a message when Ctrl+C is pressed.
    sys.exit
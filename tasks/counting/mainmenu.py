import pygame
import json
import os

pygame.init()

data_file = "player_info.json"

def load_player_data():
    try:
        with open(data_file, "r") as file:
            data = json.load(file)
            return data.get("playerLevel", 1)  # Default to level 1 if "playerLevel" doesn't exist
    except FileNotFoundError:
        # If the file doesn't exist, start from level 1
        return 1

def save_player_data(level):
    with open(data_file, "w") as file:
        json.dump({"playerLevel": level}, file)

def update_player_level(current_level):
    new_level = current_level
    if current_level < 5:
        new_level += 1
    return new_level

# Load images
try:
    tree1 = pygame.image.load('tree.png')
    stree1 = pygame.transform.rotozoom(tree1, 0, 0.3)
    mtree1 = pygame.transform.rotozoom(tree1, 0, 0.5)
    tree2 = pygame.image.load('tree2.png')
    stree2 = pygame.transform.rotozoom(tree2, 0, 0.3)
    mtree2 = pygame.transform.rotozoom(tree2, 0, 0.5)
    student1 = pygame.image.load('student2.png')
    student1 = pygame.transform.rotozoom(student1, 0, 0.3)
    mstudent1 = pygame.transform.rotozoom(student1, 0, 0.7)
    student2 = pygame.image.load('student.png')
    student2 = pygame.transform.rotozoom(student2, 0, 0.2)
    student3 = pygame.image.load('student3.png')
    student3 = pygame.transform.rotozoom(student3, 0, 0.6)    
    student4 = pygame.image.load('student4.png')
    student4 = pygame.transform.rotozoom(student4, 0, 0.15) 
    student5 = pygame.image.load('student5.png')
    student5 = pygame.transform.rotozoom(student5, 0, 0.25)
    student6 = pygame.image.load('student6.png')
    student6 = pygame.transform.rotozoom(student6, 0, 0.2)
    student7 = pygame.image.load('student7.png')
    student7 = pygame.transform.rotozoom(student7, 0, 0.3)
    butterfly = pygame.image.load('buterflu2.png')
    butterfly = pygame.transform.rotozoom(butterfly, 0, 0.2)
    butterfly2 = pygame.image.load('buterfly2.png')
    butterfly2 = pygame.transform.rotozoom(butterfly2, 0, 0.2)
    butterfly3 = pygame.image.load('buterfly3.png')
    butterfly3 = pygame.transform.rotozoom(butterfly2, 0, 0.2)
    flower = pygame.image.load('flower.png')
    flower = pygame.transform.rotozoom(flower, 0, 0.1)
    flower2 = pygame.image.load('flower2.jpg')
    flower2 = pygame.transform.rotozoom(flower2, 0, 0.2)
    flower3 = pygame.image.load('flower3.png')
    flower3 = pygame.transform.rotozoom(flower3, 0, 0.1)
    bird = pygame.image.load('bird.png')
    bird = pygame.transform.rotozoom(bird, 0, 0.2)
    bird2 = pygame.image.load('bird2.png')
    bird2 = pygame.transform.rotozoom(bird2, 0, 0.2)
    
except pygame.error as e:
    print(f"Error loading image: {e}")
    # Fallback surfaces
    tree1 = pygame.Surface((50, 50))
    stree1 = tree1
    tree2 = pygame.Surface((50, 50))
    stree2 = tree2
    student1 = pygame.Surface((50, 50))
    student2 = pygame.Surface((50, 50))
    butterfly = pygame.Surface((50, 50))
    flower = pygame.Surface((50, 50))
    bird = pygame.Surface((50, 50))
    print(f"Error loading button images: {e}")
    # Fallback surfaces
    continue_b = pygame.Surface((200, 50))
    exit_b = pygame.Surface((200, 50))
    
# Input rectangles
tree_rectangle = pygame.Rect(600, 0, 200, 50)
student_rectangle = pygame.Rect(600, 50, 200, 50)
butterfly_rectangle = pygame.Rect(600, 100, 200, 50)
flower_rectangle = pygame.Rect(600, 150, 200, 50)
bird_rectangle = pygame.Rect(600, 200, 200, 50)

WHITE = (255, 255, 255)
LIGHTGRAY = (200, 200, 200)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
background = BLACK


color_active = WHITE
color_passive = LIGHTGRAY
tree_color = color_passive
student_color = color_passive
butterfly_color = color_passive
flower_color = color_passive
bird_color = color_passive


# Initialize feedback variables
feedback_trees = "Incorrect!"
feedback_students = "Incorrect!"
feedback_butterflies = "Incorrect!"
feedback_flowers = "Incorrect!"
feedback_birds = "Incorrect!"
# Correct answers
correct_trees = 0
correct_students = 0
correct_butterflies = 0
correct_vehicles = 0
correct_flowers = 0
correct_birds = 0

# Screen setup
screen_width = 1250
screen_height = 700
screen = pygame.display.set_mode((screen_width, screen_height))

# Font setup
baseFont = pygame.font.Font(None, 45)
no_trees = '|'
no_student = '|'
no_butterflies = '|'
no_flowers = '|'
no_birds = '|'


# Define button rectangles
continue_rect = pygame.Rect(500, 400, 200, 50)  # (x, y, width, height)
exit_rect = pygame.Rect(500, 480, 200, 50)  

label_tree = baseFont.render("Number of Trees: ", True, (200, 20, 120))
label_student = baseFont.render("Number of Students: ", True, (200, 20, 120))
label_butterflies = baseFont.render("Number of Butterflies: ", True, (200, 20, 120))
label_vehicle = baseFont.render("Number of Vehicles: ", True, (200, 20, 120))
label_flowers = baseFont.render("Number of Flowers: ", True, (200, 20, 120))
label_birds = baseFont.render("Number of Birds: ", True, (200, 20, 120))
continue_b = baseFont.render("CONTINUE ", True, (100, 0, 200))
exit_b = baseFont.render("EXIT ", True, (100, 0, 200))
# Load background image
try:
    backgroundImage = pygame.image.load('background.jpg')
    backgroundImage = pygame.transform.scale(backgroundImage, (screen_width, screen_height))
except pygame.error as e:
    print(f"Error loading background image: {e}")
    backgroundImage = pygame.Surface((screen_width, screen_height))
    backgroundImage.fill(BLACK)

# Game over flag
game_over = False

# Current level
current_level = load_player_data()

def update_game():
    global correct_trees, correct_students, correct_butterflies, correct_vehicles, correct_flowers, correct_birds
    if current_level == 1:
        correct_trees = 5
        correct_students = 2
        
    elif current_level == 2:
        correct_trees = 7
        correct_students = 3
        correct_butterflies = 2
        
    elif current_level == 3:
        correct_trees = 10
        correct_students = 5
        correct_butterflies = 4
        
    elif current_level == 4:
        correct_trees = 11
        correct_students = 7
        correct_butterflies = 6
        correct_flowers = 4
        
    elif current_level == 5:
        correct_trees = 12
        correct_students = 8
        correct_butterflies = 7
        correct_flowers = 5
        correct_birds = 2
        
def reset_game_state():
    global no_trees, no_student, no_butterflies, no_vehicles, no_flowers, no_birds
    global feedback_trees, feedback_students, feedback_butterflies, feedback_vehicles, feedback_flowers, feedback_birds
    no_trees = '|'
    no_student = '|'
    no_butterflies = '|'
    no_vehicles = '|'
    no_flowers = '|'
    no_birds = '|'
    feedback_trees = "Incorrect!"
    feedback_students = "Incorrect!"
    feedback_butterflies = "Incorrect!"
    feedback_vehicles = "Incorrect!"
    feedback_flowers = "Incorrect!"
    feedback_birds = "Incorrect!"
    
# # Button positions (X, Y)
# continue_button_pos = (500, 400)  # X = 500, Y = 400
# exit_button_pos = (500, 480)      # X = 500, Y = 480

# Button rectangles (X, Y, width, height)
continue_button = pygame.Rect(500,400, 200, 70)
exit_button = pygame.Rect(500,480, 200, 70)
    
run = True
while run:
    # Clear the screen
    screen.fill(background)
    screen.blit(backgroundImage, (0, 0))
    current_level = load_player_data()
    print(f"Starting game at level: {current_level}")  # Debugging line
    # Update game state based on current level
    update_game()
    # current_level = load_player_data()
    # print(f"Starting game at level: {current_level}")  # Debugging line
    # Draw input fields and labels
    screen.blit(label_tree, (320, 10))
    screen.blit(label_student, (260, 60))
    if current_level >= 2:
        screen.blit(label_butterflies, (240, 110))
    if current_level >= 4:
        screen.blit(label_flowers, (280, 160))
    if current_level >= 5:
        screen.blit(label_birds, (320, 210))

    pygame.draw.rect(screen, tree_color, tree_rectangle, 5)
    pygame.draw.rect(screen, student_color, student_rectangle, 5)
    if current_level >= 2:
        pygame.draw.rect(screen, butterfly_color, butterfly_rectangle, 5)       
    if current_level >= 4:
        pygame.draw.rect(screen, flower_color, flower_rectangle, 5)
    if current_level >= 5:
        pygame.draw.rect(screen, bird_color, bird_rectangle, 5)

    # Render text for input fields
    textSurface = baseFont.render(no_trees, True, (250, 50, 100))
    screen.blit(textSurface, (tree_rectangle.x + 5, tree_rectangle.y + 5))
    textSurface = baseFont.render(no_student, True, (250, 50, 100))
    screen.blit(textSurface, (student_rectangle.x + 5, student_rectangle.y + 5))
    if current_level >= 2:
        textSurface = baseFont.render(no_butterflies, True, (250, 50, 100))
        screen.blit(textSurface, (butterfly_rectangle.x + 5, butterfly_rectangle.y + 5))
    if current_level >= 4:
        textSurface = baseFont.render(no_flowers, True, (250, 50, 100))
        screen.blit(textSurface, (flower_rectangle.x + 5, flower_rectangle.y + 5))
    if current_level >= 5:
        textSurface = baseFont.render(no_birds, True, (250, 50, 100))
        screen.blit(textSurface, (bird_rectangle.x + 5, bird_rectangle.y + 5))

    # Draw other elements (trees, students, butterflies, etc.)
    screen.blit(tree1, (50, 300))    #adding objects to the level one 
    screen.blit(stree2, (260, 430))
    screen.blit(tree2, (350, 280))
    screen.blit(student1, (490, 410))
    screen.blit(student2, (660, 450))
    screen.blit(tree1, (750, 300))
    screen.blit(stree1, (600, 440))
    if current_level >= 2: #adding objects to the level two
        screen.blit(stree1,(70,430))
        screen.blit(stree2,(190,430))
        screen.blit(student3,(330,510))
        screen.blit(butterfly, (890, 250))
        screen.blit(butterfly2,(900,100))
        
    if current_level >= 3:#adding objects to the level three
        screen.blit(tree2,(1050,280))
        screen.blit(tree2,(900,280))
        screen.blit(mtree2,(-2,390))
        screen.blit(student7,(450,480))
        screen.blit(student4,(120,445))
        screen.blit(butterfly2,(800,100))
        screen.blit(butterfly2,(1000,100))
        
        
    if current_level >= 4:#adding objects to the level four
        screen.blit(mtree1,(890,400))
        screen.blit(student6,(1040,400))
        screen.blit(mstudent1,(10,500))
        screen.blit(flower, (900, 500))
        screen.blit(flower, (830, 490))
        screen.blit(flower2, (180,520))
        screen.blit(flower3, (250, 520))
        screen.blit(butterfly2,(600,270))
        screen.blit(butterfly,(300,270))
        
    if current_level >= 5:#adding objects to the level five
        screen.blit(mtree2,(320,390))
        screen.blit(student5,(700,400))
        screen.blit(butterfly,(950,450))
        screen.blit(butterfly2,(100,200))
        screen.blit(bird, (1100, 300))
        screen.blit(bird2, (100, 100))
        screen.blit(flower3, (940, 500))

    # Check if all answers are correct
    if (feedback_trees == "Correct!" and feedback_students == "Correct!" and
        (current_level < 2 or feedback_butterflies == "Correct!") and
        (current_level < 4 or feedback_flowers == "Correct!") and
        (current_level < 5 or feedback_birds == "Correct!")):
        game_over = True
        
    
    if game_over:

        game_over_surface = baseFont.render("Game Over! You Win!", True, GREEN)
        screen.blit(game_over_surface, (screen_width // 2 - 150, screen_height // 2))
        
        # # Draw button rectangles
        pygame.draw.rect(screen, (255, 0, 0), continue_rect)  # Red outline
        pygame.draw.rect(screen, (255, 0, 0), exit_rect)  # Red outline
        # Draw button text
        screen.blit(continue_b, (continue_rect.x +25 , continue_rect.y + 10))
        screen.blit(exit_b, (exit_rect.x + 60, exit_rect.y + 10))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_over:
                # Check if the continue button is clicked
                if continue_button.collidepoint(event.pos):
                    print("Continue button clicked")  # Debugging
                    current_level = update_player_level(current_level)
                    save_player_data(current_level)
                    game_over = False
                    reset_game_state()
                # Check if the exit button is clicked
                elif exit_button.collidepoint(event.pos):
                    print("Exit button clicked")  # Debugging
                    save_player_data(current_level)
                    run = False
            # Check which rectangle is clicked
            if tree_rectangle.collidepoint(event.pos):
                active_field = 'tree'
                tree_color = color_active
                student_color = color_passive
                butterfly_color = color_passive
                vehicle_color = color_passive
                flower_color = color_passive
                bird_color = color_passive
            elif student_rectangle.collidepoint(event.pos):
                active_field = 'student'
                student_color = color_active
                tree_color = color_passive
                butterfly_color = color_passive
                vehicle_color = color_passive
                flower_color = color_passive
                bird_color = color_passive
            elif butterfly_rectangle.collidepoint(event.pos) and current_level >= 2:
                active_field = 'butterfly'
                butterfly_color = color_active
                tree_color = color_passive
                student_color = color_passive
                vehicle_color = color_passive
                flower_color = color_passive
                bird_color = color_passive
            elif flower_rectangle.collidepoint(event.pos) and current_level >= 4:
                active_field = 'flower'
                flower_color = color_active
                tree_color = color_passive
                student_color = color_passive
                butterfly_color = color_passive
                vehicle_color = color_passive
                bird_color = color_passive
            elif bird_rectangle.collidepoint(event.pos) and current_level >= 5:
                active_field = 'bird'
                bird_color = color_active
                tree_color = color_passive
                student_color = color_passive
                butterfly_color = color_passive
                vehicle_color = color_passive
                flower_color = color_passive
            else:
                active_field = None
                tree_color = color_passive
                student_color = color_passive
                butterfly_color = color_passive
                vehicle_color = color_passive
                flower_color = color_passive
                bird_color = color_passive
            
                
        if event.type == pygame.KEYDOWN:
            if active_field == 'tree':
                if event.key == pygame.K_BACKSPACE:
                    no_trees = no_trees[:-1]  # Remove the last character
                else:
                    no_trees += event.unicode  # Add the typed character
                # Validate input for trees
                try:
                    if int(no_trees.replace('|', '')) == correct_trees:
                        feedback_trees = "Correct!"
                    else:
                        feedback_trees = "Incorrect!"
                except ValueError:
                    feedback_trees = "Invalid input!"
            elif active_field == 'student':
                if event.key == pygame.K_BACKSPACE:
                    no_student = no_student[:-1]  # Remove the last character
                else:
                    no_student += event.unicode  # Add the typed character
                # Validate input for students
                try:
                    if int(no_student.replace('|', '')) == correct_students:
                        feedback_students = "Correct!"
                    else:
                        feedback_students = "Incorrect!"
                except ValueError:
                    feedback_students = "Invalid input!"
            elif active_field == 'butterfly' and current_level >= 2:
                if event.key == pygame.K_BACKSPACE:
                    no_butterflies = no_butterflies[:-1]
                else:
                    no_butterflies += event.unicode
                try:
                    if int(no_butterflies.replace('|', '')) == correct_butterflies:
                        feedback_butterflies = "Correct!"
                    else:
                        feedback_butterflies = "Incorrect!"
                except ValueError:
                    feedback_butterflies = "Invalid input!"
            elif active_field == 'flower' and current_level >= 4:
                if event.key == pygame.K_BACKSPACE:
                    no_flowers = no_flowers[:-1]
                else:
                    no_flowers += event.unicode
                try:
                    if int(no_flowers.replace('|', '')) == correct_flowers:
                        feedback_flowers = "Correct!"
                    else:
                        feedback_flowers = "Incorrect!"
                except ValueError:
                    feedback_flowers = "Invalid input!"
            elif active_field == 'bird' and current_level >= 5:
                if event.key == pygame.K_BACKSPACE:
                    no_birds = no_birds[:-1]
                else:
                    no_birds += event.unicode
                try:
                    if int(no_birds.replace('|', '')) == correct_birds:
                        feedback_birds = "Correct!"
                    else:
                        feedback_birds = "Incorrect!"
                except ValueError:
                    feedback_birds = "Invalid input!"

        if event.type == pygame.QUIT:
            run = False  # Exit the game loop

    # Update the display
    pygame.display.flip()
pygame.quit()
# =================================================================================================
# Contributing Authors:	    Ty Gordon, Caleb Fields, Abdallah Sher
# Email Addresses:          wtgo223@uky.edu, cwfi224@uky.edu, afsh230@uky.edu
# Date:                     11/17/2023
# Purpose:                  To implement the client and game logic
# Misc:                     N/A
# =================================================================================================

import pygame
import tkinter as tk
import sys
import socket
import json # For packing and sending
import os # For file management
import time # For sleep

from assets.code.helperCode import *

# This is the main game loop.  For the most part, you will not need to modify this.  The sections
# where you should add to the code are marked.  Feel free to change any part of this project
# to suit your needs.
# Player1 is the left player, if it false then the player is assumed to be the right.
# Modified by Ty Gordon, Caleb Fields, Abdallah Sher
def playGame(screenWidth:int, screenHeight:int, playerPaddle:str, client:socket.socket) -> None:
    # Pygame inits
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.init()

    # Constants
    WHITE = (255,255,255)
    clock = pygame.time.Clock()
    scoreFont = pygame.font.Font("./assets/fonts/pong-score.ttf", 32)
    winFont = pygame.font.Font("./assets/fonts/visitor.ttf", 48)
    pointSound = pygame.mixer.Sound("./assets/sounds/point.wav")
    bounceSound = pygame.mixer.Sound("./assets/sounds/bounce.wav")

    # Display objects
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    winMessage = pygame.Rect(0,0,0,0)
    topWall = pygame.Rect(-10,0,screenWidth+20, 10)
    bottomWall = pygame.Rect(-10, screenHeight-10, screenWidth+20, 10)
    centerLine = []
    for i in range(0, screenHeight, 10):
        centerLine.append(pygame.Rect((screenWidth/2)-5,i,5,5))

    # Paddle properties and init
    paddleHeight = 50
    paddleWidth = 10
    paddleStartPosY = (screenHeight/2)-(paddleHeight/2)
    leftPaddle = Paddle(pygame.Rect(10,paddleStartPosY, paddleWidth, paddleHeight))
    rightPaddle = Paddle(pygame.Rect(screenWidth-20, paddleStartPosY, paddleWidth, paddleHeight))

    ball = Ball(pygame.Rect(screenWidth/2, screenHeight/2, 5, 5), -5, 0)

    if playerPaddle == "left":
        opponentPaddleObj = rightPaddle
        playerPaddleObj = leftPaddle
    else:
        opponentPaddleObj = leftPaddle
        playerPaddleObj = rightPaddle

    lScore = 0
    rScore = 0

    sync = 0
    ballCounter = 0

    playing = True
    sendPlayAgain = False

    while True:
        # Wiping the screen
        screen.fill((0,0,0))

        # Getting keypress events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    playerPaddleObj.moving = "down"

                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    playerPaddleObj.moving = "up"

            elif event.type == pygame.KEYUP:
                playerPaddleObj.moving = ""

        # Update the player paddle's location on the screen
        if playerPaddleObj.moving == "down":
            if playerPaddleObj.rect.bottomleft[1] < screenHeight-10:
                playerPaddleObj.rect.y += playerPaddleObj.speed
        elif playerPaddleObj.moving == "up":
            if playerPaddleObj.rect.topleft[1] > 10:
                playerPaddleObj.rect.y -= playerPaddleObj.speed

        # =========================================================================================

        # If the game is over, display the win message
        if lScore > 4 or rScore > 4:
            winText = "Player 1 Wins! " if lScore > 4 else "Player 2 Wins! "
            textSurface = winFont.render(winText, False, WHITE, (0,0,0))
            textRect = textSurface.get_rect()
            textRect.center = ((screenWidth/2), screenHeight/2)
            winMessage = screen.blit(textSurface, textRect)
            pygame.display.update()
            time.sleep(5)
            pygame.display.quit()
            break
        elif ballCounter >= 1:
            # ==== Ball Logic =====================================================================
            ball.updatePos()

            # If the ball makes it past the edge of the screen, update score, etc.
            if ball.rect.x > screenWidth:
                lScore += 1
                pointSound.play()
                ball.reset(nowGoing="left")
            elif ball.rect.x < 0:
                rScore += 1
                pointSound.play()
                ball.reset(nowGoing="right")
                
            # If the ball hits a paddle
            if ball.rect.colliderect(playerPaddleObj.rect):
                bounceSound.play()
                ball.hitPaddle(playerPaddleObj.rect.center[1])
            elif ball.rect.colliderect(opponentPaddleObj.rect):
                bounceSound.play()
                ball.hitPaddle(opponentPaddleObj.rect.center[1])
                
            # If the ball hits a wall
            if ball.rect.colliderect(topWall) or ball.rect.colliderect(bottomWall):
                bounceSound.play()
                ball.hitWall()
            
            pygame.draw.rect(screen, WHITE, ball)
            # ==== End Ball Logic =================================================================

        # Drawing the dotted line in the center
        for i in centerLine:
            pygame.draw.rect(screen, WHITE, i)
        
        # Drawing the player's new location
        for paddle in [playerPaddleObj, opponentPaddleObj]:
            pygame.draw.rect(screen, WHITE, paddle)

        pygame.draw.rect(screen, WHITE, topWall)
        pygame.draw.rect(screen, WHITE, bottomWall)
        scoreRect = updateScore(lScore, rScore, screen, WHITE, scoreFont)
        pygame.display.update()
        clock.tick(60)

        # =========================================================================================
        # ============================ SERVER-CLIENT DIALOG =======================================

        # -_-_-_-_- SEND GAME STATE -_-_-_-_-
        data = {'sync': sync,   # Assemble the Json dictionary
                'paddle': [playerPaddleObj.rect.x, playerPaddleObj.rect.y],
                'ball': [ball.rect.x, ball.rect.y],
                'score': [lScore, rScore],
                }
            

        
        jsonData = json.dumps(data) # Dump the data
        client.send(jsonData.encode()) # Send the data

        # -_-_-_-_- RECIEVE GAME STATE -_-_-_-_-

        # Recieve game state from server
        received = client.recv(1024) # Recieve socket data
        data = received.decode()    # Decode socket data
        jsonData = json.loads(data) # Parse Json data

        if sync != jsonData['sync']: # If the sync variable is not equal to the sync variable from the server
            # Update the player paddle position
            if playerPaddle == "left":
                playerPaddleObj.rect.x = jsonData['left'][0]
                playerPaddleObj.rect.y = jsonData['left'][1]
            else:
                playerPaddleObj.rect.x = jsonData['right'][0]
                playerPaddleObj.rect.y = jsonData['right'][1]

        ball.rect.x = jsonData['ball'][0]   # Update the ball position
        ball.rect.y = jsonData['ball'][1]

        lScore = jsonData['score'][0]   # Update the scores
        rScore = jsonData['score'][1]

        # Update paddle positions
        if playerPaddle == "left":
            opponentPaddleObj.rect.x = jsonData['right'][0]
            opponentPaddleObj.rect.y = jsonData['right'][1]
        else:
            opponentPaddleObj.rect.x = jsonData['left'][0]
            opponentPaddleObj.rect.y = jsonData['left'][1]

        sync = jsonData['sync'] + 1 # Update the sync variable

        # DEBUG 
        print("Sync: ", jsonData['sync'])
        print("Left: ", jsonData['left'][0], " ", jsonData['left'][1])
        print("Right: ", jsonData['right'][0], " ", jsonData['right'][1])
        print("Ball: ", jsonData['ball'][0], " ", jsonData['ball'][1])

        if ballCounter < 1:
            time.sleep(1)
            ballCounter+=1

        # =========================================================================================


# This is where you will connect to the server to get the info required to call the game loop.  Mainly
# the screen width, height and player paddle (either "left" or "right")
# If you want to hard code the screen's dimensions into the code, that's fine, but you will need to know
# which client is which
# Modified by Ty Gordon, Caleb Fields, Abdallah Sher
# Purpose:      This method is fired when the join button is clicked
# Pre: The fields in the start screen have been filled
# Post: The game will be ready to be played
# Arguments:
# ip            A string holding the IP address of the server
# port          An int holding the port the server is using
# errorLabel    A tk label widget, modify it's text to display messages to the user (example below)
# app           The tk window object, needed to kill the window
# Create a socket and connect to the server
# You don't have to use SOCK_STREAM, use what you think is best
def joinServer(name:str, ip:str, port:str, errorLabel:tk.Label, app:tk.Tk) -> None:
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip, int(port)))
    client.send(name.encode())

    errorLabel.config(text="Waiting for other player...")
    errorLabel.update()

    # -_-_-_-_- Recieve preliminary data from server -_-_-_-_-
    received = client.recv(1024)
    data = received.decode()
    jsonData = json.loads(data)

    side = jsonData['side']
    screenHeight = jsonData['height']
    screenWidth = jsonData['width']
    errorLabel.config(text=f"Unable to connect to server: IP: {ip}, Port: {port}")
    errorLabel.update()     

    # Close this window and start the game with the info passed to you from the server
    app.withdraw()     # Hides the window (we'll kill it later)
    playGame(screenWidth, screenHeight, side, client)  # User will be either left or right paddle
    app.wm_deiconify()


    #app.quit()         # Kills the window

# Author: Alexander Barrera, Modified by Caleb Fields, Abdallah Sher
# Purpose: Create the starting screen for the client
# Pre: None
# Post: User should be presented with the starting screen and be able to interact with it
# This displays the opening screen, you don't need to edit this (but may if you like)
def startScreen() -> None:
    app = tk.Tk()
    app.title("Server Info")

    # Determine the current script's directory
    script_directory = os.path.dirname(__file__)

    # Define the relative path to the image file
    relative_image_path = os.path.join("assets", "images", "logo.png")
    image_path = os.path.join(script_directory, relative_image_path)

    image = tk.PhotoImage(file=image_path)

    titleLabel = tk.Label(image=image)
    titleLabel.grid(column=0, row=0, columnspan=2)

    nameLabel = tk.Label(text="Name:")
    nameLabel.grid(column=0, row=1, sticky="W", padx=8)

    nameEntry = tk.Entry(app)
    nameEntry.grid(column=1, row=1)

    ipLabel = tk.Label(text="Server IP:")
    ipLabel.grid(column=0, row=2, sticky="W", padx=8)

    ipEntry = tk.Entry(app)
    ipEntry.grid(column=1, row=2)

    portLabel = tk.Label(text="Server Port:")
    portLabel.grid(column=0, row=3, sticky="W", padx=8)

    portEntry = tk.Entry(app)
    portEntry.grid(column=1, row=3)

    errorLabel = tk.Label(text="")
    errorLabel.grid(column=0, row=5, columnspan=2)

    joinButton = tk.Button(text="Join", command=lambda: joinServer(nameEntry.get(), ipEntry.get(), portEntry.get(), errorLabel, app))
    joinButton.grid(column=0, row=4, columnspan=2)

    app.mainloop()


if __name__ == "__main__":
    startScreen()
    
    # Uncomment the line below if you want to play the game without a server to see how it should work
    # the startScreen() function should call playGame with the arguments given to it by the server this is
    # here for demo purposes only
    #playGame(640, 480,"left",socket.socket(socket.AF_INET, socket.SOCK_STREAM))
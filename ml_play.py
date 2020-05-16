"""
The template of the script for the machine learning process in game pingpong
"""
import pickle
import numpy as np
from os import path
# Import the necessary modules and classes
from mlgame.communication import ml as comm


def transformCommand(command):
    if 'MOVE_RIGHT' == command:
        return 1
    elif 'MOVE_LEFT' == command:
        return 2
    else:
        return 0

def ml_loop(side: str):
    """
    The main loop for the machine learning process
    The `side` parameter can be used for switch the code for either of both sides,
    so you can write the code for both sides in the same script. Such as:
    ```python
    if side == "1P":
        ml_loop_for_1P()
    else:
        ml_loop_for_2P()
    ```
    @param side The side which this script is executed for. Either "1P" or "2P".
    """

    # === Here is the execution order of the loop === #
    # 1. Put the initialization code here
    ball_served = False
    blocker_last_x = 0
    blocker_vx = 0
    last_command = 0
    filename = path.join(path.dirname(__file__), "save", "trained_model.pickle")
    with open(filename, 'rb') as file:
        tree = pickle.load(file)

    feature = []

    # 2. Inform the game process that ml process is ready
    comm.ml_ready()

    # 3. Start an endless loop
    while True:
        # 3.1. Receive the scene information sent from the game process
        scene_info = comm.recv_from_game()

        # 3.2. If either of two sides wins the game, do the updating or
        #      resetting stuff and inform the game process when the ml process
        #      is ready.
        if scene_info["status"] != "GAME_ALIVE":
            # Do some updating or resetting stuff
            ball_served = False

            # 3.2.1 Inform the game process that
            #       the ml process is ready for the next round
            comm.ml_ready()
            continue

        # 3.3 Put the code here to handle the scene information
        feature = []
        feature.append(scene_info["ball"][0])
        feature.append(scene_info["ball"][1])
        feature.append(scene_info["ball_speed"][0])
        feature.append(scene_info["ball_speed"][1])
        feature.append(scene_info["platform_1P"][0])
        if scene_info["ball"][1] == 80:
            feature.append(scene_info["ball"][0])
        else: feature.append(1000)
        feature.append(scene_info["blocker"][0])

        if(blocker_last_x != -99):
            blocker_vx = scene_info["blocker"][0] - blocker_last_x
            if scene_info["blocker"][0] == 0: blocker_vx = 5
            elif scene_info["blocker"][0] == 170: blocker_vx = -5
        else:
            blocker_vx = -99

        if scene_info["ball_speed"][1] > 0 and (scene_info["ball"][1]+scene_info["ball_speed"][1]) >= 415 and last_command == 0:
            y = abs((415 - scene_info["ball"][1]) / scene_info["ball_speed"][1])
            pred = (int)(scene_info["ball"][0] + scene_info["ball_speed"][0] * y)

        elif scene_info["ball_speed"][1] > 0 : # 球正在向下 # ball goes down
            x = ( scene_info["platform_1P"][1]-scene_info["ball"][1] ) // scene_info["ball_speed"][1] # 幾個frame以後會需要接  # x means how many frames before catch the ball
            pred = scene_info["ball"][0]+(scene_info["ball_speed"][0]*x)  # 預測最終位置 # pred means predict ball landing site 
            bound = pred // 200 # Determine if it is beyond the boundary
            if (bound > 0): # pred > 200 # fix landing position
                if (bound%2 == 0) : 
                    pred = pred - bound*200                    
                else :
                    pred = 200 - (pred - 200*bound)
            elif (bound < 0) : # pred < 0
                if (bound%2 ==1) :
                    pred = abs(pred - (bound+1) *200)
                else :
                    pred = pred + (abs(bound)*200)
        else : # 球正在向上 # ball goes up
            pred = 100

        feature.append(pred)
        feature.append(pred - 5)
        feature.append(pred + 5)

        feature = np.array(feature)
        feature = feature.reshape((-1, 10))

        # 3.4 Send the instruction for this frame to the game process
        if not ball_served:
            comm.send_to_game({"frame": scene_info["frame"], "command": "SERVE_TO_LEFT"})
            last_command = 0
            ball_served = True
        else:
            command = tree.predict(feature)
            last_command = command

            if command == 0:
                comm.send_to_game({"frame": scene_info["frame"], "command": "NONE"})
            elif command == 1:
                comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_RIGHT"})
            else :
                comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_LEFT"})
        blocker_last_x = scene_info["blocker"][0]
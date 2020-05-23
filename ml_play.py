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
    filename = path.join(path.dirname(__file__), "save", "trained_model_1P.pickle")
    with open(filename, 'rb') as file:
        tree = pickle.load(file)

    feature = []

    # 2. Inform the game process that ml process is ready
    comm.ml_ready()

    # 3. Start an endless loop
    while True:
        # 3.1. Receive the scene information sent from the game process
        scene_info = comm.recv_from_game()

        def move_to(pred) : #move platform to predicted position to catch ball 
            if scene_info["platform_1P"][0]+20  > (pred) and scene_info["platform_1P"][0]+20 < (pred): return 0 # NONE
            elif scene_info["platform_1P"][0]+20 <= (pred) : return 1 # goes right
            else : return 2 # goes left

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
        if scene_info["ball_speed"][1] > 0:
            if scene_info["ball_speed"][0] > 0: feature.append(0)
            else: feature.append(1)
        else:
            if scene_info["ball_speed"][0] > 0: feature.append(2)
            else: feature.append(3)
        feature.append(scene_info["blocker"][0])
        feature.append(scene_info["ball_speed"][0])
        feature.append(scene_info["ball_speed"][1])
        
        feature = np.array(feature)
        feature = feature.reshape((-1, 6))

        # 3.4 Send the instruction for this frame to the game process
        if not ball_served:
            comm.send_to_game({"frame": scene_info["frame"], "command": "SERVE_TO_LEFT"})
            ball_served = True
        else:
            pred = tree.predict(feature)
            command = move_to(pred)

            if command == 0:
                comm.send_to_game({"frame": scene_info["frame"], "command": "NONE"})
            elif command == 1:
                comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_RIGHT"})
            else :
                comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_LEFT"})
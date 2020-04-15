"""
The template of the main script of the machine learning process
"""

import games.arkanoid.communication as comm
from games.arkanoid.communication import ( \
    SceneInfo, GameStatus, PlatformAction
)
import games.arkanoid.game.gameobject as gameobject

def ml_loop():
    """
    The main loop of the machine learning process
    This loop is run in a separate process, and communicates with the game process.
    Note that the game process won't wait for the ml process to generate the
    GameInstruction. It is possible that the frame of the GameInstruction
    is behind of the current frame in the game process. Try to decrease the fps
    to avoid this situation.
    """

    # === Here is the execution order of the loop === #
    # 1. Put the initialization code here.
    ball_served = False
    # 2. Inform the game process that ml process is ready before start the loop.
    comm.ml_ready()

    # 3. Start an endless loop.
    while True:
        # 3.1. Receive the scene information sent from the game process.
        scene_info = comm.get_scene_info()

        # 3.2. If the game is over or passed, the game process will reset
        #      the scene and wait for ml process doing resetting job.
        if scene_info.status == GameStatus.GAME_OVER or \
            scene_info.status == GameStatus.GAME_PASS:
            # Do some stuff if needed
            ball_served = False

            # 3.2.1. Inform the game process that ml process is ready
            comm.ml_ready()
            continue

        # 3.3. Put the code here to handle the scene information
        ball_pos = scene_info.ball
        # vector = scene_info.vector
        plat_pos = scene_info.platform
        # print(vector[0])
        # 3.4. Send the instruction for this frame to the game process
        if not ball_served:
            comm.send_instruction(scene_info.frame, PlatformAction.SERVE_TO_LEFT)
            vector = [-7, -7]
            ball_last_pos = (0, 500)
            ball_served = True
        else:
            vector = [(ball_pos[0] - ball_last_pos[0]), (ball_pos[1] - ball_last_pos[1])]
            # if(vector[1] < 0):
            #         goal = 100
            # else:
            #     intersectX = (int)((400 - ball_pos[1]) / vector[1]) * vector[0] + ball_pos[0]
            #     # print("intersextX = ", intersectX)
            #     if(intersectX < 0):
            #         # print("need predict")
            #         intersectX = 0
            #         intersectY = (int)(abs(ball_pos[0] / vector[0])) * vector[1] + ball_pos[1]
            #         # print("intersext X, Y = ", intersectX, intersectY)
            #         goal = (int)((400 - intersectY) / vector[1]) * (vector[0]) * (-1)
            #     elif(intersectX > 200):
            #         # print("need predict")
            #         intersectX = 200
            #         intersectY = (int)(abs((200 - ball_pos[0]) / vector[0])) * vector[1] + ball_pos[1]
            #         # print("intersext X, Y = ", intersectX, intersectY)
            #         goal = 200 + (int)((400 - intersectY) / vector[1]) * (vector[0]) * (-1)
            #     else:
            #         goal = intersectX
            if(vector[1] < 0):
                    vector[0] *= -1
                    vector[1] *= -1
            intersectX = (int)((400 - ball_pos[1]) / vector[1]) * vector[0] + ball_pos[0]
            if(intersectX < 0):
                intersectX = 0
                intersectY = (int)(abs(ball_pos[0] / vector[0])) * vector[1] + ball_pos[1]
                goal = (int)((400 - intersectY) / vector[1]) * (vector[0]) * (-1)
            elif(intersectX > 200):
                intersectX = 200
                intersectY = (int)(abs((200 - ball_pos[0]) / vector[0])) * vector[1] + ball_pos[1]
                goal = 200 + (int)((400 - intersectY) / vector[1]) * (vector[0]) * (-1)
            else:
                goal = intersectX

            goal = goal + (5 - (goal % 10))
            # print(goal)

            if(plat_pos[0] + 20 <= goal):
                comm.send_instruction(scene_info.frame, PlatformAction.MOVE_RIGHT)
            elif(plat_pos[0] + 20 > goal):
                comm.send_instruction(scene_info.frame, PlatformAction.MOVE_LEFT)
            # else:
            #     comm.send_instruction(scene_info.frame, PlatformAction.NONE)

            ball_last_pos = ball_pos
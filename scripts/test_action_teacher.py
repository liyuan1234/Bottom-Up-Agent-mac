
import yaml
import sys
import os
import cv2

from BottomUpAgent.BottomUpAgent import SuperGamer
from BottomUpAgent.Teacher import Teacher
from BottomUpAgent.Eye import Eye



def get_operation_guidance_human(config):
    teacher = Teacher(config)
    eye = Eye(config)

    candidate_operations = [
        {"action_name": "Move Forward", "description": "Move the character forward."},
        {"action_name": "Move Backward", "description": "Move the character backward."},
        {"action_name": "Turn Left", "description": "Turn the character to the left."},
        {"action_name": "Turn Right", "description": "Turn the character to the right."}
    ]
    op = teacher.get_operation_guidance_human(candidate_operations)

    print(op)
    

if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    get_operation_guidance_human(config=config)
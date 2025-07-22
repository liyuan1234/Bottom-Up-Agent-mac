from BottomUpAgent.Eye import Eye
from BottomUpAgent.LongMemory import LongMemory
from BottomUpAgent.Detector import Detector

import yaml
import cv2
import matplotlib.pyplot as plt


def test_action_retrieval(config):
    long_memory = LongMemory(config)
    detector = Detector(config)

    img = "scripts/images/22.jpg"
    img_cv = cv2.imread(img)
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)

    state_feature = detector.encode_image(img_cv)

    potential_actions = long_memory.get_action_clusters(state_feature, 0.85)

    print("Potential Actions:")
    print(potential_actions)
            
if __name__ == "__main__":

    with open("config_c5.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    test_action_retrieval(config)
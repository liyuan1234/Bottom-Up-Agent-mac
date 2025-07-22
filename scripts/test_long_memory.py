import yaml
import cv2
from BottomUpAgent.LongMemory import LongMemory
from BottomUpAgent.Detector import Detector
from BottomUpAgent.Mcts import MCST

from matplotlib import pyplot as plt

img1 = "scripts/images/1.jpg"
img2 = "scripts/images/1.jpg"

def test_candidate_coordinates(config):
    long_memory = LongMemory(config)
    if not long_memory.is_initialized():
        long_memory.initialize()
    detector = Detector(config)

    img1_cv = cv2.imread(img1)
    img1_cv = cv2.cvtColor(img1_cv, cv2.COLOR_BGR2RGB)

    candidate_coordinates = detector.detect_centers(img1_cv)
    img1_features = detector.encode_image(img1_cv)

    long_memory.save_candidate_coordinates(img1_features, candidate_coordinates, img1_cv)

    img2_cv = cv2.imread(img2)
    img2_cv = cv2.cvtColor(img2_cv, cv2.COLOR_BGR2RGB)
    img2_features = detector.encode_image(img2_cv)

    idx, candidate_coordinates = long_memory.get_candidate_coordinates(img2_features)

    if idx is not None:

        print(idx)
        print(candidate_coordinates)

        img1_bk = long_memory.get_candidate_coordinates_img(idx)

        plt.figure(figsize=(20,20))
        plt.imshow(img1_bk)
        for action in candidate_coordinates:
            plt.scatter(action[0], action[1], color='red', s=100)

        plt.show()


def test_policy(config):
    long_memory = LongMemory(config)
    if not long_memory.is_initialized():
        long_memory.initialize()

    detector = Detector(config)

    im1 = cv2.imread(img1)
    im1 = cv2.cvtColor(im1, cv2.COLOR_BGR2RGB)
    state_feature = detector.encode_image(im1)

    idx, mcst_str = long_memory.get_policy(state_feature)
    if mcst_str is None:
        mcst = MCST()
    else:
        mcst = MCST.from_dict(mcst_str)

    p_node = mcst.random_select()
    children_actions = mcst.get_children_actions(p_node)
    print(children_actions)
    if 1 not in children_actions:
        actions = p_node.actions.copy()
        actions.append(1)
        value = 2
        mcst.expand(p_node, value, actions)

        long_memory.save_policy(idx, state_feature, mcst)

    mcst_str = long_memory.get_policy(state_feature)
    idx, mcst_str = long_memory.get_policy(state_feature)
    if mcst_str is None:
        mcst = MCST()
    else:
        mcst = MCST.from_dict(mcst_str)

    print(mcst.to_dict())

def test_random_select(config):
    long_memory = LongMemory(config)
    if not long_memory.is_initialized():
        long_memory.initialize()

    detector = Detector(config)

    im1 = cv2.imread(img1)
    im1 = cv2.cvtColor(im1, cv2.COLOR_BGR2RGB)
    state_feature = detector.encode_image(im1)

    idx, mcst_str = long_memory.get_policy(state_feature)
    if mcst_str is None:
        mcst = MCST()
    else:
        mcst = MCST.from_dict(mcst_str)

    p_node = mcst.random_select_bsf()
    print(p_node.node_id)
    print(p_node.is_fixed)

def test_delete_action(config):
    long_memory = LongMemory(config)
    if not long_memory.is_initialized():
        long_memory.initialize()

    action_id = 12
    action = long_memory.get_action(action_id)
    if action is None:
        print("Action not found")
        return

    action_cluser_id = 8
    action_cluster = long_memory.get_action_clusters_by_id(action_cluser_id)


    long_memory.delete_action(action, action_cluster)

if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    test_delete_action(config=config)
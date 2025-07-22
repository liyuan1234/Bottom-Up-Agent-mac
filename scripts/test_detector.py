import yaml
import sys
import os
import cv2
from sklearn.metrics.pairwise import cosine_similarity

from BottomUpAgent.Eye import Eye
from BottomUpAgent.BottomUpAgent import SuperGamer
from BottomUpAgent.Detector import Detector
from matplotlib import pyplot as plt


def test_detect_centers(config):
    detector = Detector(config)
    im1 = cv2.imread("scripts/images/1.jpg")
    im1 = cv2.cvtColor(im1, cv2.COLOR_BGR2RGB)

    centers = detector.detect_centers(im1)

    plt.figure(figsize=(20,20))
    plt.imshow(im1)
    for center in centers:
        plt.scatter(center[0], center[1], color='red', s=100)

    print(centers)
    plt.show()

def test_cal_sim(config):
    detector = Detector(config)
    eye = Eye(config)
    im1 = cv2.imread("scripts/images/21.jpg")
    im2 = cv2.imread("scripts/images/22.jpg")

    im1 = cv2.cvtColor(im1, cv2.COLOR_BGR2RGB)
    im2 = cv2.cvtColor(im2, cv2.COLOR_BGR2RGB)

    im1_feature = detector.encode_image(im1)
    im2_feature = detector.encode_image(im2)

    sim = cosine_similarity(im1_feature, im2_feature)
    print(sim)

    im2.resize(im1.shape)
    eye.detect_acted_cv(im1, im2)

if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    test_cal_sim(config=config)
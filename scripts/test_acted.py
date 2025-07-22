import yaml
import cv2

from BottomUpAgent.Eye import Eye


def test_acted(config):
    eye = Eye(config)
    im1 = cv2.imread("scripts/images/1.jpg")
    im1 = cv2.cvtColor(im1, cv2.COLOR_BGR2RGB)
    im1 = cv2.resize(im1, (1280, 744))

    im2 = cv2.imread("scripts/images/4.jpg")
    im2 = cv2.cvtColor(im2, cv2.COLOR_BGR2RGB)
    im2 = cv2.resize(im2, (1280, 744))

    acted = eye.detect_acted_cv(im1, im2)

    print(acted)

if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    test_acted(config=config)
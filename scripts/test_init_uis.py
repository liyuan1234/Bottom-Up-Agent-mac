import yaml

from BottomUpAgent.BottomUpAgent import SuperGamer


def test_init_uis(config):
    gamer = SuperGamer(config)
    

if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    test_init_uis(config=config)
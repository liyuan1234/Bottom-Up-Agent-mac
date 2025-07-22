import yaml

from BottomUpAgent.BottomUpAgent import SuperGamer


def test_run(config):
    gamer = SuperGamer(config)
    task = 'PlayGame and win the game'
    gamer.run(task)

if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    test_run(config=config)
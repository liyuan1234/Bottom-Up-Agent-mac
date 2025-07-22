import yaml

from BottomUpAgent.BottomUpAgent import SuperGamer




def test_train_action_step(config):
    gamer = SuperGamer(config)
    task = 'PlayGame and learn the basic ui actions'
    gamer.train_action_step(task)

def test_train_action(config):
    gamer = SuperGamer(config)
    task = 'PlayGame and learn the basic ui actions'
    gamer.train_action(task)

if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    test_train_action(config=config)
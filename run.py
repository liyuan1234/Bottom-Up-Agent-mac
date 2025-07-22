import yaml
import argparse
from BottomUpAgent.BottomUpAgent import BottomUpAgent


def main(config):
    gamer = BottomUpAgent(config)
    task = 'Play the game'
    gamer.run(task=task, max_step=1000)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', required=True, help='path to the config file')
    
    opt = parser.parse_args()

    with open(opt.config_file, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    main(config=config)
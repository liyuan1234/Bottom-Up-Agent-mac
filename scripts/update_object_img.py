from BottomUpAgent.LongMemory import LongMemory
import yaml
import cv2
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', required=True, help='path to the config file')
    parser.add_argument('--object_id', required=True, help='object id to update')
    parser.add_argument('--object_img_file', required=True, help='path to the object image file')
    
    opt = parser.parse_args()

    with open(opt.config_file, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    memory = LongMemory(config)

    object_image = cv2.imread(opt.object_img_file)
    object_image = cv2.cvtColor(object_image, cv2.COLOR_BGR2RGB)

    memory.update_object(opt.object_id, object_image)
    print(f"Updated object {opt.object_id} with new image.")
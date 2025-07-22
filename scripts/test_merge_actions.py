import yaml
import sys
import os
import cv2

from BottomUpAgent.Brain import Brain
from BottomUpAgent.LongMemory import LongMemory
from base_model import creat_base_model
from BottomUpAgent import Prompt
from BottomUpAgent import FunctionCalls

def test_cluster_actions(config):
    long_memory = LongMemory(config)
    base_model = creat_base_model(config['brain']['base_model'])
    cluster_actions_tool = FunctionCalls.cluster_actions_tool(config['brain']['base_model'])

    for i in [3]:
        print(f"Processing state {i}...")
        state_feature = long_memory.get_mcst_state(i)

        actions = long_memory.get_actions_by_state(state_feature)



        actions_info = []
        for action in actions:
            action_info = {"id": action["id"], "name": action["name"], "description": action["description"]}
            print(f"Action: {action_info}")
            actions_info.append(action_info)

        prompt = Prompt.cluster_actions_prompt(actions)

        response = base_model.call_text(prompt, [cluster_actions_tool])

        print(response)

        clusters = []

        if response['function'] is not None:
            if 'clusters' in response['function']['input']:
                clusters = response['function']['input']['clusters']

        print("Action Clusters:")
        for cluster in clusters:
            print(cluster)
            # long_memory.save_action_cluster(state_feature, cluster['name'], cluster['description'], cluster['members'])


def test_cluster_actions2(config):
    long_memory = LongMemory(config)
    base_model = creat_base_model(config['brain']['base_model'])
    cluster_actions_tool = FunctionCalls.cluster_actions_tool(config['brain']['base_model'])
    action_ids = [1]
    for action_id in action_ids:
        action = long_memory.get_action(action_id)
        state_feature =  action['state_feature']

        actions = long_memory.get_actions_by_state(state_feature)

        actions_info = []
        for action in actions:
            action_info = {"id": action["id"], "name": action["name"], "description": action["description"]}
            print(f"Action: {action_info}")
            actions_info.append(action_info)

        prompt = Prompt.cluster_actions_prompt(actions_info)

        response = base_model.call_text(prompt, [cluster_actions_tool])

        print(response)

        clusters = []

        if response['function'] is not None:
            if 'clusters' in response['function']['input']:
                clusters = response['function']['input']['clusters']

        print("Action Clusters:")
        for cluster in clusters:
            print(cluster)
            long_memory.save_action_cluster(state_feature, cluster['name'], cluster['description'], cluster['members'])


def test_merge_actions(config):
    long_memory = LongMemory(config)
    brain = Brain(config, None)
    action_ids = 132
    new_action_ids = [133, 134, 135, 136, 137, 138, 139]
    action = long_memory.get_action(action_id)
    state_feature =  action['state_feature']
    action_clusters = brain.long_memory.get_action_clusters(state_feature)

    new_actions = []
    for action_id in new_actions:
        action = long_memory.get_action(action_id)
        new_actions.append({"id": action["id"], "name": action["name"], "description": action["description"]})


    action_clusters_merged = brain.merge_actions(action_clusters, new_actions)
    print("Merged Action Clusters:")
    print(action_clusters_merged)


if __name__ == "__main__":
    with open("config/sts_explore_gpt4o.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    test_cluster_actions2(config=config)
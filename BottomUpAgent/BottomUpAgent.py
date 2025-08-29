import time
from .Logger import Logger
from .Eye import Eye
from .Hand import Hand
from .Brain import Brain
from .Detector import Detector
from .Teacher import Teacher
from .Mcts import MCTS
from utils.utils import image_grounding, cv_to_base64, operations_to_str, image_grounding_v3
from .UnifiedOperation import UnifiedOperation
from .pre_knowledge import get_pre_knowledge
import numpy as np
from pynput import keyboard as pkb
from .visualizer import push_data, data_init

from concurrent.futures import ThreadPoolExecutor, as_completed

class BottomUpAgent:
    def __init__(self, config):
        self.game_name = config['game_name']

        self.logger = Logger(config['project_name'], config['game_name'] + ' - ' + config['run_name'], backend='wandb')
        self.eye = Eye(config)
        self.hand = Hand(config)
        self.detector = Detector(config)
        self.teacher = Teacher(config)
        self.brain = Brain(config, self.detector, self.logger)
        self.close_explore = config['close_explore']
        self.close_evaluate = config['close_evaluate'] if 'close_evaluate' in config else False
        self.close_reset = config['close_reset'] if 'close_reset' in config else True

        self.operates = config['operates'] if 'operates' in config else ['Click']
        self.max_operation_length = config['max_operation_length'] if 'max_operation_length' in config else 2
        self.is_base = config['is_base'] if 'is_base' in config else False
        self.exec_duration = config['exec_duration'] if 'exec_duration' in config else 3.0

        self.suspended_skill_cluster_ids = []

        print(f"GameAgent initialized")
        print(f"game_name: {self.game_name}")


    def get_observation(self):
        screen = self.eye.get_screenshot_cv()
        state_feature = self.detector.encode_image(screen)
        return {"state_feature": state_feature, "screen": screen}
    
    
    def get_potential_operations(self, existed_objects):
        # use for train action
        operations = []
        for operate in self.operates:
            if operate == 'Click':
                for object in existed_objects:
                    operations.append({'operate': operate, 'object_id': object['id'], 'params': {'x': object['center'][0], 'y': object['center'][1]}})
            else:
                print(f"Unsupported operate: {operate}")
                continue
        return operations
    
    def operate_grounding(self, operation, state):
        if operation['operate'] == 'Click':
            if 'params' not in operation:
                object_img = self.brain.long_memory.get_object_image_by_id(operation['object_id'])
                grounding_result, score = image_grounding_v3(state['screen'], object_img)
                if grounding_result:
                    operation_ = UnifiedOperation.Click(grounding_result[0], grounding_result[1])
                    operation['params'] = {'x': grounding_result[0], 'y': grounding_result[1]}
                    return operation_
                else:
                    print(f"Operation grounding failed: {operation['object_id']} score: {score}")
                    return None
            else:
                operation_ = UnifiedOperation.Click(operation['params']['x'], operation['params']['y'])
                return operation_
            
        else:
            print(f"Unsupported operate: {operation['operate']}")
            return None


    

    def run_step(self, step, task):
        self.logger.log({"step": step}, step)
        # get screen 
        ob = self.get_observation()

        state = self.brain.long_memory.get_state(ob)

        if state is None:
            print("No state found, create state")

            mcts = MCTS()
            
            import cv2
            import os
            from datetime import datetime
            
            # Save the screen as PNG to ../images
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            output_dir = "./states"
            os.makedirs(output_dir, exist_ok=True)
            filename = f"state_screen_{timestamp}.png"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, ob['screen'])
            print(f"Saved state screen to {filepath}")
            
            _, image_blob = cv2.imencode('.png', ob['screen'])
            image_blob = image_blob.tobytes()
            state = {
                'id': None,
                'state_feature': ob['state_feature'],
                'object_ids': [],
                'mcts': mcts,
                'skill_clusters': [],
                "image": ob['screen'],  # Store the original screen, not the blob
            }
            state['id'] = self.brain.long_memory.save_state(state)
            

        skill_clusters_ids = state['skill_clusters']
        skill_clusters = self.brain.long_memory.get_skill_clusters_by_ids(skill_clusters_ids)

        if len(skill_clusters) == 0:
            skill_cluster = None
            skills = []
        else:
            skill_cluster_id = self.brain.select_skill_cluster(step, ob, skill_clusters)
            if skill_cluster_id is None:
                return 'Continue'   
            
            skill_cluster = self.brain.long_memory.get_skill_clusters_by_id(skill_cluster_id)
            skills = self.brain.long_memory.get_skills_by_ids(skill_cluster['members'])
            print(f"selected skill_cluster id: {skill_cluster['id']} name: {skill_cluster['name']} description: {skill_cluster['description']}")
            push_data({'skill_goal': {'id': skill_cluster['id'], "name": skill_cluster['name'], "description": skill_cluster['description']}})

        result = 'Retry'
        suspended_skill_ids = []
        while result == 'Retry':
            skill, suspend_flag = self.brain.select_skill(skills, skill_cluster, suspended_skill_ids, self.close_explore)
            if skill['name'] == 'Explore':
                self.logger.log({"decision": 0, "decision_text": "Explore"}, step)
                push_data({'decision': "Explore"})

                result = self.explore(step, state, skill, skill_clusters)
                if skill_cluster is not None:
                    self.brain.long_memory.update_skill_cluster_explore_nums(skill_cluster['id'], skill_cluster['explore_nums'] + 1)
                break
            else:
                self.logger.log({"decision": 1, "decision_text": "Exploit"}, step)
                push_data({'decision': "Exploit"})
                suspended_skill_ids.append(skill['id'])
                result = self.exploit(step, task, skill)
                if result == 'Fail':
                    suspended_skill_ids.append(skill['id'])
                    result = 'Retry'
            if result == 'ExploreFail' and suspend_flag:
                print("Explore failed, suspend skill cluster")
                self.suspended_skill_cluster_ids.append(skill_cluster['id'])
            elif result == 'Continue':
                self.suspended_skill_cluster_ids.clear()
            self.state_reset()

        self.brain.skill_evolution(step, skills, skill_cluster) 
        
        
    def skill_augment(self, step, state, node):
        """
        Generate new skill by augmenting the existing skill.
        Will change the mcts and objects in the state.
        """
        self.state_reset()
        
        obs = [self.get_observation()]

        operations = node.operations.copy()
        for operation in operations:
            print(f"operation: {operation}")
            operation_ = self.operate_grounding(operation, obs[-1])
            if operation_ is None:
                return None, True
            self.hand.do_operation(operation_, self.eye.left, self.eye.top)
            time.sleep(self.exec_duration)
            obs.append(self.get_observation())

        existed_object_ids = state['object_ids']
        existed_objects = self.brain.long_memory.get_object_by_ids(existed_object_ids)
        updated_objects = self.detector.update_objects(obs[-1]['screen'], existed_objects)
        print(f"detectced objects nums: {len(updated_objects)}")
        updated_objects = self.brain.long_memory.update_objects(state, updated_objects)

        potential_operations = self.get_potential_operations(updated_objects)

        # print(f"potential_operations: {potential_operations}")
        if len(potential_operations) == 0:
            print("No potential operations found")
            node.is_fixed = True
            return None, False

        candidate_operations = []
        existed_children_operations = state['mcts'].get_children_operations(node)    
        for operation in potential_operations:
            existed_flag = False   
            for existed_operation in existed_children_operations:
                if (operation['operate'] == existed_operation['operate']) and (operation['object_id'] == existed_operation['object_id']):
                    existed_flag = True
                    break
            if not existed_flag:
                candidate_operations.append(operation)
            
        if len(candidate_operations) == 0:
            print("No candidate operations found after skill")
            node.is_fixed = True
            return None, False




        #{'operate': 'Click', 'object_id': 46, 'params': {'x': 482, 'y': 35}}
        # if not hasattr(self.teacher, 'brain') or self.teacher.brain is None:
        #     self.teacher.brain = self.brain
        select_operation = self.teacher.get_operation_guidance(candidate_operations)
        if select_operation == 'do operation using brain.do_operation!':            
            state_with_screen_attribute = {'screen': state['image']}
            response = self.brain.do_operation(step, '', state_with_screen_attribute, pre_knowledge=None)
            print('Using AI to pick operation. AI response:'+response)
            select_operation = {'operate': response['operate'],'object_id':[], 'params': response['params']}
        print(f"select_operation: {select_operation}")
        existed_children_operations.append(select_operation)
        operation_ = self.operate_grounding(select_operation, obs[-1])

        self.hand.do_operation(operation_, self.eye.left, self.eye.top)
        time.sleep(self.exec_duration)
        obs.append(self.get_observation())
        operations.append(select_operation)
        print(f"operations: {operations}")
        new_mcts_node = state['mcts'].expand(node, 3, operations)
        if self.eye.detect_acted_cv(obs[-2]['screen'], obs[-1]['screen']):
            new_skill = self.brain.generate_and_save_skill(step, obs, operations, state['id'], new_mcts_node.node_id)

            if self.brain.detect_state_changed(obs[0], obs[-1]):
                print("State changed")
                new_mcts_node.is_fixed = True
                return new_skill, True
            else:
                return new_skill, False
        else:
            operations[-1].pop('params', None)
            print("Operation not acted")
            return None, False


    def explore(self, step, state, skill, skill_clusters):
        if self.close_explore:
            return 'ExploreFail'
        
        mcts = state['mcts']
        if skill['mcts_node_id'] is None:
            mcts_node_id = 0
        else:
            mcts_node_id = skill['mcts_node_id']

        mcts_node = mcts.get_node(mcts_node_id)
        print(f"mcts_node_id: {mcts_node_id}")
        parent_node = mcts.get_node(mcts_node.parent_id) if mcts_node.parent_id is not None else None

        new_skill_num = 0
        stop_flag = False
        new_skills = []
        print(f"begin explore skill augment from parent node")
        if (parent_node is not None) and (len(parent_node.operations) < self.max_operation_length):
            while (not parent_node.is_fixed) and (not stop_flag) and (new_skill_num < 3):
                new_skill, stop_flag = self.skill_augment(step, state, parent_node)
                if new_skill is not None:
                    new_skill_num += 1
                    new_skills.append(new_skill)

        print(f"begin explore skill augment from selected node")
        new_skill_num = 0
        if (len(mcts_node.operations) < self.max_operation_length):
            while (not mcts_node.is_fixed) and (not stop_flag) and (new_skill_num < 3):
                new_skill, stop_flag = self.skill_augment(step, state, mcts_node)
                if new_skill is not None:
                    new_skill_num += 1
                    new_skills.append(new_skill)

        if len(new_skills) == 0:
            print("No new skills generated")
            return 'ExploreFail'
        else:
            print(f"New skills generated: {len(new_skills)}")
            self.brain.merge_and_save_skills(step, state, skill_clusters, new_skills)
            print(f"skill_clusters num: {len(skill_clusters)}")
            self.brain.long_memory.update_state(state)
            self.logger.log({f"skills/skills_generate_num": len(new_skills)}, step)
            return 'Continue'
    
    def exploit(self, step, task, skill):
        print(f"begin exploit")
        self.state_reset()
        obs = [self.get_observation()]
        print(f"selected skill id: {skill['id']} name: {skill['name']} description: {skill['description']} \
                   fitness: {skill['fitness']} num: {skill['num']} operations: {skill['operations']}")
        skill_fitness = skill['fitness']
        exec_chain = []
        operations = skill['operations']
        for operation in operations:
            ob = self.get_observation()
            operation_ = self.operate_grounding(operation, ob)
            exec_chain.append({'screen': f'data:image/png;base64,{cv_to_base64(ob["screen"])}', 'operation': operation_})
            push_data({'exec_chain': exec_chain})
            if operation_ is None:
                print("Operation grounding failed")
                push_data({'result': 'grounding failed'})
                return 'Fail'

            self.hand.do_operation(operation_, self.eye.left, self.eye.top)
            time.sleep(2.0)
        obs.append(self.get_observation())
        exec_chain.append({'screen': f'data:image/png;base64,{cv_to_base64(obs[-1]["screen"])}'})
        push_data({'exec_chain': exec_chain})
        
        if not self.eye.detect_acted_cv(obs[-2]['screen'], obs[-1]['screen']):
            print("Action not acted")
            self.logger.log({"eval/skill_acted": 0}, step)
            push_data({'result': 'not acted'})
            return 'Fail'

        # skill_evaluate
        if not self.close_evaluate:
            time0 = time.time()
            is_consistent, is_progressive = self.brain.skill_evaluate(step, task, obs, skill)
            elapsed_time = time.time() - time0
            print(f"skill_evaluate elapsed_time: {elapsed_time}")
            print(f"is_consistent: {is_consistent} is_progressive: {is_progressive}")
            push_data({'result': f"is_consistent: {is_consistent} is_progressive: {is_progressive}"})
            if is_consistent is not None and is_progressive is not None:
                self.logger.log({"eval/skill_consistent": int(is_consistent), "eval/skill_progressive": int(is_progressive)}, step)
                accumulated_consistent = self.logger.last_value('eval/accumulated_skill_consistent') if self.logger.last_value('eval/accumulated_skill_consistent') is not None else 0
                accumulated_progressive = self.logger.last_value('eval/accumulated_skill_progressive') if self.logger.last_value('eval/accumulated_skill_progressive') is not None else 0
            
                if is_consistent:
                    skill_fitness += 1
                    accumulated_consistent += 1

                if is_progressive:
                    skill_fitness += 1
                    accumulated_progressive += 1

                self.logger.log({"eval/accumulated_skill_consistent": accumulated_consistent, "eval/accumulated_skill_progressive": accumulated_progressive}, step)

                num = skill['num'] + 1
                
                # skill_fitness = (skill_fitness + skill['fitness'] * skill['num']) / num
                skill['fitness'] = skill_fitness
                skill['num'] = num

                self.brain.long_memory.update_skill(skill['id'], skill_fitness, num)

                if is_consistent and is_progressive:
                    result = 'Continue'
                else:
                    result = 'Fail'
        else:
            result = 'Continue'

        self.logger.log({"eval/skill_acted": 1}, step)
        return result
        
    def run_step_base(self, task, step):
        self.state_reset()
        self.logger.log({"decision": 1, "decision_text": "Exploit"}, step)
        push_data({'step': step, 'decision': 'Exploit'})
        
        # Use get_observation() instead of get_state()
        ob1 = self.get_observation()
        import cv2
        import os
        from datetime import datetime
        
        # Save the screen as PNG to ../images
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        output_dir = "./states_base"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"state_screen_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)
        cv2.imwrite(filepath, ob1['screen'])
        print(f"Saved state screen to {filepath}")

        operation = self.brain.do_operation(step, task, ob1, get_pre_knowledge(self.game_name))
        if operation is None:
            return 'Continue'
        self.hand.do_operation(operation, self.eye.left, self.eye.top)
        time.sleep(3.0)
        ob2 = self.get_observation()

        if not self.eye.detect_acted_cv(ob1['screen'], ob2['screen']):
            print("Action not acted")
            self.logger.log({"eval/skill_acted": 0}, step)
            return 'Continue'

        # skill_evaluate
        if not self.close_evaluate:
            time0 = time.time()
            observations = [ob1, ob2]
            is_progressive = self.brain.skill_evaluate2(step, task, observations)
            elapsed_time = time.time() - time0
            print(f"skill_evaluate elapsed_time: {elapsed_time}")
            print(f"is_progressive: {is_progressive}")
            if is_progressive is not None:
                self.logger.log({"eval/skill_progressive": int(is_progressive)}, step)
                accumulated_progressive = self.logger.last_value('eval/accumulated_skill_progressive') if self.logger.last_value('eval/accumulated_skill_progressive') is not None else 0

                if is_progressive:
                    accumulated_progressive += 1

                self.logger.log({"eval/accumulated_skill_progressive": accumulated_progressive}, step)

        self.logger.log({"eval/skill_acted": 1}, step)

        im1 = f'data:image/png;base64,{cv_to_base64(ob1["screen"])}'
        im2 = f'data:image/png;base64,{cv_to_base64(ob2["screen"])}'

        push_data({'exec_chain': [{'screen': im1, 'operation': operation}, {'screen': im2}]})
        return 'Continue'

        
    def run(self, task, max_step=50):
        is_paused = False
        is_continuous = True
        step_requested = False
        should_exit = False

        self.get_observation()

        def toggle_pause():
            nonlocal is_paused
            is_paused = not is_paused   

        def toggle_continuous():
            nonlocal is_continuous
            is_continuous = True

        def request_step():
            nonlocal step_requested
            step_requested = True   

        def request_exit():
            nonlocal should_exit
            should_exit = True

        def on_press(key):
            try:
                if key.char == ' ':
                    toggle_pause()
                elif key.char == ']':
                    toggle_continuous()
                elif key.char == '[':
                    request_step()
                elif key.char == '/':
                    request_exit()
            except AttributeError:
                # prevent shift、ctrl error
                pass

        listener = pkb.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()  # non-blocking listen

        print("Running controls:")
        print("Space: Toggle pause")
        print("]: Toggle continuous execution")
        print("[: Step execution")
        print("/: Exit running")

        finished = False
        step = self.logger.last_value('step') + 1  if self.logger.last_value('step') is not None else 0
        while not finished and not should_exit:
            if is_paused and not step_requested:
                time.sleep(0.1)
                continue

            print(f"Running step: {step}")
            self.logger.log({"step": step}, step)

            if step > max_step:
                break

            if self.is_base:
                result = self.run_step_base(task, step)
            else:
                result = self.run_step(step, task)

            if result == 'Finished':
                finished = True

            if step_requested:
                step_requested = False
                is_paused = True  # Always pause after step execution

            if not is_continuous:
                is_paused = True  # Always pause if not in continuous mode

            time.sleep(0.1)  # Small delay between steps
            step += 1

    def state_reset(self):
        if self.close_reset:
            return
        if self.game_name== 'Slay the Spire':
            x = self.eye.left + 100
            y = self.eye.top + 100
            self.hand.right_single_click(x, y)
            time.sleep(1.0)

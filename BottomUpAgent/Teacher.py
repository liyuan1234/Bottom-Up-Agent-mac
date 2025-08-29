import random
from pynput import mouse
import pyautogui




class Teacher():
    def __init__(self, config):
        self.type = config['teacher_type']

    def get_operation_guidance(self, candidate_operations):
        if self.type == 'Human':
            return self.get_operation_guidance_human(candidate_operations)
        
        elif self.type == 'mouse_click':
            print('awaiting click...')
            return self.await_mouse_operation()
        elif self.type == 'AI':
            return 'do operation using brain.do_operation!' 
        elif self.type == 'Random':
            return random.choice(candidate_operations)
        else:
            print(f"Unsupported type: {self.type}")
            return None

    def await_mouse_operation(self):
        start_pos = [None,None]
        end_pos = [None,None]
        def on_move(x, y):
            print(f'move: {x},{y}', end='\r')
        
        def on_click(x, y, button, pressed):
            if pressed:
                start_pos[0] = x
                start_pos[1] = y
                return True # do not terminate yet
            elif not pressed:
                end_pos[0] = x
                end_pos[1] = y
                
                print(f'startpos: {start_pos}')
                print(f'end pos: {end_pos}')
                return False     # terminate
            
        with mouse.Listener(on_click=on_click, on_move=on_move) as listener:
            listener.join()
            
        if (abs(start_pos[0] - end_pos[0]) + abs(start_pos[1]-end_pos[1])) < 1: # check if mouse moved much
            return {'operate': 'Click', 'object_id': None, 'params': {'x': start_pos[0],'y':start_pos[1]}} 
        else:
            return {'operate': 'Drag', 'object_id': None, 'params': {'x1': start_pos[0],'y1':start_pos[1],'x2':end_pos[0],'y2':end_pos[1]}} 


    def get_operation_guidance_human(self, candidate_operations):
        print("\n[Human Operation Guidance]")
        print("Please select an operation by typing the index:")

        for idx, op in enumerate(candidate_operations):
            print(f"{idx}: {op}")

        while True:
            try:
                choice = input("Enter index of chosen operation: ").strip()
                if choice == '':
                    print("No input received. Returning None.")
                    return None
                if not choice.isdigit():
                    print("Invalid input. Please enter a valid index.")
                    continue

                index = int(choice)
                if 0 <= index < len(candidate_operations):
                    return candidate_operations[index]
                else:
                    print("Index out of range. Try again.")
            except KeyboardInterrupt:
                print("\nCancelled by user.")
                return None
            except Exception as e:
                print(f"Error: {e}")
                return None


    


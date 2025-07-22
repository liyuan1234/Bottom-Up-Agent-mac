import numpy as np

class MCTS_NODE():
    def __init__(self, node_id, parent_id=None, value=0, operations=None, children_ids=None, n_visits=0, is_fixed=False):
        self.node_id = node_id
        self.parent_id = parent_id
        self.value = value
        self.operations = operations or []
        self.children_ids = children_ids or []
        self.n_visits = n_visits
        self.is_fixed = is_fixed

    def to_dict(self):
        return {
            "node_id": self.node_id,
            "parent_id": self.parent_id,
            "value": self.value,
            "operations": self.operations,
            "children_ids": self.children_ids,
            "is_fixed": self.is_fixed,
            "n_visits": self.n_visits
        }

    @staticmethod
    def from_dict(data):
        return MCTS_NODE(
            node_id=data["node_id"],
            parent_id=data["parent_id"],
            value=data["value"],
            operations=data["operations"],
            children_ids=data["children_ids"],
            is_fixed=data["is_fixed"],
            n_visits=data["n_visits"]
        )

class MCTS():
    def __init__(self, nodes=None, optimal_node_id=None, node_id=0):
        self.nodes = nodes or {}
        self.optimal_node_id = optimal_node_id
        self.node_id = node_id

        if len(self.nodes) == 0:
            node = MCTS_NODE(node_id)
            node.value = 5
            self.nodes[node_id] = node
            self.optimal_node_id = node.node_id
            self.node_id += 1

    def to_dict(self):
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "optimal_node_id": self.optimal_node_id,
            "node_id": self.node_id 
            }

    @staticmethod
    def from_dict(data):
        nodes = {}
        for node_data in data["nodes"]:
            node = MCTS_NODE.from_dict(node_data)
            nodes[node.node_id] = node
        return MCTS(nodes=nodes, optimal_node_id=data["optimal_node_id"], node_id=data["node_id"])

    
    def random_select(self):
        if len(self.nodes) == 1:
            return self.nodes[0]
        else:
            # select one node in the tree by the total_value
            weights = np.array([node.value for node in self.nodes])

            sum = weights.sum()

            if sum == 0:
                probabilities = np.ones(len(weights)) / len(weights)
            else:
                probabilities = weights / weights.sum()
            selected_node = np.random.choice(self.nodes, p=probabilities)

            return selected_node

    def random_select_bsf(self):
        if len(self.nodes) == 1 and not self.nodes[0].is_fixed:
            return self.nodes[0]

        # Get all nodes and their depths (using operations length)
        node_depths = {}
        for node in self.nodes:
            node_depths[node.node_id] = len(node.operations)

        # Find the maximum depth
        max_depth = max(node_depths.values())

        # Try each depth level from 0 to max_depth
        for depth in range(max_depth + 1):
            # Get all nodes at current depth that are not fixed
            current_depth_nodes = []
            current_depth_weights = []
            
            for node in self.nodes:
                if node_depths[node.node_id] == depth and not node.is_fixed:
                    current_depth_nodes.append(node)
                    current_depth_weights.append(node.value)

            if len(current_depth_nodes) > 0:
                # If we found unfixed nodes at this depth, select one randomly
                weights = np.array(current_depth_weights)
                if weights.sum() > 0:
                    probabilities = weights / weights.sum()
                    selected_node = np.random.choice(current_depth_nodes, p=probabilities)
                    return selected_node

        # If we get here, all nodes are fixed
        return None
          
    def expand(self, p_node, value, operations):
        # expand the node
        new_node = MCTS_NODE(self.node_id, parent_id=p_node.node_id, value=value, operations=operations)
        self.nodes[self.node_id] = new_node
        p_node.children_ids.append(new_node.node_id)
        self.node_id += 1

        if value > self.nodes[self.optimal_node_id].value:
            self.optimal_node_id = new_node.node_id

        return new_node

    def get_children_operations(self, node):
        operations = []
        for id in node.children_ids:
            operation = self.nodes[id].operations[-1]
            operations.append(operation)
        return operations
    
    def get_node(self, node_id):
        if node_id == None:
            return None
        for node in self.nodes.values():
            if node.node_id == node_id:
                return node
        return None

    def delete_node(self, node_id):
        # delete the node
        node = self.get_node(node_id)
        if node == None:
            return False
        
        if len(node.children_ids) > 0:
            return False
        
        if node.parent_id != None:
            parent_node = self.get_node(node.parent_id)
            if parent_node != None:
                parent_node.children_ids.remove(node.node_id)
        
        self.nodes.pop(node_id, None)
        return True

    # def insert(self, operations):
    #     """
    #     Insert the full operations path into the tree.
    #     Only adds missing nodes one by one (layer by layer).
    #     Returns the final node corresponding to the operations.
    #     """
    #     current_node = self.get_node(0)  # root node

    #     for depth, op in enumerate(operations):
    #         target_ops = operations[:depth + 1]
    #         found = False

    #         for child_id in current_node.children_ids:
    #             child_node = self.get_node(child_id)
    #             if child_node.operations == target_ops:
    #                 current_node = child_node
    #                 found = True
    #                 break

    #         if not found:
    #             # Create new node for this layer
    #             new_node = MCTS_NODE(
    #                 node_id=self.node_id,
    #                 parent_id=current_node.node_id,
    #                 value=0,
    #                 operations=target_ops,
    #             )

    #             self.nodes[self.node_id] = new_node
    #             current_node.children_ids.append(new_node.node_id)
    #             current_node = new_node
    #             self.node_id += 1

    #     return current_node
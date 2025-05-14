class Node:
    def __init__(self, node_id, input_data, output_data):
        self.node_id = node_id
        self.input_data = input_data
        self.output_data = output_data

def find_peak_memory_in_sequence(nodes):
    """
    计算拓扑节点按顺序执行时的最大峰值占用内存。

    Args:
        nodes: 一个 Node 对象的列表，按执行顺序列出。

    Returns:
        执行过程中的最大峰值内存占用。
    """
    current_memory_usage = 0
    peak_memory_usage = 0  # 假设内存占用从0开始，并且不会是负的峰值

    # 也可以将 peak_memory_usage 初始化为 float('-inf')
    # 如果序列可能导致所有累积值都是负数，并且你想捕获最小的负数（即绝对值最大的负数）
    # 但对于内存占用，通常我们关心正值。
    # 如果第一个操作就导致负的 current_memory_usage，
    # peak_memory_usage 仍为0是合理的，表示没有正的内存峰值。
    # 或者，可以初始化 peak_memory_usage = 第一个节点的 delta (如果列表不为空)

    if not nodes:
        return 0 # 如果没有节点，峰值为0

    # 更健壮的初始化方式，特别是如果允许所有值为负
    # peak_memory_usage = float('-inf') # 确保任何计算值都会比它大
    # for i, node in enumerate(nodes):
    #     delta = node.output_data - node.input_data
    #     current_memory_usage += delta
    #     if i == 0: # 特殊处理第一个峰值，确保它被记录
    #         peak_memory_usage = current_memory_usage
    #     else:
    #         if current_memory_usage > peak_memory_usage:
    #             peak_memory_usage = current_memory_usage
    # if peak_memory_usage < 0 and we only care about positive peaks:
    #     return 0

    # 简化版本，假设我们对“占用”感兴趣，通常是正值。
    # 如果所有操作导致内存减少，峰值仍为0。
    for node in nodes:
        delta = node.output_data - node.input_data
        current_memory_usage += delta
        if current_memory_usage > peak_memory_usage:
            peak_memory_usage = current_memory_usage
            
    return peak_memory_usage

# 示例数据
# 场景1:
nodes_scenario1 = [
    Node('1', 3, 7),
    Node('2', 5, 9),
    Node('3', 2, 6)
]

# 场景2:
nodes_scenario2 = [
    Node('1', 3, 7),
    Node('2', 5, 9),
    Node('3', 6, 2)  # 节点3的输入输出改变
]

# 测试
peak1 = find_peak_memory_in_sequence(nodes_scenario1)
print(f"场景1的峰值内存占用: {peak1}") # 预期输出: 12

peak2 = find_peak_memory_in_sequence(nodes_scenario2)
print(f"场景2的峰值内存占用: {peak2}") # 预期输出: 8

# 边界情况：内存一直减少
nodes_scenario3 = [
    Node('A', 5, 2), # current = -3, peak = 0
    Node('B', 4, 1)  # current = -3 -3 = -6, peak = 0
]
peak3 = find_peak_memory_in_sequence(nodes_scenario3)
print(f"场景3的峰值内存占用 (一直减少): {peak3}") # 预期输出: 0 (因为我们初始化peak为0且只取更大的)

# 如果希望峰值可以为负（例如，追踪最大“赤字”）
def find_peak_memory_in_sequence_can_be_negative(nodes):
    if not nodes:
        return 0
    
    current_memory_usage = 0
    # 初始化为第一个操作后的状态，或者 float('-inf')
    # 为了简单，我们假设至少有一个节点
    delta_first = nodes[0].output_data - nodes[0].input_data
    current_memory_usage = delta_first
    peak_memory_usage = current_memory_usage
    
    for i in range(1, len(nodes)):
        node = nodes[i]
        delta = node.output_data - node.input_data
        current_memory_usage += delta
        if current_memory_usage > peak_memory_usage:
            peak_memory_usage = current_memory_usage
            
    return peak_memory_usage

print("\n允许负峰值的计算:")
peak3_neg = find_peak_memory_in_sequence_can_be_negative(nodes_scenario3)
print(f"场景3的峰值内存占用 (允许负峰值): {peak3_neg}") # 预期: -3 (因为-3 > -6)

nodes_scenario4 = [
    Node('A', 2, 5), # current = 3, peak = 3
    Node('B', 10, 1)  # current = 3 - 9 = -6, peak = 3
]
peak4_neg = find_peak_memory_in_sequence_can_be_negative(nodes_scenario4)
print(f"场景4的峰值内存占用 (允许负峰值): {peak4_neg}") # 预期: 3
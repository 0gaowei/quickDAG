import networkx as nx
import re
from collections import deque, defaultdict
import matplotlib.pyplot as plt
import numpy as np

def parse_dot_dag(filename):
    """解析DOT格式的DAG文件"""
    G = nx.DiGraph()
    memory_weights = {}
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # 解析节点
    node_pattern = r'(\d+)\s+\[size="([^"]+)",\s+alpha="([^"]+)"\]'
    for match in re.finditer(node_pattern, content):
        node_id, size, alpha = match.groups()
        # 转换大小为数值
        try:
            size_value = int(size)
        except ValueError:
            try:
                size_value = float(size)
            except ValueError:
                size_value = 0
        
        G.add_node(node_id, size=size_value, alpha=float(alpha))
    
    # 解析边
    edge_pattern = r'(\d+)\s+->\s+(\d+)\s+\[size\s*=\s*"([^"]+)"\]'
    for match in re.finditer(edge_pattern, content):
        src, dst, size = match.groups()
        G.add_edge(src, dst)
        # 转换内存权重为数值
        try:
            size_value = int(size)
        except ValueError:
            try:
                size_value = float(size)
            except ValueError:
                size_value = 0
        
        memory_weights[(src, dst)] = size_value
    
    return G, memory_weights

def standard_topological_sort(G, algorithm="dfs"):
    """
    标准拓扑排序实现
    algorithm: 'dfs' 或 'bfs'
    """
    if algorithm == "dfs":
        # DFS拓扑排序
        def dfs_topo_sort(graph):
            visited = set()
            topo_order = []
            
            def dfs(node):
                visited.add(node)
                for successor in graph.successors(node):
                    if successor not in visited:
                        dfs(successor)
                topo_order.append(node)
            
            for node in graph.nodes():
                if node not in visited:
                    dfs(node)
            
            return list(reversed(topo_order))
        
        return dfs_topo_sort(G)
    elif algorithm == "bfs":
        # BFS拓扑排序 (Kahn算法)
        in_degree = {node: G.in_degree(node) for node in G.nodes()}
        queue = deque([node for node in G.nodes() if in_degree[node] == 0])
        topo_order = []
        
        while queue:
            node = queue.popleft()
            topo_order.append(node)
            
            for successor in G.successors(node):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)
        
        return topo_order

def calculate_node_memory_lifecycle(G, topo_order, memory_weights):
    """
    计算每个节点输出内存的生命周期
    返回: {node_id: (start, end)}
    """
    node_to_index = {node: idx for idx, node in enumerate(topo_order)}
    lifecycle = {}
    
    # 计算每个节点的输出内存生命周期
    for node in G.nodes():
        idx = node_to_index[node]
        
        # 如果节点没有后继(输出)，则生命周期结束于其自身
        if G.out_degree(node) == 0:
            lifecycle[node] = (idx, idx)
            continue
        
        # 找到所有使用此节点输出的最后一个节点
        end_idx = idx
        for succ in G.successors(node):
            end_idx = max(end_idx, node_to_index[succ])
        
        lifecycle[node] = (idx, end_idx)
    
    return lifecycle

def identify_long_lifecycle_nodes(G, topo_order, lifecycle):
    """
    识别长生命周期的节点
    返回可移动的节点列表及其目标位置
    """
    node_to_index = {node: idx for idx, node in enumerate(topo_order)}
    nodes_to_move = []
    
    for node in G.nodes():
        if G.in_degree(node) == 0:  # 跳过源节点
            continue
        
        # 固定规则: 这里我们假设某些节点类型为长生命周期(在实际应用中需要根据节点类型判断)
        # 由于我们没有节点类型信息，这里模拟一下 - 假设节点ID为偶数的是特殊类型
        is_special_type = int(node) % 2 == 0
        
        # 动态规则: 计算输入内存最大生命周期L1和输出内存最小生命周期L2
        L1 = 0
        for pred in G.predecessors(node):
            if pred in lifecycle:
                L1 = max(L1, lifecycle[pred][1] - lifecycle[pred][0])
        
        L2 = float('inf')
        min_succ_idx = float('inf')
        for succ in G.successors(node):
            if succ in lifecycle:
                L2 = min(L2, lifecycle[succ][1] - lifecycle[succ][0])
                min_succ_idx = min(min_succ_idx, node_to_index[succ])
        
        if L2 == float('inf'):  # 没有后继节点
            continue
            
        # 应用长生命周期判断规则
        if is_special_type or L1 > L2:
            current_idx = node_to_index[node]
            target_idx = min_succ_idx - 1  # 移动到最靠前的输出节点前
            
            if target_idx > current_idx:  # 只有向后移动才有意义
                nodes_to_move.append((node, current_idx, target_idx))
    
    return nodes_to_move

def optimize_topo_order(topo_order, nodes_to_move):
    """
    优化拓扑排序，移动指定节点
    """
    # 按目标位置从后向前排序，以避免移动冲突
    nodes_to_move.sort(key=lambda x: -x[2])
    
    optimized_order = topo_order.copy()
    
    for node, current_idx, target_idx in nodes_to_move:
        # 从原位置移除
        optimized_order.pop(current_idx)
        
        # 由于移除了一个元素，如果target_idx > current_idx，需要调整目标索引
        if target_idx > current_idx:
            target_idx -= 1
        
        # 插入到新位置
        optimized_order.insert(target_idx, node)
    
    return optimized_order+

def calculate_memory_profile(G, topo_order, node_memory, edge_memory):
    """
    计算内存使用profile和理论最小值
    """
    node_to_index = {node: idx for idx, node in enumerate(topo_order)}
    memory_profile = [0] * (len(topo_order) + 1)
    
    # 计算每个时间点的内存占用
    for node in G.nodes():
        idx = node_to_index[node]
        
        # 节点自身的内存占用
        memory_size = node_memory.get(node, 0)
        memory_profile[idx] += memory_size
        
        # 处理输出边的内存
        for succ in G.successors(node):
            edge = (node, succ)
            if edge in edge_memory:
                edge_size = edge_memory[edge]
                end_idx = node_to_index[succ]
                
                # 从节点生成开始到被消费前，边的内存占用增加
                for i in range(idx, end_idx + 1):
                    memory_profile[i] += edge_size
    
    # 理论最小值是内存profile的最大值
    peak_memory = max(memory_profile)
    return peak_memory, memory_profile

def visualize_memory_profile(before_profile, after_profile):
    """可视化优化前后的内存profile"""
    plt.figure(figsize=(12, 6))
    
    x_before = np.arange(len(before_profile))
    x_after = np.arange(len(after_profile))
    
    plt.plot(x_before, before_profile, 'b-', label='优化前')
    plt.plot(x_after, after_profile, 'r-', label='优化后')
    
    plt.xlabel('执行时间点')
    plt.ylabel('内存占用')
    plt.title('Topo排序优化前后的内存占用对比')
    plt.legend()
    plt.grid(True)
    
    # 标注最大值
    max_before = max(before_profile)
    max_after = max(after_profile)
    
    idx_before = before_profile.index(max_before)
    idx_after = after_profile.index(max_after)
    
    plt.annotate(f'峰值: {format_memory_size(max_before)}', 
                xy=(idx_before, max_before), 
                xytext=(idx_before, max_before*1.1),
                arrowprops=dict(facecolor='black', shrink=0.05))
    
    plt.annotate(f'峰值: {format_memory_size(max_after)}', 
                xy=(idx_after, max_after), 
                xytext=(idx_after, max_after*1.1),
                arrowprops=dict(facecolor='black', shrink=0.05))
    
    plt.savefig('memory_profile_comparison.png')
    plt.show()

def format_memory_size(size):
    """将内存大小格式化为人类可读的形式"""
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    index = 0
    size_float = float(size)
    while size_float >= 1024 and index < len(suffixes) - 1:
        size_float /= 1024
        index += 1
    return f"{size_float:.2f} {suffixes[index]}"

def apply_topo_optimization(dag_file):
    """应用Topo排序优化流程"""
    # 1. 解析DAG
    G, edge_memory = parse_dot_dag(dag_file)
    
    # 提取节点内存大小
    node_memory = {node: G.nodes[node].get('size', 0) for node in G.nodes()}
    
    # 2. 应用常规拓扑排序
    standard_order = standard_topological_sort(G, "bfs")
    print(f"标准DFS拓扑排序: {standard_order}")
    
    # 3. 计算节点内存生命周期
    lifecycle = calculate_node_memory_lifecycle(G, standard_order, edge_memory)
    
    # 4. 识别长生命周期节点
    nodes_to_move = identify_long_lifecycle_nodes(G, standard_order, lifecycle)
    print(f"需要移动的节点: {nodes_to_move}")
    
    # 5. 优化拓扑排序
    optimized_order = optimize_topo_order(standard_order, nodes_to_move)
    print(f"优化后的拓扑排序: {optimized_order}")
    
    # 6. 计算优化前后的内存理论最小值
    before_peak, before_profile = calculate_memory_profile(G, standard_order, node_memory, edge_memory)
    after_peak, after_profile = calculate_memory_profile(G, optimized_order, node_memory, edge_memory)
    
    # 7. 输出优化结果
    print(f"\n优化前内存理论最小值: {before_peak} ({format_memory_size(before_peak)})")
    print(f"优化后内存理论最小值: {after_peak} ({format_memory_size(after_peak)})")
    
    if before_peak > after_peak:
        reduction = before_peak - after_peak
        reduction_percentage = (reduction / before_peak) * 100
        print(f"内存减少: {reduction} ({format_memory_size(reduction)}), 减少率: {reduction_percentage:.2f}%")
    else:
        print("本例中Topo优化未能降低内存理论最小值")
    
    # 8. 可视化内存profile
    visualize_memory_profile(before_profile, after_profile)
    
    return {
        "standard_order": standard_order,
        "optimized_order": optimized_order,
        "before_peak": before_peak,
        "after_peak": after_peak,
        "before_profile": before_profile,
        "after_profile": after_profile
    }

if __name__ == "__main__":
    # 应用到提供的DAG文件
    dag_file = "./dag_src/dag-default.txt"
    result = apply_topo_optimization(dag_file)

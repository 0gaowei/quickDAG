import networkx as nx
from collections import deque
import re

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
        # 转换大小为数值，但保留字符串类型的节点ID
        try:
            size_value = int(size)
        except ValueError:
            try:
                size_value = float(size)
            except ValueError:
                size_value = size  # 保持原样如果无法转换
        
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
                size_value = 0  # 默认为0如果无法转换
        
        memory_weights[(src, dst)] = size_value
    
    return G, memory_weights

def compute_max_memory(dag, memory_weights):
    """
    计算DAG的最大内存峰值
    
    参数:
    dag: networkx DiGraph对象，表示有向无环图
    memory_weights: dict, 边的权重，表示内存需求
    
    返回:
    max_memory: 最大内存峰值
    cut: 产生最大内存峰值的拓扑切割
    """
    # 确保图中有唯一的源点s和汇点t
    source_nodes = [n for n in dag.nodes() if dag.in_degree(n) == 0]
    sink_nodes = [n for n in dag.nodes() if dag.out_degree(n) == 0]
    
    if len(source_nodes) != 1 or len(sink_nodes) != 1:
        raise ValueError(f"图必须有唯一的源点和汇点。当前源点: {source_nodes}, 汇点: {sink_nodes}")
    
    s = source_nodes[0]
    t = sink_nodes[0]
    
    # 步骤1: 构造初始流
    f_max = 1 + sum(memory_weights.values())
    initial_flow = {(i, j): f_max for (i, j) in dag.edges()}
    
    # 步骤2: 图形转换 - 构造G+
    G_plus = nx.DiGraph()
    for (i, j) in dag.edges():
        G_plus.add_edge(i, j, capacity=initial_flow[(i, j)] - memory_weights[(i, j)])
    
    # 步骤3: 在G+上计算最大流
    max_flow_value, max_flow = nx.maximum_flow(G_plus, s, t)
    
    # 步骤4: 构建残差网络并找到从s可达的节点集合
    residual = nx.DiGraph()
    
    # 添加原始边的残差容量
    for (i, j) in G_plus.edges():
        capacity = G_plus[i][j]['capacity']
        flow = max_flow[i].get(j, 0)
        if flow < capacity:
            residual.add_edge(i, j, capacity=capacity-flow)
        if flow > 0:
            residual.add_edge(j, i, capacity=flow)
    
    # 找到从s可达的节点集合S
    S = set()
    queue = deque([s])
    S.add(s)
    
    while queue:
        node = queue.popleft()
        for neighbor in list(residual.successors(node)):
            if neighbor not in S:
                S.add(neighbor)
                queue.append(neighbor)
    
    # 步骤5: 构造拓扑切割
    T = set(dag.nodes()) - S
    cut_edges = [(i, j) for (i, j) in dag.edges() if i in S and j in T]
    
    # 计算切割的权重和，即最大内存峰值
    max_memory = sum(memory_weights[(i, j)] for (i, j) in cut_edges)
    
    return max_memory, (S, T)

def format_memory_size(size):
    """将内存大小格式化为人类可读的形式"""
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    index = 0
    while size >= 1024 and index < len(suffixes) - 1:
        size /= 1024
        index += 1
    return f"{size:.2f} {suffixes[index]}"

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print(f"用法: python {sys.argv[0]} <dag_file>")
        sys.exit(1)
    
    dag_file = sys.argv[1]
    G, memory_weights = parse_dot_dag(dag_file)
    
    print(f"读取DAG完成: {len(G.nodes())}个节点, {len(G.edges())}条边")
    
    try:
        max_memory, cut = compute_max_memory(G, memory_weights)
        
        print(f"最大内存峰值: {max_memory} ({format_memory_size(max_memory)})")
        print(f"对应的拓扑切割:")
        print(f"  集合S ({len(cut[0])}个节点): {sorted(cut[0])}")
        print(f"  集合T ({len(cut[1])}个节点): {sorted(cut[1])}")
        
        cut_edges = [(i, j) for (i, j) in G.edges() if i in cut[0] and j in cut[1]]
        print(f"切割边 ({len(cut_edges)}条):")
        total_weight = 0
        for i, j in cut_edges:
            weight = memory_weights[(i, j)]
            total_weight += weight
            print(f"  {i} -> {j}: 内存权重 = {weight} ({format_memory_size(weight)})")
        
        print(f"验证切割总权重: {total_weight} ({format_memory_size(total_weight)})")
    
    except ValueError as e:
        print(f"错误: {e}")
        
        # 打印DAG的源节点和汇点信息
        source_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
        sink_nodes = [n for n in G.nodes() if G.out_degree(n) == 0]
        
        print(f"源节点 ({len(source_nodes)}个): {source_nodes}")
        print(f"汇点 ({len(sink_nodes)}个): {sink_nodes}")

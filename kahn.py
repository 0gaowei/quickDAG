from collections import deque, defaultdict

# 构建图和入度字典
def build_graph(file_content):
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    nodes = set()
    edges = []

    for line in file_content:
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        if '->' in line:
            parts = line.split('->')
            start = parts[0].strip()
            end = parts[1].split()[0].strip()
            graph[start].append(end)
            in_degree[end] += 1
            nodes.update([start, end])
            edges.append((start, end))
        elif '[' in line and ']' in line:
            node = line.split()[0]
            nodes.add(node)
            if node not in in_degree:
                in_degree[node] = 0

    return graph, in_degree, nodes, edges

# Kahn算法实现拓扑排序
def kahn_topological_sort(graph, in_degree):
    queue = deque([node for node in in_degree if in_degree[node] == 0])
    topo_order = []

    while queue:
        node = queue.popleft()
        topo_order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(topo_order) == len(in_degree):
        return topo_order
    else:
        raise ValueError("Graph has a cycle, topological sort not possible")

# 输出DOT文件
def export_dot_file(output_path, topo_order, edges):
    with open(output_path, 'w') as f:
        f.write("digraph G {\n")
        for node in topo_order:
            f.write(f"  {node};\n")
        for src, dst in edges:
            if src in topo_order and dst in topo_order:
                f.write(f"  {src} -> {dst};\n")
        f.write("}\n")

# 主程序
file_path = './dag_src/dag-default.txt'
output_path = './dag_src/topo_kahn_output.dot'

with open(file_path, 'r') as file:
    file_content = file.readlines()

graph, in_degree, nodes, edges = build_graph(file_content)
topological_order = kahn_topological_sort(graph, in_degree)

print("拓扑排序结果:", topological_order)
export_dot_file(output_path, topological_order, edges)
print(f"DOT 格式文件已输出至: {output_path}")

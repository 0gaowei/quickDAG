import re
import heapq
from collections import defaultdict

def parse_dot_file(filepath):
    adj = defaultdict(list)           # 出边列表
    indegree = defaultdict(int)       # 入度计数
    incoming_sizes = defaultdict(list) # 每个节点的入边 size 列表
    outgoing_sizes = defaultdict(list) # 每个节点的出边 size 列表
    edge_list = []                    # 记录所有边 (src, dst)

    node_pattern = re.compile(r'^\s*(\d+)\s+\[.*\]$')
    edge_pattern = re.compile(r'^\s*(\d+)\s*->\s*(\d+)\s*\[size\s*=\s*"(\d+)"\]')

    with open(filepath, 'r') as f:
        for line in f:
            node_match = node_pattern.match(line)
            edge_match = edge_pattern.match(line)

            if node_match:
                node = int(node_match.group(1))
                indegree[node] += 0  # 初始化节点

            elif edge_match:
                src = int(edge_match.group(1))
                dst = int(edge_match.group(2))
                size = int(edge_match.group(3))

                adj[src].append(dst)
                indegree[dst] += 1
                incoming_sizes[dst].append(size)
                outgoing_sizes[src].append(size)
                edge_list.append((src, dst))

    return adj, indegree, incoming_sizes, outgoing_sizes, edge_list

def memory_aware_topo_sort(adj, indegree, incoming_sizes):
    topo_order = []
    heap = []

    for node in indegree:
        if indegree[node] == 0:
            released_memory = sum(incoming_sizes[node])
            heapq.heappush(heap, (-released_memory, node))  # 最大堆

    while heap:
        _, node = heapq.heappop(heap)
        topo_order.append(node)

        for neighbor in adj[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                released_memory = sum(incoming_sizes[neighbor])
                heapq.heappush(heap, (-released_memory, neighbor))

    return topo_order

def export_dot_file(filename, topo_nodes, edge_list):
    with open(filename, 'w') as f:
        f.write("digraph G {\n")
        for node in topo_nodes:
            f.write(f"  {node};\n")
        for src, dst in edge_list:
            if src in topo_nodes and dst in topo_nodes:
                f.write(f"  {src} -> {dst};\n")
        f.write("}\n")

# ✅ 修改你的静态路径
if __name__ == "__main__":
    filepath = './dag_src/dag-default.txt'
    output_path = './dag_src/releasefirst_sorted_output.dot'

    adj, indegree, incoming_sizes, outgoing_sizes, edge_list = parse_dot_file(filepath)
    order = memory_aware_topo_sort(adj, indegree, incoming_sizes)

    print("Topological order (memory-aware, release-first):")
    print(order)

    export_dot_file(output_path, order, edge_list)
    print(f"DOT output written to: {output_path}")

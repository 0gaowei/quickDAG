import re
import heapq
import sys
from collections import defaultdict

'''
用法:
python min_inmem_alloc.py <DAG文件路径> <输出DOT文件路径>
'''

def parse_dot_file(filepath):
    adj = defaultdict(list)           # 出边列表
    indegree = defaultdict(int)       # 入度计数
    incoming_sizes = defaultdict(list) # 每个节点的入边 size 列表
    outgoing_sizes = defaultdict(list) # 每个节点的出边 size 列表
    edge_list = []                    # 所有边列表

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

def memory_aware_topo_sort_min_allocate(adj, indegree, outgoing_sizes):
    topo_order = []
    heap = []

    for node in indegree:
        if indegree[node] == 0:
            allocated_memory = sum(outgoing_sizes[node])
            heapq.heappush(heap, (allocated_memory, node))  # 最小分配优先

    while heap:
        _, node = heapq.heappop(heap)
        topo_order.append(node)

        for neighbor in adj[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                allocated_memory = sum(outgoing_sizes[neighbor])
                heapq.heappush(heap, (allocated_memory, neighbor))

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

def main():
    # 检查命令行参数
    if len(sys.argv) != 3:
        print("用法: python min_inmem_alloc.py <DAG文件路径> <输出DOT文件路径>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    output_path = sys.argv[2]
    
    try:
        adj, indegree, incoming_sizes, outgoing_sizes, edge_list = parse_dot_file(filepath)
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{filepath}'")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 解析文件时出错 - {str(e)}")
        sys.exit(1)
    
    try:
        order = memory_aware_topo_sort_min_allocate(adj, indegree, outgoing_sizes)
        
        print("拓扑排序结果 (内存感知, 最小分配优先):")
        print(order)
        
        export_dot_file(output_path, order, edge_list)
        print(f"DOT 格式文件已输出至: {output_path}")
    except Exception as e:
        print(f"错误: 处理过程中出错 - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

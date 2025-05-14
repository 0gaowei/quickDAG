import re
import os


def parse_dag_file(dag_file_path):
    """解析DAG图文件，提取节点和边的信息"""
    nodes = {}
    edges = []

    if not os.path.exists(dag_file_path):
        print(f"警告: DAG文件不存在: {dag_file_path}")
        return nodes

    with open(dag_file_path, 'r') as f:
        lines = f.readlines()

    print(f"DAG文件包含 {len(lines)} 行")

    for line in lines:
        # 匹配边信息：源节点、目标节点和边的size
        edge_match = re.match(r'(\d+)\s+->\s+(\d+)\s+\[size\s*=\s*["\'"]?(\d+)["\'"]?', line.strip())
        if edge_match:
            src = int(edge_match.group(1))
            dst = int(edge_match.group(2))
            edge_size = int(edge_match.group(3))
            edges.append((src, dst, edge_size))

            # 确保节点存在于字典中
            if src not in nodes:
                nodes[src] = {"in_edges": [], "out_edges": []}
            if dst not in nodes:
                nodes[dst] = {"in_edges": [], "out_edges": []}

            # 添加出入边记录
            nodes[src]["out_edges"].append((dst, edge_size))
            nodes[dst]["in_edges"].append((src, edge_size))

    print(f"解析到 {len(nodes)} 个节点和 {len(edges)} 条边")
    return nodes


def calculate_memory_change(nodes):
    """计算每个节点的内存变化量"""
    memory_change = {}

    for node_id, node_info in nodes.items():
        # 计算出度总size
        out_size = sum(edge_size for _, edge_size in node_info["out_edges"])

        # 计算入度总size
        in_size = sum(edge_size for _, edge_size in node_info["in_edges"])

        # 计算内存变化量
        memory_change[node_id] = out_size - in_size

    return memory_change


def parse_topological_order(topo_file_path):
    """从文件中提取拓扑序列"""
    topo_order = []

    if not os.path.exists(topo_file_path):
        print(f"警告: 拓扑序文件不存在: {topo_file_path}")
        return topo_order

    with open(topo_file_path, 'r') as f:
        lines = f.readlines()

    print(f"拓扑序文件包含 {len(lines)} 行")

    # 打印前10行帮助调试
    print("拓扑序文件前10行内容预览:")
    for i, line in enumerate(lines[:10]):
        print(f"{i + 1}: {line.strip()}")

    # 解析拓扑序列，忽略首尾行（digraph G { 和 }）以及边的定义行
    for line in lines[1:-1]:  # 跳过第一行和最后一行
        line = line.strip()
        if "->" not in line and line.endswith(";"):
            # 如果是节点定义行（如 "1;"），提取节点ID
            node_id = line.rstrip(";").strip()
            if node_id.isdigit():
                topo_order.append(int(node_id))

    if not topo_order:
        print("未能解析拓扑序，尝试备用方法...")
        for line in lines:
            # 尝试直接提取数字
            line = line.strip()
            if line.isdigit():
                topo_order.append(int(line))
            elif line.endswith(";") and line[:-1].isdigit():
                topo_order.append(int(line[:-1]))

    return topo_order


def calculate_peak_memory(memory_changes, topo_order):
    """根据拓扑序列计算最大内存占用"""
    current_memory = 0
    peak_memory = 0

    for node_id in topo_order:
        if node_id in memory_changes:
            current_memory += memory_changes[node_id]
            peak_memory = max(peak_memory, current_memory)

    return peak_memory


def main():
    # 文件路径
    dag_file = "./dag_src/dag-default.txt"  # 使用用户提供的文件路径
    topo_file = "./dag_src/topo_kahn_output.dot"  # 使用用户提供的文件路径

    # 解析DAG文件并计算内存变化量
    nodes = parse_dag_file(dag_file)
    if not nodes:
        print("错误: 未能解析任何节点，请检查DAG文件格式")
        return

    memory_changes = calculate_memory_change(nodes)

    # 解析拓扑序文件
    topo_order = parse_topological_order(topo_file)

    # 如果拓扑序列为空，则尝试其它解析方法
    if not topo_order:
        print("拓扑序列为空，尝试其它解析方法...")

        try:
            with open(topo_file, 'r') as f:
                content = f.read()
                # 尝试从文件中提取数字序列
                topo_order = [int(num) for num in re.findall(r'\b\d+\b', content)
                              if not re.search(r'->.*' + num, content)]  # 排除边定义中的数字
            print(f"使用正则表达式提取到 {len(topo_order)} 个节点")
        except Exception as e:
            print(f"解析拓扑序时出错: {e}")

    if not topo_order:
        print("警告: 无法解析拓扑序列，请检查文件格式")
        return

    # 过滤拓扑序中不在DAG中的节点
    valid_topo_order = [node for node in topo_order if node in memory_changes]
    if len(valid_topo_order) < len(topo_order):
        print(f"警告: 拓扑序中有 {len(topo_order) - len(valid_topo_order)} 个节点不在DAG中")
        topo_order = valid_topo_order

    # 计算最大内存占用
    peak_memory = calculate_peak_memory(memory_changes, topo_order)

    print("\n节点的内存变化量:")
    for node_id, change in sorted(memory_changes.items()):
        print(f"节点 {node_id}: {change}")

    print(f"\n拓扑序列 (共 {len(topo_order)} 个节点):")
    print(topo_order[:20])  # 只显示前20个节点，避免输出过长
    if len(topo_order) > 20:
        print(f"... 以及其它 {len(topo_order) - 20} 个节点")

    print(f"\n在给定拓扑序下的最大内存占用: {peak_memory}")

    return peak_memory


if __name__ == "__main__":
    main()

import re
import heapq
import os
from collections import defaultdict, deque

class Node:
    def __init__(self, id, size, alpha):
        self.id = id
        self.size = size  # 节点大小
        self.alpha = alpha  # alpha值，可用于优先级计算
        self.in_edges = []  # 入边列表 [(source_id, edge_size), ...]
        self.out_edges = [] # 出边列表 [(target_id, edge_size), ...]
        self.constraints = []  # 节点约束列表

class DAG:
    def __init__(self):
        self.nodes = {}  # id -> Node
        self.edges = []  # [(source, target, size), ...]
        self.constraints = {}  # 节点约束: {node_id: priority_level, ...}
    
    def parse_dot_file(self, file_path):
        """从文件解析DOT格式的DAG图"""
        try:
            with open(file_path, 'r') as f:
                dot_content = f.read()
            self.parse_dot(dot_content)
            print(f"成功从 {file_path} 读取DAG图")
            return True
        except Exception as e:
            print(f"读取文件 {file_path} 失败: {str(e)}")
            return False
    
    def parse_dot(self, dot_content):
        """解析DOT格式的DAG图"""
        # 解析节点
        node_pattern = r'(\d+)\s+\[size="([^"]+)",\s+alpha="([^"]+)"\]'
        for match in re.finditer(node_pattern, dot_content):
            node_id, size_str, alpha_str = match.groups()
            node_id = int(node_id)
            # 将size转换为整数
            try:
                size = int(size_str)
            except ValueError:
                # 如果size不是简单的整数，暂时设为1
                size = 1
            alpha = float(alpha_str)
            self.nodes[node_id] = Node(node_id, size, alpha)
        
        # 解析边
        edge_pattern = r'(\d+)\s+->\s+(\d+)\s+\[size\s+=\s*"([^"]+)"\]'
        for match in re.finditer(edge_pattern, dot_content):
            source_id, target_id, size_str = match.groups()
            source_id, target_id = int(source_id), int(target_id)
            size = int(size_str)
            
            # 添加边信息
            self.edges.append((source_id, target_id, size))
            
            # 更新节点的入边和出边信息
            if source_id in self.nodes and target_id in self.nodes:
                self.nodes[source_id].out_edges.append((target_id, size))
                self.nodes[target_id].in_edges.append((source_id, size))
    
    def set_node_constraints(self, constraints):
        """设置节点约束
        constraints: {node_id: priority_level, ...} 
        优先级值越小，越优先执行
        """
        self.constraints = constraints
        for node_id, priority in constraints.items():
            if node_id in self.nodes:
                self.nodes[node_id].constraints.append(("priority", priority))
    
    def kahn_topological_sort(self):
        """使用Kahn算法进行拓扑排序"""
        # 计算每个节点的入度
        in_degree = {node_id: len(node.in_edges) for node_id, node in self.nodes.items()}
        
        # 找到所有入度为0的节点
        queue = []
        for node_id, degree in in_degree.items():
            if degree == 0:
                # 考虑节点约束作为优先级
                priority = self.constraints.get(node_id, 0)
                heapq.heappush(queue, (priority, node_id))
        
        result = []
        
        while queue:
            _, node_id = heapq.heappop(queue)
            result.append(node_id)
            
            # 减少相邻节点的入度
            for target_id, _ in self.nodes[node_id].out_edges:
                in_degree[target_id] -= 1
                if in_degree[target_id] == 0:
                    priority = self.constraints.get(target_id, 0)
                    heapq.heappush(queue, (priority, target_id))
        
        if len(result) != len(self.nodes):
            raise ValueError("图中存在环路，无法进行拓扑排序")
        
        return result
    
    def simulate_memory(self, execution_order):
        """模拟执行过程中的内存变化，并打印详细计算过程"""
        current_memory = 0
        max_memory = 0
        memory_trace = []
        
        # print("\n====== 内存变化详细计算过程 ======")
        # print(f"初始内存: {current_memory}")
        
        # 构建节点到执行顺序的映射
        execution_time = {node_id: idx for idx, node_id in enumerate(execution_order)}
        
        # 记录每条边的数据何时可以被释放
        edge_release_time = {}
        for source_id, target_id, size in self.edges:
            # 边的数据在目标节点执行后可以释放
            edge_release_time[(source_id, target_id)] = execution_time[target_id]
        
        # 按执行顺序模拟内存变化
        for idx, node_id in enumerate(execution_order):
            node = self.nodes[node_id]
            
            # print(f"\n>> 执行节点 {node_id} <<")
            # print(f"  开始时内存: {current_memory}")
            
            memory_changes = []
            
            # 如果是起始节点，只添加出边内存
            if not node.in_edges:  # 起始节点
                # print(f"  节点 {node_id} 是起始节点，只添加出边数据")
                for target_id, out_size in node.out_edges:
                    current_memory += out_size
                    memory_changes.append(("+", target_id, out_size))
                    # print(f"  添加出边 {node_id}->{target_id} 数据: +{out_size} 当前内存: {current_memory}")
            
            # 如果是终止节点，只减去入边内存
            elif not node.out_edges:  # 终止节点
                # print(f"  节点 {node_id} 是终止节点，只减去入边数据")
                for source_id, in_size in node.in_edges:
                    current_memory -= in_size
                    memory_changes.append(("-", source_id, in_size))
                    # print(f"  减去入边 {source_id}->{node_id} 数据: -{in_size} 当前内存: {current_memory}")
            
            # 中间节点，减去入边，加上出边
            else:
                # print(f"  节点 {node_id} 是中间节点")
                
                # 减去入边数据
                for source_id, in_size in node.in_edges:
                    current_memory -= in_size
                    memory_changes.append(("-", source_id, in_size))
                    # print(f"计算前内存: {current_memory}  减去入边 {source_id}->{node_id} 数据: -{in_size} 当前内存: {current_memory}")
                    
                # 添加出边数据
                for target_id, out_size in node.out_edges:
                    current_memory += out_size
                    memory_changes.append(("+", target_id, out_size))
                    # print(f"  添加出边 {node_id}->{target_id} 数据: +{out_size} 当前内存: {current_memory}")
            
            # 汇总内存变化
            if memory_changes:
                in_sum = sum(size for op, _, size in memory_changes if op == "-")
                out_sum = sum(size for op, _, size in memory_changes if op == "+")
                net_change = out_sum - in_sum
                # if net_change >= 0:
                    # print(f"  内存净变化: +{net_change} (减少: {in_sum}, 增加: {out_sum})")
                # else:
                    # print(f"  内存净变化: {net_change} (减少: {in_sum}, 增加: {out_sum})")
            
            # 更新最大内存
            if current_memory > max_memory:
                max_memory = current_memory
                # print(f"  *** 新的内存峰值: {max_memory} ***")
            
            # print(f"  结束时内存: {current_memory}")
            memory_trace.append((node_id, current_memory))
        
        # print(f"最终内存: {current_memory}")
        # print(f"内存峰值: {max_memory}")
        # print("====== 内存模拟结束 ======\n")
        
        return max_memory, memory_trace

    
    def optimize_execution_order(self):
        """优化执行顺序，尝试减少内存峰值"""
        # 基本拓扑排序作为初始顺序
        base_order = self.kahn_topological_sort()
        best_order = base_order
        best_memory, _ = self.simulate_memory(base_order)
        
        # 使用贪心策略：在每步选择能最大程度减少当前内存的节点
        def greedy_memory_optimization():
            in_degree = {node_id: len(node.in_edges) for node_id, node in self.nodes.items()}
            result = []
            available = []  # 存储可执行的节点
            current_memory = 0
            
            # 初始化：添加所有入度为0的节点到可执行列表
            for node_id, degree in in_degree.items():
                if degree == 0:
                    # 计算该节点的内存增长 (出边总和)
                    node = self.nodes[node_id]
                    out_sum = sum(size for _, size in node.out_edges)
                    # 考虑节点约束
                    constraint_priority = self.constraints.get(node_id, 0)
                    # 优先执行约束优先级高的节点，其次考虑内存影响
                    heapq.heappush(available, (constraint_priority, out_sum, node_id))
            
            while available:
                # 选择优先级最高的节点，如果优先级相同则选择产生最小输出的节点
                _, _, node_id = heapq.heappop(available)
                result.append(node_id)
                
                node = self.nodes[node_id]
                
                # 更新内存：加上出边数据
                for _, out_size in node.out_edges:
                    current_memory += out_size
                
                # 减少相邻节点的入度，并检查是否有新的可执行节点
                for target_id, _ in node.out_edges:
                    in_degree[target_id] -= 1
                    if in_degree[target_id] == 0:
                        next_node = self.nodes[target_id]
                        out_sum = sum(size for _, size in next_node.out_edges)
                        constraint_priority = self.constraints.get(target_id, 0)
                        heapq.heappush(available, (constraint_priority, out_sum, target_id))
                
                # 减去入边数据（模拟释放）
                for _, in_size in node.in_edges:
                    current_memory -= in_size
            
            # 验证结果是否是有效的拓扑排序
            if len(result) != len(self.nodes):
                print("警告：贪心策略未能生成有效的拓扑排序")
                return base_order
            
            return result
        
        # 策略1: 考虑节点约束的贪心优化
        greedy_order = greedy_memory_optimization()
        greedy_memory, _ = self.simulate_memory(greedy_order)
        if greedy_memory < best_memory:
            print("策略1: 贪心优化，内存峰值减少")
            best_order = greedy_order
            best_memory = greedy_memory
        print("\n贪心优化后的排序:", greedy_order)
        print("贪心优化后内存峰值:", greedy_memory)
        print("内存优化效果: {:.2f}%".format((best_memory - greedy_memory) / best_memory * 100))
        
        # 策略2: 优先释放大数据，同时考虑节点约束
        def big_data_release_optimization():
            in_degree = {node_id: len(node.in_edges) for node_id, node in self.nodes.items()}
            result = []
            available = []
            
            # 添加所有入度为0的节点
            for node_id, degree in in_degree.items():
                if degree == 0:
                    constraint_priority = self.constraints.get(node_id, 0)
                    heapq.heappush(available, (constraint_priority, 0, node_id))  # (约束优先级, 释放内存, 节点ID)
            
            # 记录当前正在使用的边
            active_edges = set()
            
            while available:
                _, _, node_id = heapq.heappop(available)
                result.append(node_id)
                node = self.nodes[node_id]
                
                # 更新活跃边
                for source_id, _ in node.in_edges:
                    if (source_id, node_id) in active_edges:
                        active_edges.remove((source_id, node_id))
                
                # 添加出边到活跃边
                for target_id, _ in node.out_edges:
                    active_edges.add((node_id, target_id))
                
                # 减少相邻节点的入度
                for target_id, _ in node.out_edges:
                    in_degree[target_id] -= 1
                    if in_degree[target_id] == 0:
                        # 计算该节点可以释放的内存
                        release_memory = 0
                        for source_id, edge_size in self.nodes[target_id].in_edges:
                            if source_id in result:
                                release_memory += edge_size
                        
                        constraint_priority = self.constraints.get(target_id, 0)
                        # 优先级排序: 先看约束优先级，再看释放内存量
                        heapq.heappush(available, (constraint_priority, -release_memory, target_id))
            
            return result
        
        release_order = big_data_release_optimization()
        release_memory, _ = self.simulate_memory(release_order)
        if release_memory < best_memory:
            print("策略2: 优先释放大数据，内存峰值减少")
            best_order = release_order
            best_memory = release_memory
        print("\n优先释放大数据后的排序:", release_order)
        print("优先释放大数据后内存峰值:", release_memory)
        print("内存优化效果: {:.2f}%".format((best_memory - release_memory) / best_memory * 100))
        
        # 策略3: 混合策略 - 考虑节点约束、输出大小和释放内存
        def hybrid_optimization():
            in_degree = {node_id: len(node.in_edges) for node_id, node in self.nodes.items()}
            result = []
            available = []
            current_memory = 0
            
            # 添加所有入度为0的节点
            for node_id, degree in in_degree.items():
                if degree == 0:
                    node = self.nodes[node_id]
                    constraint_priority = self.constraints.get(node_id, 0)
                    out_sum = sum(size for _, size in node.out_edges)
                    # 综合考虑约束优先级和输出大小
                    score = constraint_priority * 1000 + out_sum  # 约束优先级权重更大
                    heapq.heappush(available, (score, node_id))
            
            while available:
                _, node_id = heapq.heappop(available)
                result.append(node_id)
                node = self.nodes[node_id]
                
                # 更新内存：加上出边
                for _, out_size in node.out_edges:
                    current_memory += out_size
                
                # 减去入边（释放内存）
                for _, in_size in node.in_edges:
                    current_memory -= in_size
                
                # 减少相邻节点的入度，并检查是否有新的可执行节点
                for target_id, _ in node.out_edges:
                    in_degree[target_id] -= 1
                    if in_degree[target_id] == 0:
                        next_node = self.nodes[target_id]
                        constraint_priority = self.constraints.get(target_id, 0)
                        
                        # 计算执行该节点后的内存变化
                        memory_change = sum(size for _, size in next_node.out_edges) - sum(size for _, size in next_node.in_edges)
                        
                        # 综合考虑约束优先级和内存变化
                        score = constraint_priority * 1000 + memory_change
                        heapq.heappush(available, (score, target_id))
            
            return result
        
        hybrid_order = hybrid_optimization()
        hybrid_memory, _ = self.simulate_memory(hybrid_order)
        if hybrid_memory < best_memory:
            print("策略3: 混合优化，内存峰值减少")
            best_order = hybrid_order
            best_memory = hybrid_memory
        print("\n混合优化后的排序:", hybrid_order)
        print("混合优化后内存峰值:", hybrid_memory)
        print("内存优化效果: {:.2f}%".format((best_memory - hybrid_memory) / best_memory * 100))
        
        # 输出最佳结果
        return best_order, best_memory

# 测试代码
def main():
    dag_file_path = "./dag_src/dag-default.txt"
    
    dag = DAG()
    if not dag.parse_dot_file(dag_file_path):
        print(f"无法读取DAG文件 {dag_file_path}，程序退出")
        return
    
    # 设置节点约束 (示例，根据实际需求调整)
    # 这里设置某些节点的执行优先级，数字越小优先级越高
    node_constraints = {
        1: 0,  # 起始节点最高优先级
        4: 2,  # 节点4优先级较高
        7: 1,  # 节点7优先级次高
        12: 0  # 终止节点最高优先级
    }
    dag.set_node_constraints(node_constraints)
    
    print(f"节点约束: {node_constraints}")
    
    # 基本拓扑排序 (考虑节点约束)
    basic_order = dag.kahn_topological_sort()
    basic_memory, _ = dag.simulate_memory(basic_order)
    print("\n基本拓扑排序:", basic_order)
    print("内存峰值:", basic_memory)
    
    # 优化排序 (考虑节点约束)
    optimized_order, optimized_memory = dag.optimize_execution_order()
    print("\n优化后的排序:", optimized_order)
    print("优化后内存峰值:", optimized_memory)
    
    if basic_memory > 0:
        print(f"内存优化效果: {(basic_memory - optimized_memory) / basic_memory * 100:.2f}%")
    
    # 打印内存变化过程
    _, memory_trace = dag.simulate_memory(optimized_order)
    print("\n内存变化过程:")
    for node_id, memory in memory_trace:
        print(f"执行节点 {node_id} 后，内存使用: {memory}")

if __name__ == "__main__":
    main()

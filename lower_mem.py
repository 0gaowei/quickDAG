import re
import heapq
import os
from collections import defaultdict, deque
import sys

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
        base_memory = best_memory
        best_method = "base"
        
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
            print("!!!!!!!!!!!!!!!!!!!!!策略1: 贪心优化，内存峰值减少!!!!!!!!!!!!!!!!!!!!!")
            best_method="贪心策略"
            best_order = greedy_order
            best_memory = greedy_memory
        print("贪心优化后的排序:", greedy_order)
        print("贪心优化后内存峰值:", greedy_memory)
        print("内存优化效果: {:.2f}%".format((base_memory - greedy_memory) / base_memory * 100), "\n")
        
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
            print("!!!!!!!!!!!!!!!!!!!!!策略2: 优先释放大数据，内存峰值减少!!!!!!!!!!!!!!!!!!!!!!")
            best_method="优先释放大数据"
            best_order = release_order
            best_memory = release_memory
        print("优先释放大数据后的排序:", release_order)
        print("优先释放大数据后内存峰值:", release_memory)
        print("内存优化效果: {:.2f}%".format((base_memory - release_memory) / base_memory * 100), "\n")
        
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
            print("!!!!!!!!!!!!!!!!!!!!!策略3: 混合优化，内存峰值减少!!!!!!!!!!!!!!!!!!!!!")
            best_method="混合优化"
            best_order = hybrid_order
            best_memory = hybrid_memory
        print("混合优化后的排序:", hybrid_order)
        print("混合优化后内存峰值:", hybrid_memory)
        print("内存优化效果: {:.2f}%".format((base_memory - hybrid_memory) / base_memory * 100), "\n")
        
        # 新增策略4: MINLEVELS - 根据节点层次进行排序
        def minlevels_optimization():
            # 计算每个节点的层次（到源节点的最短路径长度）
            node_levels = {}
            
            # 找到所有源节点（入度为0的节点）
            sources = [node_id for node_id, node in self.nodes.items() if not node.in_edges]
            
            # 使用BFS计算每个节点的层次
            queue = deque([(source_id, 0) for source_id in sources])
            while queue:
                node_id, level = queue.popleft()
                
                # 如果节点已经计算过层次，取最小值
                if node_id in node_levels:
                    node_levels[node_id] = min(node_levels[node_id], level)
                else:
                    node_levels[node_id] = level
                
                # 遍历所有出边，计算下一层节点的层次
                for target_id, _ in self.nodes[node_id].out_edges:
                    queue.append((target_id, level + 1))
            
            # 按层次和约束排序
            in_degree = {node_id: len(node.in_edges) for node_id, node in self.nodes.items()}
            result = []
            available = []
            
            # 添加所有入度为0的节点
            for node_id, degree in in_degree.items():
                if degree == 0:
                    level = node_levels.get(node_id, 0)
                    constraint_priority = self.constraints.get(node_id, 0)
                    heapq.heappush(available, (level, constraint_priority, node_id))
            
            while available:
                level, priority, node_id = heapq.heappop(available)
                result.append(node_id)
                
                # 更新相邻节点的入度
                for target_id, _ in self.nodes[node_id].out_edges:
                    in_degree[target_id] -= 1
                    if in_degree[target_id] == 0:
                        target_level = node_levels.get(target_id, 0)
                        constraint_priority = self.constraints.get(target_id, 0)
                        heapq.heappush(available, (target_level, constraint_priority, target_id))
            
            return result
        
        minlevels_order = minlevels_optimization()
        minlevels_memory, _ = self.simulate_memory(minlevels_order)
        if minlevels_memory < best_memory:
            print("!!!!!!!!!!!!!!!!!!!!!策略4: MINLEVELS，内存峰值减少!!!!!!!!!!!!!!!!!!!!!")
            best_method="MINLEVELS"
            best_order = minlevels_order
            best_memory = minlevels_memory
        print("MINLEVELS优化后的排序:", minlevels_order)
        print("MINLEVELS优化后内存峰值:", minlevels_memory)
        print("内存优化效果: {:.2f}%".format((base_memory - minlevels_memory) / base_memory * 100), "\n")
        
        # 新增策略5: RESPECTORDER - 尊重原始顺序
        def respectorder_optimization():
            in_degree = {node_id: len(node.in_edges) for node_id, node in self.nodes.items()}
            result = []
            available = []
            
            # 添加所有入度为0的节点
            for node_id, degree in in_degree.items():
                if degree == 0:
                    # 使用节点ID作为顺序依据
                    heapq.heappush(available, (node_id, node_id))
            
            while available:
                _, node_id = heapq.heappop(available)
                result.append(node_id)
                
                # 更新相邻节点的入度
                for target_id, _ in self.nodes[node_id].out_edges:
                    in_degree[target_id] -= 1
                    if in_degree[target_id] == 0:
                        heapq.heappush(available, (target_id, target_id))
            
            return result
        
        respectorder_order = respectorder_optimization()
        respectorder_memory, _ = self.simulate_memory(respectorder_order)
        if respectorder_memory < best_memory:
            print("!!!!!!!!!!!!!!!!!!!!!策略5: RESPECTORDER，内存峰值减少!!!!!!!!!!!!!!!!!!!!!")
            best_method="RESPECTORDER"
            best_order = respectorder_order
            best_memory = respectorder_memory
        print("RESPECTORDER优化后的排序:", respectorder_order)
        print("RESPECTORDER优化后内存峰值:", respectorder_memory)
        print("内存优化效果: {:.2f}%".format((base_memory - respectorder_memory) / base_memory * 100), "\n")
        
        # 新增策略6: MAXMINSIZE - 选择大小最合适的节点
        def maxminsize_optimization():
            in_degree = {node_id: len(node.in_edges) for node_id, node in self.nodes.items()}
            result = []
            available = []
            
            # 计算所有节点大小的中位数
            node_sizes = [node.size for node in self.nodes.values()]
            if node_sizes:
                median_size = sorted(node_sizes)[len(node_sizes) // 2]
            else:
                median_size = 0
            
            # 添加所有入度为0的节点
            for node_id, degree in in_degree.items():
                if degree == 0:
                    node = self.nodes[node_id]
                    # 计算节点大小与中位数的差异（越接近中位数，优先级越高）
                    size_diff = abs(node.size - median_size)
                    constraint_priority = self.constraints.get(node_id, 0)
                    heapq.heappush(available, (constraint_priority, size_diff, node_id))
            
            while available:
                _, _, node_id = heapq.heappop(available)
                result.append(node_id)
                
                # 更新相邻节点的入度
                for target_id, _ in self.nodes[node_id].out_edges:
                    in_degree[target_id] -= 1
                    if in_degree[target_id] == 0:
                        target_node = self.nodes[target_id]
                        size_diff = abs(target_node.size - median_size)
                        constraint_priority = self.constraints.get(target_id, 0)
                        heapq.heappush(available, (constraint_priority, size_diff, target_id))
            
            return result
        
        maxminsize_order = maxminsize_optimization()
        maxminsize_memory, _ = self.simulate_memory(maxminsize_order)
        if maxminsize_memory < best_memory:
            print("!!!!!!!!!!!!!!!!!!!!!策略6: MAXMINSIZE，内存峰值减少!!!!!!!!!!!!!!!!!!!!!")
            best_method="MAXMINSIZE"
            best_order = maxminsize_order
            best_memory = maxminsize_memory
        print("MAXMINSIZE优化后的排序:", maxminsize_order)
        print("MAXMINSIZE优化后内存峰值:", maxminsize_memory)
        print("内存优化效果: {:.2f}%".format((base_memory - maxminsize_memory) / base_memory * 100), "\n")
        
        # 新增策略7: MAXSIZE - 优先选择大节点
        def maxsize_optimization():
            in_degree = {node_id: len(node.in_edges) for node_id, node in self.nodes.items()}
            result = []
            available = []
            
            # 添加所有入度为0的节点
            for node_id, degree in in_degree.items():
                if degree == 0:
                    node = self.nodes[node_id]
                    constraint_priority = self.constraints.get(node_id, 0)
                    # 负号使得大小最大的节点优先级最高
                    heapq.heappush(available, (constraint_priority, -node.size, node_id))
            
            while available:
                _, _, node_id = heapq.heappop(available)
                result.append(node_id)
                
                # 更新相邻节点的入度
                for target_id, _ in self.nodes[node_id].out_edges:
                    in_degree[target_id] -= 1
                    if in_degree[target_id] == 0:
                        target_node = self.nodes[target_id]
                        constraint_priority = self.constraints.get(target_id, 0)
                        heapq.heappush(available, (constraint_priority, -target_node.size, target_id))
            
            return result
        
        maxsize_order = maxsize_optimization()
        maxsize_memory, _ = self.simulate_memory(maxsize_order)
        if maxsize_memory < best_memory:
            print("!!!!!!!!!!!!!!!!!!!!!策略7: MAXSIZE，内存峰值减少!!!!!!!!!!!!!!!!!!!!!")
            best_method="MAXSIZE"
            best_order = maxsize_order
            best_memory = maxsize_memory
        print("MAXSIZE优化后的排序:", maxsize_order)
        print("MAXSIZE优化后内存峰值:", maxsize_memory)
        print("内存优化效果: {:.2f}%".format((base_memory - maxsize_memory) / base_memory * 100), "\n")
        
        # 新增策略8: GE Topo优化 - 长生命周期节点向后移动
        def ge_topo_optimization():
            # 使用当前最优顺序作为基础
            order = best_order.copy()
            
            # 计算每个节点的输入和输出内存生命周期
            exec_index = {node_id: idx for idx, node_id in enumerate(order)}
            
            # 识别长生命周期节点
            long_lifecycle_nodes = []
            for node_id in order:
                node = self.nodes[node_id]
                
                # 计算输入内存的最大生命周期
                input_lifecycle = 0
                for source_id, _ in node.in_edges:
                    if source_id in exec_index:
                        lifecycle = exec_index[node_id] - exec_index[source_id]
                        input_lifecycle = max(input_lifecycle, lifecycle)
                
                # 计算输出内存的最小生命周期
                output_lifecycle = float('inf')
                for target_id, _ in node.out_edges:
                    if target_id in exec_index:
                        lifecycle = exec_index[target_id] - exec_index[node_id]
                        output_lifecycle = min(output_lifecycle, lifecycle)
                
                # 仅使用动态规则: 如果输入生命周期大于输出生命周期，则判定为长生命周期节点
                if output_lifecycle != float('inf') and input_lifecycle > output_lifecycle:
                    long_lifecycle_nodes.append(node_id)
            
            if not long_lifecycle_nodes:
                return order
            
            # 对每个长生命周期节点，尝试向后移动
            for node_id in long_lifecycle_nodes:
                current_pos = order.index(node_id)
                
                # 寻找最靠前的输出节点位置
                min_output_pos = len(order)
                for target_id, _ in self.nodes[node_id].out_edges:
                    if target_id in order:
                        output_pos = order.index(target_id)
                        min_output_pos = min(min_output_pos, output_pos)
                
                # 如果可以向后移动（保持在最靠前的输出节点之前）
                if min_output_pos > current_pos + 1:
                    # 移动节点到新位置
                    order.remove(node_id)
                    new_pos = min_output_pos - 1
                    order.insert(new_pos, node_id)
            
            # 验证结果是否是有效的拓扑排序
            visited = set()
            for node_id in order:
                # 检查所有前驱节点是否已访问
                for source_id, _ in self.nodes[node_id].in_edges:
                    if source_id not in visited:
                        print("警告: GE Topo优化后的顺序不是有效的拓扑排序，使用原始顺序")
                        return best_order
                visited.add(node_id)
            
            return order
        
        ge_topo_order = ge_topo_optimization()
        ge_topo_memory, _ = self.simulate_memory(ge_topo_order)
        if ge_topo_memory < best_memory:
            print("!!!!!!!!!!!!!!!!!!!!!策略8: GE Topo优化，内存峰值减少!!!!!!!!!!!!!!!!!!!!!")
            best_method="GE Topo优化"
            best_order = ge_topo_order
            best_memory = ge_topo_memory
        print("GE Topo优化后的排序:", ge_topo_order)
        print("GE Topo优化后内存峰值:", ge_topo_memory)
        print("内存优化效果: {:.2f}%".format((base_memory - ge_topo_memory) / base_memory * 100), "\n")

        # 输出最佳结果
        print(f"\n最佳优化方法: {best_method}")
        return best_order, best_memory, best_method

# 主程序需要修改
def main():
    # 检查命令行参数
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("用法: python lower_mem.py <DAG文件路径> [输出DOT文件路径]")
        sys.exit(1)
    
    dag_file_path = sys.argv[1]
    
    # 如果提供了输出路径，则使用它，否则使用默认路径
    output_path = sys.argv[2] if len(sys.argv) == 3 else f"{os.path.splitext(dag_file_path)[0]}_optimized.dot"
    
    dag = DAG()
    if not dag.parse_dot_file(dag_file_path):
        print(f"错误: 找不到文件 '{dag_file_path}' 或解析失败")
        sys.exit(1)
    
    # 设置节点约束 (示例，根据实际需求调整)
    # 这里设置某些节点的执行优先级，数字越小优先级越高
    node_constraints = {
        # 1: 0,  # 起始节点最高优先级
        # 4: 2,  # 节点4优先级较高
        # 7: 1,  # 节点7优先级次高
        # 12: 0  # 终止节点最高优先级
    }
    dag.set_node_constraints(node_constraints)
    
    print(f"节点约束: {node_constraints}")
    
    # 基本拓扑排序 (考虑节点约束)
    basic_order = dag.kahn_topological_sort()
    basic_memory, _ = dag.simulate_memory(basic_order)
    print("\n基本拓扑排序:", basic_order)
    print("内存峰值:", basic_memory)
    
    # 优化排序 (考虑节点约束)
    optimized_order, optimized_memory, best_method = dag.optimize_execution_order()
    print("\n优化后的排序:", optimized_order)
    print("优化后内存峰值:", optimized_memory)
    print("最佳优化方法:", best_method)
    
    if basic_memory > 0:
        print(f"内存优化效果: {(basic_memory - optimized_memory) / basic_memory * 100:.2f}%")
    
    # 打印内存变化过程
    # _, memory_trace = dag.simulate_memory(optimized_order)
    # print("\n内存变化过程:")
    # for node_id, memory in memory_trace:
    #     print(f"执行节点 {node_id} 后，内存使用: {memory}")
    
    # 输出优化后的DAG图（如果需要）
    # 这里可以添加导出DOT文件的功能
    # export_dot_file(output_path, optimized_order, edge_list)
    # print(f"优化后的DOT文件已保存至: {output_path}")

if __name__ == "__main__":
    main()

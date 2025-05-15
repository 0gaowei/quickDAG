import numpy as np
import os

def read_memory_data(filename):
    """从结果文件中读取内存占用数据"""
    memory_values = []
    
    if not os.path.exists(filename):
        print(f"警告: 文件 {filename} 不存在!")
        return memory_values
    
    with open(filename, 'r') as f:
        for line in f:
            try:
                # 每行是一个表示内存占用的数字
                memory_values.append(float(line.strip()))
            except ValueError:
                print(f"警告: 无法解析行: {line.strip()}")
    
    return memory_values

def calculate_improvement_ratio(baseline, optimized):
    """计算优化率"""
    improvements = []
    
    for b, o in zip(baseline, optimized):
        if b > 0:  # 避免除以零
            improvement = (b - o) / b * 100  # 百分比
            improvements.append(improvement)
    
    return improvements

def main():
    # 读取三种算法的内存占用数据
    kahn_mem = read_memory_data('./test_results/kahn_mem.txt')
    max_release_mem = read_memory_data('./test_results/max_release_mem.txt')
    min_inmem_mem = read_memory_data('./test_results/min_inmem_mem.txt')
    
    # 确保数据长度一致
    min_length = min(len(kahn_mem), len(max_release_mem), len(min_inmem_mem))
    
    if min_length == 0:
        print("错误: 未能读取到有效的内存占用数据!")
        return
    
    kahn_mem = kahn_mem[:min_length]
    max_release_mem = max_release_mem[:min_length]
    min_inmem_mem = min_inmem_mem[:min_length]
    
    # 计算最大释放分配算法的优化率
    max_release_improvements = calculate_improvement_ratio(kahn_mem, max_release_mem)
    max_release_avg_improvement = np.mean(max_release_improvements)
    
    # 计算最小内存分配算法的优化率
    min_inmem_improvements = calculate_improvement_ratio(kahn_mem, min_inmem_mem)
    min_inmem_avg_improvement = np.mean(min_inmem_improvements)
    
    # 输出结果
    print(f"数据样本数量: {min_length}")
    print(f"最大释放分配算法平均内存优化率: {max_release_avg_improvement:.2f}%")
    print(f"最小内存分配算法平均内存优化率: {min_inmem_avg_improvement:.2f}%")
    
    # 还可以计算一些额外的统计信息
    print("\n额外统计信息:")
    print(f"Kahn算法平均内存占用: {np.mean(kahn_mem)/1024/1024/1024:.2f} GB")
    print(f"最大释放算法平均内存占用: {np.mean(max_release_mem)/1024/1024/1024:.2f} GB")
    print(f"最小内存算法平均内存占用: {np.mean(min_inmem_mem)/1024/1024/1024:.2f} GB")
    
    # 输出每个样本的优化率到文件
    with open('./test_results/optimization_ratios.txt', 'w') as f:
        f.write("样本ID,Kahn内存(B),最大释放分配内存(B),最小内存分配内存(B),最大释放优化率(%),最小内存优化率(%)\n")
        for i in range(min_length):
            f.write(f"{i+1},{kahn_mem[i]},{max_release_mem[i]},{min_inmem_mem[i]},{max_release_improvements[i]:.2f},{min_inmem_improvements[i]:.2f}\n")
    
    print(f"\n详细优化率已输出到 './test_results/optimization_ratios.csv'")

if __name__ == "__main__":
    main()

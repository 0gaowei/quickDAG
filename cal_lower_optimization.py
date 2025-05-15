import os
import re
import numpy as np
from collections import defaultdict

def extract_optimization_rates(file_path):
    """从优化结果文件中提取各策略的内存优化率"""
    # 定义正则表达式模式来匹配策略名称和优化率
    pattern = re.compile(r'(混合优化|MINLEVELS优化|RESPECTORDER优化|MAXMINSIZE优化|MAXSIZE优化|GE Topo优化).*?内存优化效果:\s*([-\d.]+)%', re.DOTALL)
    
    # 也可以检测最佳优化方法
    best_pattern = re.compile(r'最佳优化方法:\s*(.*?)\n.*?内存优化效果:\s*([-\d.]+)%', re.DOTALL)
    
    strategies = {}
    best_strategy = None
    best_rate = None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 提取各策略的优化率
            for match in pattern.finditer(content):
                strategy_name = match.group(1)
                optimization_rate = float(match.group(2))
                strategies[strategy_name] = optimization_rate
            
            # 提取最佳优化方法
            best_match = best_pattern.search(content)
            if best_match:
                best_strategy = best_match.group(1)
                best_rate = float(best_match.group(2))
                
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
    
    return strategies, best_strategy, best_rate

def main():
    # 结果文件所在目录
    results_dir = './test_results/'
    
    # 检查目录是否存在
    if not os.path.exists(results_dir):
        print(f"错误: 目录 {results_dir} 不存在!")
        return
    
    # 存储所有策略的优化率
    all_rates = defaultdict(list)
    best_strategies_count = defaultdict(int)
    total_files = 0
    
    # 遍历所有结果文件
    for filename in os.listdir(results_dir):
        if filename.endswith('_lower_mem.txt'):
            file_path = os.path.join(results_dir, filename)
            strategies, best_strategy, best_rate = extract_optimization_rates(file_path)
            
            # 添加各策略的优化率
            for strategy_name, rate in strategies.items():
                all_rates[strategy_name].append(rate)
            
            # 记录最佳策略
            if best_strategy:
                best_strategies_count[best_strategy] += 1
            
            total_files += 1
    
    if total_files == 0:
        print("未找到有效的结果文件!")
        return
    
    print(f"共处理 {total_files} 个结果文件\n")
    
    # 计算并输出每个策略的平均优化率
    print("各策略平均优化率:")
    print("-" * 50)
    print(f"{'策略名称':<20} | {'平均优化率':<10} | {'样本数':<10}")
    print("-" * 50)
    
    # 按平均优化率排序
    strategy_avg_rates = {}
    for strategy_name, rates in all_rates.items():
        avg_rate = np.mean(rates)
        strategy_avg_rates[strategy_name] = avg_rate
    
    sorted_strategies = sorted(strategy_avg_rates.items(), key=lambda x: x[1], reverse=True)
    
    for strategy_name, avg_rate in sorted_strategies:
        rates = all_rates[strategy_name]
        print(f"{strategy_name:<20} | {avg_rate:>10.2f}% | {len(rates):<10}")
    
    print("\n最佳优化策略统计:")
    print("-" * 50)
    print(f"{'策略名称':<20} | {'被选为最佳次数':<15} | {'占比':<10}")
    print("-" * 50)
    
    # 按被选为最佳的次数排序
    sorted_best = sorted(best_strategies_count.items(), key=lambda x: x[1], reverse=True)
    
    for strategy_name, count in sorted_best:
        percentage = count / total_files * 100
        print(f"{strategy_name:<20} | {count:>15} | {percentage:>9.2f}%")
    
    # 输出全局最佳策略
    if sorted_strategies:
        best_overall = sorted_strategies[0][0]
        best_rate = sorted_strategies[0][1]
        print(f"\n全局最佳策略: {best_overall} (平均优化率: {best_rate:.2f}%)")

if __name__ == "__main__":
    main()

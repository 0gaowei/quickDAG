#!/bin/bash

# 创建必要的目录
mkdir -p ./dag_input/
mkdir -p ./test_results/

# 生成100个DAG图
echo "正在生成DAG图..."
for i in $(seq 1 100)
do
    ./daggen/daggen -n 100 -o ./dag_input/$i.dot --dot
    echo "已生成 $i.dot"
done

# 对每个DAG图应用三种基本排序算法
echo "正在应用基本排序算法..."
for i in $(seq 1 100)
do
    # Kahn算法进行拓扑排序
    python kahn.py ./dag_input/$i.dot ./test_results/${i}_kahn.dot
    echo "已完成 $i.dot 的Kahn排序"
    
    # 最大释放分配算法
    python max_release_alloc.py ./dag_input/$i.dot ./test_results/${i}_max_release.dot
    echo "已完成 $i.dot 的最大释放分配排序"
    
    # 最小内存分配算法
    python min_inmem_alloc.py ./dag_input/$i.dot ./test_results/${i}_min_inmem.dot
    echo "已完成 $i.dot 的最小内存分配排序"
    
    # 计算各算法的内存占用并存储结果
    python cal.py ./dag_input/$i.dot ./test_results/${i}_kahn.dot >> ./test_results/kahn_mem.txt
    echo "已计算 ${i}_kahn.dot 的内存占用"
    
    python cal.py ./dag_input/$i.dot ./test_results/${i}_max_release.dot >> ./test_results/max_release_mem.txt
    echo "已计算 ${i}_max_release.dot 的内存占用"
    
    python cal.py ./dag_input/$i.dot ./test_results/${i}_min_inmem.dot >> ./test_results/min_inmem_mem.txt
    echo "已计算 ${i}_min_inmem.dot 的内存占用"
done

# 对每个DAG图应用启发式低内存优化的8种策略
echo "正在应用启发式优化策略..."
for i in $(seq 1 100)
do
    python lower_mem.py ./dag_input/$i.dot  > ./test_results/${i}_lower_mem.txt
    echo "已完成 $i.dot 的TOPO优化"
done

echo "所有任务已完成!"

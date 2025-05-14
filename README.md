# QUICK-DAG

## 用`daggen`工具生成DAG图

n表示DAG图的节点数，o表示DAG图的输出文件名，--dot表示输出为`.dot`文件。
测试时n设置为100，o循环100次，每次输出为`1.dot`到`100.dot`，保存到路径`./dag_src/`中。

示例：

```bash
./daggen -n 100 -o 1.dot --dot
```

## 不同方法对DAG图进行排序

对上面生成的100个DAG图进行排序，分别使用`kahn.py`、`max_release_alloc.py`、`min_inmem_alloc.py`、`lower_mem.py`四种方法对DAG图进行排序。

### 内存感知的拓扑排序

#### 使用`kahn.py`脚本对DAG图进行拓扑排序

```bash
python kahn.py ./dag_src/1.dot ./dag_src/1_kahn.dot
```

#### 使用`max_release_alloc.py`对DAG图进行排序

```bash
python max_release_alloc.py ./dag_src/1.dot ./dag_src/1_max_release.dot
```

#### 使用`min_inmem_alloc.py`对DAG图进行排序

```bash
python min_inmem_alloc.py ./dag_src/1.dot ./dag_src/1_min_inmem.dot
```

#### 使用`cal.py`计算上面三种方法的内存占用

```bash
python cal.py ./dag_src/1.dot ./dag_src/1_kahn.dot
```

### 启发式策略的拓扑优化

#### 使用`lower_mem.py`对DAG图进行排序

```bash
python lower_mem.py ./dag_src/1.dot
```

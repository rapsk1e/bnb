# ⚽ Football Starting XI Optimization using Branch and Bound

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-red)
![Algorithm](https://img.shields.io/badge/Algorithm-Branch%20and%20Bound-green)
![License](https://img.shields.io/badge/License-Educational-orange)

## 📌 Overview

This project implements the **Branch and Bound Algorithm** to optimize a football team's **Starting XI lineup** based on:

- Formation requirements
- Player ratings
- Transfer budget constraints
- Position compatibility rules

The system automatically searches for the best combination of players that maximizes the total squad rating while staying within the available budget.

A web-based interface built with **Streamlit** allows users to upload datasets, select formations, set budgets, and visualize the optimized lineup.

---

## 🎯 Problem Statement

Football clubs often face the challenge of building the strongest possible squad while operating under financial constraints.

Given:

- A dataset of football players
- A predefined formation
- A limited transfer budget

The objective is:

> Find the optimal Starting XI with the highest total rating without exceeding the budget.

This problem belongs to the class of **combinatorial optimization problems**, making it suitable for the **Branch and Bound** approach.

---

## 🚀 Features

✅ Upload custom player datasets (.csv)

✅ Multiple football formations:

- 4-3-3
- 4-4-2
- 4-2-3-1
- 3-5-2

✅ Position compatibility handling

✅ Budget-constrained optimization

✅ Branch and Bound search

✅ Upper Bound calculation

✅ Automatic pruning of non-promising branches

✅ Interactive football pitch visualization

✅ Branch and Bound decision tree visualization

✅ Optimization statistics and performance metrics

---

## 🏗️ Algorithm

The optimization process follows these steps:

1. Load player dataset
2. Generate candidate players for each formation slot
3. Create root node
4. Expand nodes (Branching)
5. Compute Upper Bound
6. Prune unpromising nodes
7. Continue until optimal solution is found
8. Display optimized Starting XI

### Objective Function

Maximize:

\[
\text{Total Rating} = \sum_{i=1}^{11} Rating_i
\]

Subject to:

\[
\sum_{i=1}^{11} Value_i \le Budget
\]

---

## 📂 Dataset Structure

The dataset should contain the following columns:

| Column | Description |
|----------|-------------|
| Name | Player Name |
| Position | Player Position |
| Overall | Overall Rating |
| Value_EUR | Market Value |
| Age | Player Age |
| Club | Current Club |

Example:

| Name | Position | Overall | Value_EUR |
|--------|----------|----------|-----------|
| Erling Haaland | ST | 91 | 180000000 |
| Rodri | CDM | 90 | 130000000 |

---

## 📸 Application Preview

### Starting XI Visualization

- Interactive football field
- Player positioning according to formation
- Player ratings displayed directly on the pitch

### Branch and Bound Tree

- Explored Nodes
- Pruned Nodes
- Best Solution Node
- Budget Pruning
- Upper Bound Pruning

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/football-starting-xi-bnb.git
cd football-starting-xi-bnb
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run Streamlit:

```bash
streamlit run app.py
```

---

## 📦 Requirements

```txt
streamlit
pandas
matplotlib
graphviz
```

---

## 🧠 Branch and Bound Components

### Branching

Each node represents a partial lineup.

### Bounding

An Upper Bound is calculated to estimate the best possible rating obtainable from the current node.

### Pruning

Branches are discarded when:

- Budget exceeds available funds
- Upper Bound is lower than the current best solution

This significantly reduces the search space.

---

## 📊 Example Output

### Input

Formation: 4-3-3

Budget: €500M

Dataset: 200 Real Players

### Output

| Position | Player | Rating |
|-----------|---------|---------|
| GK | Alisson | 89 |
| CB | Van Dijk | 90 |
| ST | Haaland | 91 |
| ... | ... | ... |

Total Squad Rating: **973**

Total Budget Used: **€498M**

---

## 📈 Performance Metrics

The system reports:

- Nodes Explored
- Nodes Pruned
- Execution Time
- Pruning Efficiency

Example:

```json
{
  "nodes_explored": 152,
  "nodes_pruned": 347,
  "execution_time": "0.42 seconds",
  "pruning_efficiency": "69.55%"
}
```

---

## 🎓 Academic Context

This project was developed as a final project for the course:

**Linear Programming / Optimization Techniques**

The project demonstrates the application of:

- Branch and Bound Algorithm
- Combinatorial Optimization
- Constraint Satisfaction
- Decision Tree Search

---

## 👨‍💻 Author

**Rafli Almansyah Tambunan**

Institut Teknologi Sumatera (ITERA)

2026

---

## 📜 License

This project is developed for educational and research purposes.

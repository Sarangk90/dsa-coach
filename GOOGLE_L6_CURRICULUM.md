# Google L6 Staff Engineer - DSA Curriculum & Progress

**Generated:** 2026-01-24
**Target:** Google Staff Engineer (L6) Interview
**Focus:** DP-heavy, Trees, Graphs (based on Google interview patterns)

---

## The Big Picture: 7 Domains to Conquer

```
GOOGLE L6 DSA ROADMAP
══════════════════════════════════════════════════════════════════════════════

DOMAIN 1: ARRAY MASTERY (45h)                              ████████░░░░  65%
├── Arrays & Hashing        ███████████░  81%  ✓ Mastered   Foundation
├── Two Pointers            ██░░░░░░░░░░  25%               Traversal
├── Sliding Window          ████████████ 100%  ✓ Mastered   Windows
└── Binary Search           █████████░░░  75%               Search

    WHY: Every interview starts here. Two Pointers is "sliding window
    with independent pointers." Binary search on answer space is Google's
    favorite variant.

──────────────────────────────────────────────────────────────────────────────

DOMAIN 2: LINEAR STRUCTURES (20h)                          ░░░░░░░░░░░░   0%
├── Linked Lists            ░░░░░░░░░░░░   0%               Pointers
└── Stacks & Queues         ░░░░░░░░░░░░   0%               LIFO/FIFO

    WHY: LRU Cache (Domain 7) requires linked lists. Monotonic stack
    appears in histogram/water problems. Foundation for Design rounds.

──────────────────────────────────────────────────────────────────────────────

DOMAIN 3: RECURSION & EXPLORATION (30h)                    ██░░░░░░░░░░  23%
├── Recursion               █████░░░░░░░  45%               Trust it
└── Backtracking            ░░░░░░░░░░░░   0%               Explore all

    WHY: You cannot do DP without recursion intuition. Backtracking IS
    recursion + choice + undo. N-Queens, Sudoku, Word Search all here.

──────────────────────────────────────────────────────────────────────────────

DOMAIN 4: TREES & GRAPHS (67h) ⭐ GOOGLE CORE              ███████░░░░░  52%
├── Trees                   ████████████ 100%               Hierarchies
├── Graphs - DFS            █████░░░░░░░  55%  *partial     Connectivity
├── Graphs - BFS            █████░░░░░░░  55%  *partial     Shortest path
└── Graphs - Advanced       ░░░░░░░░░░░░   0%               Union-Find

    WHY: Google LOVES this domain. Expect 1-2 problems. Trees ARE graphs
    (connected, acyclic). Your 'graphs' progress covers basics - need
    to go deeper into DFS/BFS/Dijkstra/Topo Sort.

    * Your current 'graphs' (55%) maps to DFS+BFS basics

──────────────────────────────────────────────────────────────────────────────

DOMAIN 5: DYNAMIC PROGRAMMING (50h) ⭐⭐ GOOGLE FAVORITE    ░░░░░░░░░░░░   0%
├── 1D Linear DP            ░░░░░░░░░░░░   0%               Fibonacci+
├── 2D Grid DP              ░░░░░░░░░░░░   0%               Paths, areas
├── Knapsack                ░░░░░░░░░░░░   0%               Selection
├── String DP (LCS/Edit)    ░░░░░░░░░░░░   0%               Matching
├── State Machine DP        ░░░░░░░░░░░░   0%               Stock series
└── DP on Trees             ░░░░░░░░░░░░   0%               Tree + DP

    WHY: Google's #1 tested pattern. Most interviewers have a favorite
    DP problem. All sub-patterns share one mental model:
    "What's my state? What are my transitions?"

    ⚠️  THIS IS YOUR BIGGEST GAP - START HERE AFTER CURRENT PATTERNS

──────────────────────────────────────────────────────────────────────────────

DOMAIN 6: OPTIMIZATION PATTERNS (35h)                      ░░░░░░░░░░░░   0%
├── Heaps                   ░░░░░░░░░░░░   0%               Top-K, merge
├── Greedy                  ░░░░░░░░░░░░   0%               Local optimal
└── Intervals               ░░░░░░░░░░░░   0%               Scheduling

    WHY: Heaps enable efficient greedy. Intervals = greedy + sorting.
    Meeting Rooms II is a classic. Task Scheduler tests heap + greedy.

──────────────────────────────────────────────────────────────────────────────

DOMAIN 7: SYSTEM DESIGN BRIDGE (12h)                       ░░░░░░░░░░░░   0%
└── Design Problems         ░░░░░░░░░░░░   0%               LRU, LFU

    WHY: These coding problems directly map to system design. At L6,
    expect "now how would you scale this?" LRU Cache is MANDATORY.

══════════════════════════════════════════════════════════════════════════════
OVERALL: 26/174 problems (15%)  |  ~248 hours remaining  |  2/18 patterns mastered
══════════════════════════════════════════════════════════════════════════════
```

---

## Your Completed Quests (26)

<details>
<summary>Click to expand</summary>

**Arrays & Hashing (5/11)**
- arrays_hashing_two_sum
- arrays_hashing_group_anagrams
- arrays_hashing_top_k_frequent_elements
- arrays_hashing_subarray_sum_equals_k
- arrays_hashing_product_of_array_except_self

**Two Pointers (1/9)**
- two_pointers_linked_list_cycle

**Sliding Window (3/8)** ✓ Mastered
- sliding_window_longest_substring_without_repeating
- sliding_window_minimum_window_substring
- sliding_window_permutation_in_string

**Binary Search (3/10)**
- binary_search_basic
- binary_search_rotated_sorted_array
- binary_search_koko_eating_bananas

**Recursion (3/7)**
- recursion_fibonacci
- recursion_climbing_stairs
- recursion_power_x_n

**Trees (7/18)**
- trees_maximum_depth
- trees_inorder_traversal
- trees_lowest_common_ancestor_bst
- trees_level_order_traversal
- trees_validate_bst
- trees_path_sum
- trees_right_side_view

**Graphs (4/26)**
- graphs_number_of_islands
- graphs_clone_graph
- graphs_rotting_oranges
- graphs_01_matrix

</details>

---

## Recommended Attack Plan

```
PHASE 1: FINISH CURRENT PATTERNS (2-3 weeks)
├── Trees: 2 more problems → mastery
├── Binary Search: 1 more problem → strong
├── Two Pointers: 3Sum, Container, Trapping Rain Water
└── Recursion: Generate Parentheses, then move to Backtracking

PHASE 2: DP MARATHON (4-6 weeks) ⭐ CRITICAL
├── Week 1-2: 1D DP (House Robber, Decode Ways, LIS)
├── Week 2-3: 2D DP (Unique Paths, Min Path Sum, Maximal Square)
├── Week 3-4: Knapsack (Coin Change, Partition Equal Subset)
├── Week 4-5: String DP (LCS, Edit Distance)
└── Week 5-6: State Machine + Tree DP (Stock series, House Robber III)

PHASE 3: DEEP GRAPH DIVE (2-3 weeks)
├── Cycle detection (Course Schedule)
├── Topological Sort (Alien Dictionary)
├── Union-Find (Accounts Merge)
└── Dijkstra (Network Delay Time)

PHASE 4: FILL GAPS (2-3 weeks)
├── Linked Lists (for LRU Cache)
├── Heaps (Top-K, Merge K Sorted)
├── Backtracking (N-Queens, Word Search)
└── Design (LRU Cache - MUST KNOW)
```

---

# Detailed Curriculum by Domain

---

## DOMAIN 1: Array Mastery (45h)

*The foundation. Every interview starts here.*

### 1.1 Arrays & Hashing ✅ (15h) - 81% confidence

**System Design Connection:** Consistent hashing (DynamoDB), caching keys (Redis)

#### Hash Map Operations & Frequency Counting
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Two Sum | 🟢 Easy | [LeetCode](https://leetcode.com/problems/two-sum) |
| ✅ | Group Anagrams | 🟡 Medium | [LeetCode](https://leetcode.com/problems/group-anagrams) |
| ✅ | Top K Frequent Elements | 🟡 Medium | [LeetCode](https://leetcode.com/problems/top-k-frequent-elements) |

#### In-Place Array Manipulation
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Move Zeroes | 🟢 Easy | [LeetCode](https://leetcode.com/problems/move-zeroes) |
| ✅ | Product of Array Except Self | 🟡 Medium | [LeetCode](https://leetcode.com/problems/product-of-array-except-self) |
| ⬜ | Rotate Image | 🟡 Medium | [LeetCode](https://leetcode.com/problems/rotate-image) |

#### Prefix Sum & Subarray
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Running Sum of 1D Array | 🟢 Easy | [LeetCode](https://leetcode.com/problems/running-sum-of-1d-array) |
| ✅ | Subarray Sum Equals K | 🟡 Medium | [LeetCode](https://leetcode.com/problems/subarray-sum-equals-k) |
| ⬜ | Continuous Subarray Sum | 🟡 Medium | [LeetCode](https://leetcode.com/problems/continuous-subarray-sum) |

#### Two-Pass Techniques
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Best Time to Buy and Sell Stock | 🟢 Easy | [LeetCode](https://leetcode.com/problems/best-time-to-buy-and-sell-stock) |
| ⬜ | Next Permutation | 🟡 Medium | [LeetCode](https://leetcode.com/problems/next-permutation) |

---

### 1.2 Two Pointers (10h) - 25% confidence

**When to use:** Sorted arrays, finding pairs, partitioning

#### Opposite Direction (Converging)
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Two Sum II | 🟢 Easy | [LeetCode](https://leetcode.com/problems/two-sum-ii-input-array-is-sorted) |
| ⬜ | 3Sum | 🟡 Medium | [LeetCode](https://leetcode.com/problems/3sum) |
| ⬜ | Container With Most Water | 🟡 Medium | [LeetCode](https://leetcode.com/problems/container-with-most-water) |
| ⬜ | Trapping Rain Water | 🔴 Hard | [LeetCode](https://leetcode.com/problems/trapping-rain-water) |

#### Same Direction (Fast-Slow)
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Remove Duplicates from Sorted Array | 🟢 Easy | [LeetCode](https://leetcode.com/problems/remove-duplicates-from-sorted-array) |
| ✅ | Linked List Cycle | 🟢 Easy | [LeetCode](https://leetcode.com/problems/linked-list-cycle) |
| ⬜ | Find the Duplicate Number | 🟡 Medium | [LeetCode](https://leetcode.com/problems/find-the-duplicate-number) |

#### Partition
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Sort Colors (Dutch Flag) | 🟡 Medium | [LeetCode](https://leetcode.com/problems/sort-colors) |
| ⬜ | Squares of a Sorted Array | 🟢 Easy | [LeetCode](https://leetcode.com/problems/squares-of-a-sorted-array) |

---

### 1.3 Sliding Window ✅ (12h) - 100% confidence

**System Design Connection:** Rate limiting, TCP congestion control

#### Fixed-Size Window
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Maximum Average Subarray I | 🟢 Easy | [LeetCode](https://leetcode.com/problems/maximum-average-subarray-i) |
| ✅ | Permutation in String | 🟡 Medium | [LeetCode](https://leetcode.com/problems/permutation-in-string) |
| ⬜ | Sliding Window Maximum | 🔴 Hard | [LeetCode](https://leetcode.com/problems/sliding-window-maximum) |

#### Variable-Size Window
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Longest Substring Without Repeating | 🟡 Medium | [LeetCode](https://leetcode.com/problems/longest-substring-without-repeating-characters) |
| ⬜ | Minimum Size Subarray Sum | 🟡 Medium | [LeetCode](https://leetcode.com/problems/minimum-size-subarray-sum) |
| ✅ | Minimum Window Substring | 🔴 Hard | [LeetCode](https://leetcode.com/problems/minimum-window-substring) |

#### Window with HashMap
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Fruit Into Baskets | 🟡 Medium | [LeetCode](https://leetcode.com/problems/fruit-into-baskets) |
| ⬜ | Subarrays with K Different Integers | 🔴 Hard | [LeetCode](https://leetcode.com/problems/subarrays-with-k-different-integers) |

---

### 1.4 Binary Search (15h) - 75% confidence

**Key insight:** Not just for sorted arrays - search on answer space!

#### Standard Binary Search
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Binary Search | 🟢 Easy | [LeetCode](https://leetcode.com/problems/binary-search) |
| ⬜ | Search Insert Position | 🟢 Easy | [LeetCode](https://leetcode.com/problems/search-insert-position) |
| ⬜ | Find First and Last Position | 🟡 Medium | [LeetCode](https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array) |

#### Rotated Arrays
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Search in Rotated Sorted Array | 🟡 Medium | [LeetCode](https://leetcode.com/problems/search-in-rotated-sorted-array) |
| ⬜ | Find Minimum in Rotated Sorted Array | 🟡 Medium | [LeetCode](https://leetcode.com/problems/find-minimum-in-rotated-sorted-array) |

#### Answer Space Binary Search ⭐ Google Favorite
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Sqrt(x) | 🟢 Easy | [LeetCode](https://leetcode.com/problems/sqrtx) |
| ✅ | Koko Eating Bananas | 🟡 Medium | [LeetCode](https://leetcode.com/problems/koko-eating-bananas) |
| ⬜ | Capacity To Ship Packages | 🟡 Medium | [LeetCode](https://leetcode.com/problems/capacity-to-ship-packages-within-d-days) |
| ⬜ | Split Array Largest Sum | 🔴 Hard | [LeetCode](https://leetcode.com/problems/split-array-largest-sum) |
| ⬜ | Median of Two Sorted Arrays | 🔴 Hard | [LeetCode](https://leetcode.com/problems/median-of-two-sorted-arrays) |

---

## DOMAIN 2: Linear Structures (20h)

*Foundation for LRU Cache and monotonic stack problems.*

### 2.1 Linked Lists (10h) - Not started

**System Design Connection:** LRU Cache = HashMap + Doubly Linked List

#### In-Place Reversal
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Reverse Linked List | 🟢 Easy | [LeetCode](https://leetcode.com/problems/reverse-linked-list) |
| ⬜ | Reverse Linked List II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/reverse-linked-list-ii) |
| ⬜ | Reverse Nodes in k-Group | 🔴 Hard | [LeetCode](https://leetcode.com/problems/reverse-nodes-in-k-group) |

#### Fast-Slow Pointer
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Middle of Linked List | 🟢 Easy | [LeetCode](https://leetcode.com/problems/middle-of-the-linked-list) |
| ⬜ | Linked List Cycle II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/linked-list-cycle-ii) |
| ⬜ | Remove Nth Node From End | 🟡 Medium | [LeetCode](https://leetcode.com/problems/remove-nth-node-from-end-of-list) |

#### Merging
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Merge Two Sorted Lists | 🟢 Easy | [LeetCode](https://leetcode.com/problems/merge-two-sorted-lists) |
| ⬜ | Reorder List | 🟡 Medium | [LeetCode](https://leetcode.com/problems/reorder-list) |
| ⬜ | Merge k Sorted Lists | 🔴 Hard | [LeetCode](https://leetcode.com/problems/merge-k-sorted-lists) |

#### Special Patterns
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Intersection of Two Linked Lists | 🟢 Easy | [LeetCode](https://leetcode.com/problems/intersection-of-two-linked-lists) |
| ⬜ | Copy List with Random Pointer | 🟡 Medium | [LeetCode](https://leetcode.com/problems/copy-list-with-random-pointer) |

---

### 2.2 Stacks & Queues (10h) - Not started

**Key pattern:** Monotonic stack for "next greater/smaller" problems

#### Basic Stack
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Valid Parentheses | 🟢 Easy | [LeetCode](https://leetcode.com/problems/valid-parentheses) |
| ⬜ | Min Stack | 🟢 Easy | [LeetCode](https://leetcode.com/problems/min-stack) |
| ⬜ | Evaluate Reverse Polish Notation | 🟡 Medium | [LeetCode](https://leetcode.com/problems/evaluate-reverse-polish-notation) |

#### Monotonic Stack ⭐ Important
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Next Greater Element I | 🟢 Easy | [LeetCode](https://leetcode.com/problems/next-greater-element-i) |
| ⬜ | Daily Temperatures | 🟡 Medium | [LeetCode](https://leetcode.com/problems/daily-temperatures) |
| ⬜ | Largest Rectangle in Histogram | 🔴 Hard | [LeetCode](https://leetcode.com/problems/largest-rectangle-in-histogram) |

#### Queue Design
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Implement Queue using Stacks | 🟢 Easy | [LeetCode](https://leetcode.com/problems/implement-queue-using-stacks) |
| ⬜ | Implement Stack using Queues | 🟢 Easy | [LeetCode](https://leetcode.com/problems/implement-stack-using-queues) |
| ⬜ | Design Circular Queue | 🟡 Medium | [LeetCode](https://leetcode.com/problems/design-circular-queue) |

---

## DOMAIN 3: Recursion & Exploration (30h)

*You cannot do DP without this. Backtracking = recursion + choice + undo.*

### 3.1 Recursion Fundamentals (12h) - 45% confidence

#### Basic Recursion
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Fibonacci Number | 🟢 Easy | [LeetCode](https://leetcode.com/problems/fibonacci-number) |
| ✅ | Climbing Stairs | 🟢 Easy | [LeetCode](https://leetcode.com/problems/climbing-stairs) |
| ✅ | Power(x, n) | 🟡 Medium | [LeetCode](https://leetcode.com/problems/powx-n) |

#### Multiple Branches
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Generate Parentheses | 🟡 Medium | [LeetCode](https://leetcode.com/problems/generate-parentheses) |
| ⬜ | Letter Combinations of Phone Number | 🟡 Medium | [LeetCode](https://leetcode.com/problems/letter-combinations-of-a-phone-number) |

#### Memoization (Bridge to DP)
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Decode Ways | 🟡 Medium | [LeetCode](https://leetcode.com/problems/decode-ways) |
| ⬜ | Unique Paths | 🟡 Medium | [LeetCode](https://leetcode.com/problems/unique-paths) |

---

### 3.2 Backtracking (18h) - Not started

**Mental model:** Try → Recurse → Undo

#### Subsets & Combinations
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Subsets | 🟡 Medium | [LeetCode](https://leetcode.com/problems/subsets) |
| ⬜ | Subsets II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/subsets-ii) |
| ⬜ | Combinations | 🟡 Medium | [LeetCode](https://leetcode.com/problems/combinations) |
| ⬜ | Combination Sum | 🟡 Medium | [LeetCode](https://leetcode.com/problems/combination-sum) |
| ⬜ | Combination Sum II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/combination-sum-ii) |

#### Permutations
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Permutations | 🟡 Medium | [LeetCode](https://leetcode.com/problems/permutations) |
| ⬜ | Permutations II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/permutations-ii) |
| ⬜ | Palindrome Partitioning | 🟡 Medium | [LeetCode](https://leetcode.com/problems/palindrome-partitioning) |

#### Constraint Satisfaction ⭐ Classic
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | N-Queens | 🔴 Hard | [LeetCode](https://leetcode.com/problems/n-queens) |
| ⬜ | Sudoku Solver | 🔴 Hard | [LeetCode](https://leetcode.com/problems/sudoku-solver) |
| ⬜ | Word Search | 🟡 Medium | [LeetCode](https://leetcode.com/problems/word-search) |
| ⬜ | Partition to K Equal Sum Subsets | 🟡 Medium | [LeetCode](https://leetcode.com/problems/partition-to-k-equal-sum-subsets) |

---

## DOMAIN 4: Trees & Graphs (67h) ⭐ GOOGLE CORE

*Expect 1-2 problems from this domain. Trees ARE graphs (connected, acyclic).*

### 4.1 Trees (25h) - 100% confidence

#### Traversals (DFS)
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Binary Tree Inorder Traversal | 🟢 Easy | [LeetCode](https://leetcode.com/problems/binary-tree-inorder-traversal) |
| ⬜ | Binary Tree Preorder Traversal | 🟢 Easy | [LeetCode](https://leetcode.com/problems/binary-tree-preorder-traversal) |
| ⬜ | Binary Tree Postorder Traversal | 🟢 Easy | [LeetCode](https://leetcode.com/problems/binary-tree-postorder-traversal) |

#### Level Order (BFS)
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Binary Tree Level Order Traversal | 🟡 Medium | [LeetCode](https://leetcode.com/problems/binary-tree-level-order-traversal) |
| ⬜ | Zigzag Level Order Traversal | 🟡 Medium | [LeetCode](https://leetcode.com/problems/binary-tree-zigzag-level-order-traversal) |
| ✅ | Binary Tree Right Side View | 🟡 Medium | [LeetCode](https://leetcode.com/problems/binary-tree-right-side-view) |

#### BST Properties
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Validate Binary Search Tree | 🟡 Medium | [LeetCode](https://leetcode.com/problems/validate-binary-search-tree) |
| ⬜ | Kth Smallest Element in BST | 🟡 Medium | [LeetCode](https://leetcode.com/problems/kth-smallest-element-in-a-bst) |
| ✅ | Lowest Common Ancestor of BST | 🟡 Medium | [LeetCode](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree) |

#### Path Problems ⭐ Google Favorite
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Maximum Depth of Binary Tree | 🟢 Easy | [LeetCode](https://leetcode.com/problems/maximum-depth-of-binary-tree) |
| ✅ | Path Sum | 🟢 Easy | [LeetCode](https://leetcode.com/problems/path-sum) |
| ⬜ | Path Sum II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/path-sum-ii) |
| ⬜ | Path Sum III | 🟡 Medium | [LeetCode](https://leetcode.com/problems/path-sum-iii) |
| ⬜ | **Binary Tree Maximum Path Sum** | 🔴 Hard | [LeetCode](https://leetcode.com/problems/binary-tree-maximum-path-sum) |

#### Tree Construction
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Construct from Preorder and Inorder | 🟡 Medium | [LeetCode](https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal) |
| ⬜ | Construct from Inorder and Postorder | 🟡 Medium | [LeetCode](https://leetcode.com/problems/construct-binary-tree-from-inorder-and-postorder-traversal) |
| ⬜ | Flatten Binary Tree to Linked List | 🟡 Medium | [LeetCode](https://leetcode.com/problems/flatten-binary-tree-to-linked-list) |

---

### 4.2 Graphs - DFS (15h) - ~55% (partial)

**Your current 'graphs' progress covers basics here**

#### Basic DFS & Connected Components
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Number of Islands | 🟡 Medium | [LeetCode](https://leetcode.com/problems/number-of-islands) |
| ✅ | Clone Graph | 🟡 Medium | [LeetCode](https://leetcode.com/problems/clone-graph) |
| ⬜ | Number of Provinces | 🟡 Medium | [LeetCode](https://leetcode.com/problems/number-of-provinces) |

#### Cycle Detection ⭐ Important
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Course Schedule | 🟡 Medium | [LeetCode](https://leetcode.com/problems/course-schedule) |
| ⬜ | Course Schedule II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/course-schedule-ii) |
| ⬜ | Redundant Connection | 🟡 Medium | [LeetCode](https://leetcode.com/problems/redundant-connection) |

#### DFS with Backtracking
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | All Paths From Source to Target | 🟡 Medium | [LeetCode](https://leetcode.com/problems/all-paths-from-source-to-target) |
| ⬜ | Word Search II | 🔴 Hard | [LeetCode](https://leetcode.com/problems/word-search-ii) |

---

### 4.3 Graphs - BFS & Shortest Paths (15h) - ~55% (partial)

#### Unweighted Shortest Path
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ✅ | Rotting Oranges | 🟡 Medium | [LeetCode](https://leetcode.com/problems/rotting-oranges) |
| ⬜ | Shortest Path in Binary Matrix | 🟡 Medium | [LeetCode](https://leetcode.com/problems/shortest-path-in-binary-matrix) |
| ✅ | 01 Matrix | 🟡 Medium | [LeetCode](https://leetcode.com/problems/01-matrix) |

#### BFS with State
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Walls and Gates | 🟡 Medium | [LeetCode](https://leetcode.com/problems/walls-and-gates) |
| ⬜ | Shortest Bridge | 🟡 Medium | [LeetCode](https://leetcode.com/problems/shortest-bridge) |
| ⬜ | Open the Lock | 🟡 Medium | [LeetCode](https://leetcode.com/problems/open-the-lock) |

#### Weighted Shortest Paths (Dijkstra) ⭐
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Network Delay Time | 🟡 Medium | [LeetCode](https://leetcode.com/problems/network-delay-time) |
| ⬜ | Path with Maximum Probability | 🟡 Medium | [LeetCode](https://leetcode.com/problems/path-with-maximum-probability) |
| ⬜ | Cheapest Flights Within K Stops | 🟡 Medium | [LeetCode](https://leetcode.com/problems/cheapest-flights-within-k-stops) |

---

### 4.4 Graphs - Advanced (12h) - Not started

#### Union-Find (Disjoint Set Union)
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Number of Provinces (Union-Find) | 🟡 Medium | [LeetCode](https://leetcode.com/problems/number-of-provinces) |
| ⬜ | Redundant Connection | 🟡 Medium | [LeetCode](https://leetcode.com/problems/redundant-connection) |
| ⬜ | Accounts Merge | 🟡 Medium | [LeetCode](https://leetcode.com/problems/accounts-merge) |
| ⬜ | Most Stones Removed | 🟡 Medium | [LeetCode](https://leetcode.com/problems/most-stones-removed-with-same-row-or-column) |

#### Topological Sort ⭐ Important
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Course Schedule II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/course-schedule-ii) |
| ⬜ | **Alien Dictionary** | 🔴 Hard | [LeetCode](https://leetcode.com/problems/alien-dictionary) |
| ⬜ | Sequence Reconstruction | 🟡 Medium | [LeetCode](https://leetcode.com/problems/sequence-reconstruction) |

---

## DOMAIN 5: Dynamic Programming (50h) ⭐⭐ GOOGLE FAVORITE

> **Your biggest gap.** Google's #1 tested pattern. All sub-patterns share one model:
> "What's my state? What are my transitions?"

### 5.1 1D Linear DP (10h)

| Status | Problem | Difficulty | Link | Key Insight |
|--------|---------|------------|------|-------------|
| ✅ | Climbing Stairs | 🟢 Easy | [LeetCode](https://leetcode.com/problems/climbing-stairs) | Fibonacci |
| ⬜ | House Robber | 🟡 Medium | [LeetCode](https://leetcode.com/problems/house-robber) | Rob or skip |
| ⬜ | Decode Ways | 🟡 Medium | [LeetCode](https://leetcode.com/problems/decode-ways) | Fib + constraints |
| ⬜ | Longest Increasing Subsequence | 🟡 Medium | [LeetCode](https://leetcode.com/problems/longest-increasing-subsequence) | O(n²) or O(n log n) |

### 5.2 2D Grid DP (10h)

| Status | Problem | Difficulty | Link | Key Insight |
|--------|---------|------------|------|-------------|
| ⬜ | Unique Paths | 🟡 Medium | [LeetCode](https://leetcode.com/problems/unique-paths) | dp[i][j] = up + left |
| ⬜ | Minimum Path Sum | 🟡 Medium | [LeetCode](https://leetcode.com/problems/minimum-path-sum) | Min instead of sum |
| ⬜ | Maximal Square | 🟡 Medium | [LeetCode](https://leetcode.com/problems/maximal-square) | Min of 3 neighbors |
| ⬜ | Dungeon Game | 🔴 Hard | [LeetCode](https://leetcode.com/problems/dungeon-game) | Backward DP |

### 5.3 Knapsack Patterns (12h)

| Status | Problem | Difficulty | Link | Key Insight |
|--------|---------|------------|------|-------------|
| ⬜ | Partition Equal Subset Sum | 🟡 Medium | [LeetCode](https://leetcode.com/problems/partition-equal-subset-sum) | 0/1 knapsack |
| ⬜ | **Coin Change** | 🟡 Medium | [LeetCode](https://leetcode.com/problems/coin-change) | Unbounded knapsack |
| ⬜ | Coin Change 2 | 🟡 Medium | [LeetCode](https://leetcode.com/problems/coin-change-2) | Count combinations |
| ⬜ | Target Sum | 🟡 Medium | [LeetCode](https://leetcode.com/problems/target-sum) | Subset sum transform |

### 5.4 String DP - LCS/Edit Distance (12h)

| Status | Problem | Difficulty | Link | Key Insight |
|--------|---------|------------|------|-------------|
| ⬜ | Longest Common Subsequence | 🟡 Medium | [LeetCode](https://leetcode.com/problems/longest-common-subsequence) | Git diff uses this |
| ⬜ | **Edit Distance** | 🟡 Medium | [LeetCode](https://leetcode.com/problems/edit-distance) | Insert/delete/replace |
| ⬜ | Distinct Subsequences | 🔴 Hard | [LeetCode](https://leetcode.com/problems/distinct-subsequences) | Count matches |
| ⬜ | Regular Expression Matching | 🔴 Hard | [LeetCode](https://leetcode.com/problems/regular-expression-matching) | Wildcards |

### 5.5 State Machine DP (8h)

| Status | Problem | Difficulty | Link | Key Insight |
|--------|---------|------------|------|-------------|
| ⬜ | Best Time to Buy and Sell Stock | 🟢 Easy | [LeetCode](https://leetcode.com/problems/best-time-to-buy-and-sell-stock) | Track min |
| ⬜ | Best Time to Buy and Sell Stock II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii) | Unlimited txns |
| ⬜ | Best Time with Cooldown | 🟡 Medium | [LeetCode](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown) | 3 states |
| ⬜ | Best Time to Buy and Sell Stock IV | 🔴 Hard | [LeetCode](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iv) | K transactions |

### 5.6 DP on Trees (8h)

| Status | Problem | Difficulty | Link | Key Insight |
|--------|---------|------------|------|-------------|
| ⬜ | House Robber III | 🟡 Medium | [LeetCode](https://leetcode.com/problems/house-robber-iii) | Return (rob, skip) |
| ⬜ | **Binary Tree Maximum Path Sum** | 🔴 Hard | [LeetCode](https://leetcode.com/problems/binary-tree-maximum-path-sum) | Google favorite |
| ⬜ | Longest Univalue Path | 🟡 Medium | [LeetCode](https://leetcode.com/problems/longest-univalue-path) | Path with constraint |

---

## DOMAIN 6: Optimization Patterns (35h)

### 6.1 Heaps / Priority Queues (15h)

#### Top-K Problems
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Kth Largest Element in Array | 🟡 Medium | [LeetCode](https://leetcode.com/problems/kth-largest-element-in-an-array) |
| ✅ | Top K Frequent Elements | 🟡 Medium | [LeetCode](https://leetcode.com/problems/top-k-frequent-elements) |
| ⬜ | K Closest Points to Origin | 🟡 Medium | [LeetCode](https://leetcode.com/problems/k-closest-points-to-origin) |

#### Merge K Sorted
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Merge k Sorted Lists | 🔴 Hard | [LeetCode](https://leetcode.com/problems/merge-k-sorted-lists) |
| ⬜ | Kth Smallest in Sorted Matrix | 🟡 Medium | [LeetCode](https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix) |

#### Two Heaps (Median)
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Find Median from Data Stream | 🔴 Hard | [LeetCode](https://leetcode.com/problems/find-median-from-data-stream) |
| ⬜ | Sliding Window Median | 🔴 Hard | [LeetCode](https://leetcode.com/problems/sliding-window-median) |

#### Heap + Greedy
| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Task Scheduler | 🟡 Medium | [LeetCode](https://leetcode.com/problems/task-scheduler) |
| ⬜ | Reorganize String | 🟡 Medium | [LeetCode](https://leetcode.com/problems/reorganize-string) |

---

### 6.2 Greedy (12h)

| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Jump Game | 🟡 Medium | [LeetCode](https://leetcode.com/problems/jump-game) |
| ⬜ | Jump Game II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/jump-game-ii) |
| ⬜ | Non-overlapping Intervals | 🟡 Medium | [LeetCode](https://leetcode.com/problems/non-overlapping-intervals) |
| ⬜ | Gas Station | 🟡 Medium | [LeetCode](https://leetcode.com/problems/gas-station) |
| ⬜ | Minimum Arrows to Burst Balloons | 🟡 Medium | [LeetCode](https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons) |
| ⬜ | Remove K Digits | 🟡 Medium | [LeetCode](https://leetcode.com/problems/remove-k-digits) |
| ⬜ | Partition Labels | 🟡 Medium | [LeetCode](https://leetcode.com/problems/partition-labels) |

---

### 6.3 Intervals (8h)

| Status | Problem | Difficulty | Link |
|--------|---------|------------|------|
| ⬜ | Merge Intervals | 🟡 Medium | [LeetCode](https://leetcode.com/problems/merge-intervals) |
| ⬜ | Insert Interval | 🟡 Medium | [LeetCode](https://leetcode.com/problems/insert-interval) |
| ⬜ | Meeting Rooms | 🟢 Easy | [LeetCode](https://leetcode.com/problems/meeting-rooms) |
| ⬜ | Meeting Rooms II | 🟡 Medium | [LeetCode](https://leetcode.com/problems/meeting-rooms-ii) |
| ⬜ | My Calendar I | 🟡 Medium | [LeetCode](https://leetcode.com/problems/my-calendar-i) |
| ⬜ | Interval List Intersections | 🟡 Medium | [LeetCode](https://leetcode.com/problems/interval-list-intersections) |
| ⬜ | Employee Free Time | 🔴 Hard | [LeetCode](https://leetcode.com/problems/employee-free-time) |

---

## DOMAIN 7: System Design Bridge (12h)

*Coding problems that directly connect to system design. At L6, expect "now scale this."*

### 7.1 Design Problems - MUST KNOW

| Status | Problem | Difficulty | Link | System Design Connection |
|--------|---------|------------|------|--------------------------|
| ⬜ | **LRU Cache** | 🟡 Medium | [LeetCode](https://leetcode.com/problems/lru-cache) | Redis, Memcached, OS page replacement |
| ⬜ | LFU Cache | 🔴 Hard | [LeetCode](https://leetcode.com/problems/lfu-cache) | CDN caching strategies |
| ⬜ | Design Browser History | 🟡 Medium | [LeetCode](https://leetcode.com/problems/design-browser-history) | Stack-based navigation |
| ⬜ | Design Twitter | 🟡 Medium | [LeetCode](https://leetcode.com/problems/design-twitter) | Feed generation, fanout |
| ⬜ | Design HashMap | 🟢 Easy | [LeetCode](https://leetcode.com/problems/design-hashmap) | Hash function, collision handling |

---

## Google L6 Interview Tips

```
CODING ROUNDS (1-2)
├── Expect Medium-Hard problems
├── Focus on DP and Graph problems
├── Communicate trade-offs clearly
└── Write clean, production-quality code

SYSTEM DESIGN (2-3)
├── Connect DSA to real systems
├── LRU Cache, consistent hashing, rate limiting
├── Show breadth AND depth
└── Discuss scalability proactively

BEHAVIORAL (Googleyness)
├── Demonstrate technical leadership
├── Show cross-team influence
├── Give concrete examples of scope
└── Discuss ambiguity navigation

TIME MANAGEMENT
├── 45 min per coding problem
├── 5 min: clarify requirements
├── 10 min: design approach
├── 25 min: implement
└── 5 min: test and optimize
```

---

*Last updated: 2026-01-24 | Progress: 26/174 (15%) | ~248h remaining*

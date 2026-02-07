# Google L6 Interview Prep: ROI-Based Slices

## Your Current Progress Summary

```
YOUR PROGRESS AT A GLANCE
================================================================================

COMPLETED: 26 problems across 8 patterns
================================================================================

PATTERN CONFIDENCE:
Trees           ████████████████████  100%  (7/9 problems)
Sliding Window  ████████████████████  100%  (3/3 problems) - MASTERED
Arrays/Hashing  ████████████████░░░░   81%  (5/6 problems)
Big-O Analysis  ████████████████░░░░   80%  (conceptual)
Binary Search   ███████████████░░░░░   75%  (3/4 problems)
Graphs          ███████████░░░░░░░░░   55%  (4/8 problems)
Recursion       █████████░░░░░░░░░░░   45%  (3/5 problems)
Two Pointers    █████░░░░░░░░░░░░░░░   25%  (1/4 problems)
Dynamic Prog    ░░░░░░░░░░░░░░░░░░░░    0%  (0/7 problems) ⚠️ CRITICAL GAP

================================================================================
```

### Problems You've Already Completed

```
COMPLETED PROBLEMS (26 total)
────────────────────────────────────────────────────────────────────────────────
Arrays & Hashing (5):
  ✓ Two Sum
  ✓ Group Anagrams
  ✓ Top K Frequent Elements
  ✓ Subarray Sum Equals K
  ✓ Product of Array Except Self

Sliding Window (3) - MASTERED:
  ✓ Longest Substring Without Repeating Characters
  ✓ Minimum Window Substring
  ✓ Permutation in String

Binary Search (3):
  ✓ Binary Search
  ✓ Search in Rotated Sorted Array
  ✓ Koko Eating Bananas

Recursion (3):
  ✓ Fibonacci Number
  ✓ Climbing Stairs
  ✓ Power(x, n)

Trees (7):
  ✓ Binary Tree Inorder Traversal
  ✓ Maximum Depth of Binary Tree
  ✓ Validate Binary Search Tree
  ✓ Binary Tree Level Order Traversal
  ✓ Lowest Common Ancestor of BST
  ✓ Path Sum
  ✓ Binary Tree Right Side View

Graphs (4):
  ✓ Number of Islands
  ✓ Clone Graph
  ✓ Rotting Oranges
  ✓ 01 Matrix

Two Pointers (1):
  ✓ Linked List Cycle
────────────────────────────────────────────────────────────────────────────────
```

---

## Your Velocity Profile

```
YOUR PACE (Last 31 Days)
================================================================================

WEEKLY BREAKDOWN:
Week of Dec 22:  ████░░░░░░░░░░░░░░░░  4 problems
Week of Dec 29:  ████░░░░░░░░░░░░░░░░  4 problems
Week of Jan 05:  ███░░░░░░░░░░░░░░░░░  3 problems
Week of Jan 12:  ██████████████░░░░░░  14 problems  ← You CAN sprint
Week of Jan 19:  █░░░░░░░░░░░░░░░░░░░  1 problem (partial)

────────────────────────────────────────────────────────────────────────────────
TOTAL: 26 problems | 31 days | 15 active days (48%)
────────────────────────────────────────────────────────────────────────────────

KEY METRICS:
├── Weekly average: 5.2 problems/week
├── Per active day: 1.7 problems
├── Active days: Every other day roughly
├── Weekday/Weekend: 62% / 38% (weekdays are productive!)
└── Sprint capacity: 14/week proven (Week of Jan 12)

DAY OF WEEK PATTERN:
Mon ▓           1      Tue ▓▓▓▓        4      Wed ▓▓          2
Thu ▓▓▓▓▓▓▓▓    8 ←    Fri ▓           1
Sat ▓▓▓▓▓▓      6      Sun ▓▓▓▓        4

Thursday is your power day. Leverage it.
================================================================================
```

---

## Timeline Estimates (Based on YOUR Pace)

```
SCENARIO PLANNING
================================================================================

                            SLICE 1    SLICE 2    SLICE 3    FULL PREP
                            (22 prob)  (+18 prob) (+13 prob) (53 total)
────────────────────────────────────────────────────────────────────────────────
Current pace (5/week)       4 weeks    8 weeks    10.5 weeks Interview @ 11 wks
Moderate focus (7/week)     3 weeks    5.5 weeks  7.5 weeks  Interview @ 8 wks
Serious mode (10/week)      2 weeks    4 weeks    5.5 weeks  Interview @ 6 wks
Sprint mode (14/week)       1.5 weeks  3 weeks    4 weeks    Interview @ 4 wks
────────────────────────────────────────────────────────────────────────────────

INTERVIEW READY PROBABILITY:
After Slice 1: 70% pass rate  ← "Survival minimum"
After Slice 2: 85% pass rate  ← "Strong candidate"
After Slice 3: 93% pass rate  ← "Very well prepared"

================================================================================
```

---

# THE SLICES (Corrected Sequence)

## Philosophy: Why These Problems?

```
SELECTION CRITERIA:
1. Google interview frequency (Blind 75, LeetCode frequency tags)
2. Pattern coverage (not problem count)
3. Your existing gaps (skip mastered areas)
4. Compound learning (each problem builds on previous)
5. Time-to-value ratio (Medium > Easy for ROI, Hard only when essential)

CORRECTIONS APPLIED:
- LRU Cache moved to Slice 1 (mandatory, shouldn't wait)
- Maximum Subarray added (Kadane's is DP foundation)
- Decode Ways moved to Slice 1 (basic 1D DP, not hard)
- Path Sum II added (bridge before Max Path Sum)
- Generate Parentheses added (recursion → backtracking bridge)
- Reverse Linked List moved earlier (foundation)
- Median of Two Sorted Arrays removed (low ROI)
- Implement Trie added (high value pattern)
- Jump Game added (Blind 75, greedy/DP hybrid)
```

---

## SLICE 1: SURVIVAL KIT (22 Problems)

**Goal:** If interview happens tomorrow after completing this, you pass 70% of coding rounds.

```
YOUR SLICE 1 PROGRESS
================================================================================
Completed:  0/22 problems (0%)
Remaining: 22 problems

From your existing progress that OVERLAPS with Slice 1:
  ✓ None - Slice 1 focuses on your gaps (DP, advanced graphs, tree hard)

Your mastered areas (Sliding Window, basic Trees, basic Graphs) are NOT in
Slice 1 because you don't need to redo them.
================================================================================
```

**What this covers:**
- DP fundamentals (Google's #1 pattern) - YOU HAVE 0% HERE
- Advanced Tree problems (Path Sum II, Max Path Sum, Kth Smallest BST)
- Graph cycle detection & shortest paths (Course Schedule, Dijkstra)
- Two Pointers completion (3Sum, Container, Trapping Rain Water)
- LRU Cache (MANDATORY design problem)

**What this skips (you already know):**
- Sliding Window (you mastered it at 100%)
- Basic Trees (you're at 100% confidence)
- Basic Graphs DFS (Number of Islands, Clone Graph - done)
- Arrays basics (you're at 81%)

```
SLICE 1: SURVIVAL KIT
================================================================================
22 problems | ~35-40 hours | Interview-ready: 70%
================================================================================

PRIORITY 1: DP FUNDAMENTALS (10 problems) ⭐⭐ CRITICAL GAP
────────────────────────────────────────────────────────────────────────────────
Your DP is at 0%. This is Google's most tested pattern. These 10 problems
give you the mental models for 80% of DP questions.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│ 1 │ Maximum Subarray             │ Medium │ Kadane's       │ ○ TODO │
│ 2 │ House Robber                 │ Medium │ Take/Skip      │ ○ TODO │
│ 3 │ House Robber II              │ Medium │ Circular       │ ○ TODO │
│ 4 │ Decode Ways                  │ Medium │ Fib+Constraints│ ○ TODO │
│ 5 │ Coin Change                  │ Medium │ Unbounded      │ ○ TODO │
│ 6 │ Longest Increasing Subseq    │ Medium │ Classic LIS    │ ○ TODO │
│ 7 │ Unique Paths                 │ Medium │ 2D Grid        │ ○ TODO │
│ 8 │ Minimum Path Sum             │ Medium │ 2D + Weights   │ ○ TODO │
│ 9 │ Longest Common Subsequence   │ Medium │ String DP      │ ○ TODO │
│10 │ Best Time Buy/Sell Stock II  │ Medium │ Unlimited Txn  │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

After these 10: You can recognize and solve basic DP in interviews.

PRIORITY 2: GRAPH ESSENTIALS (5 problems) ⭐ PARTIAL GAP
────────────────────────────────────────────────────────────────────────────────
You have basic DFS (Number of Islands, Clone Graph, Rotting Oranges, 01 Matrix).
You're missing cycle detection (Course Schedule) and weighted shortest paths
(Dijkstra) - both frequently tested at Google.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│11 │ Course Schedule              │ Medium │ Cycle Detection│ ○ TODO │
│12 │ Course Schedule II           │ Medium │ Topo Sort      │ ○ TODO │
│13 │ Network Delay Time           │ Medium │ Dijkstra       │ ○ TODO │
│14 │ Number of Provinces          │ Medium │ Union-Find     │ ○ TODO │
│15 │ Shortest Path Binary Matrix  │ Medium │ BFS Grid       │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

After these 5: You can handle cycle, topo sort, Dijkstra, Union-Find basics.

PRIORITY 3: TREE COMPLETION (3 problems) ⭐ NEAR COMPLETE
────────────────────────────────────────────────────────────────────────────────
You're at 100% confidence with 7 done. These 3 fill the HARD gaps.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│16 │ Path Sum II                  │ Medium │ All Paths      │ ○ TODO │
│17 │ Binary Tree Max Path Sum     │ Hard   │ Any-to-Any     │ ○ TODO │
│18 │ Kth Smallest Element BST     │ Medium │ BST + Inorder  │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

Note: You have Path Sum (Easy) done. Path Sum II is the Medium follow-up.
Binary Tree Max Path Sum is a Google FAVORITE.

PRIORITY 4: TWO POINTERS COMPLETION (3 problems)
────────────────────────────────────────────────────────────────────────────────
You're at 25% (only Linked List Cycle done). These are bread-and-butter.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│19 │ 3Sum                         │ Medium │ Converging     │ ○ TODO │
│20 │ Container With Most Water    │ Medium │ Greedy+2Ptr    │ ○ TODO │
│21 │ Trapping Rain Water          │ Hard   │ Multiple       │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

PRIORITY 5: DESIGN (1 problem) ⭐⭐ MANDATORY
────────────────────────────────────────────────────────────────────────────────
LRU Cache is THE most asked design problem. Must be cold-perfect.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│22 │ LRU Cache                    │ Medium │ Hash + DLL     │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

================================================================================
SLICE 1 SUMMARY:
├── DP: 10 problems (0% → foundation)
├── Graphs: 5 problems (55% → solid on advanced)
├── Trees: 3 problems (100% confidence → hard problems covered)
├── Two Pointers: 3 problems (25% → strong)
└── Design: 1 problem (LRU Cache mandatory)

Your current progress toward Slice 1: 0/22 (0%)

Time estimate at YOUR pace:
├── Current (5/week): 4.5 weeks
├── Moderate (7/week): 3 weeks
└── Sprint (14/week): 1.5 weeks
================================================================================
```

### Slice 1 Links (Copy-Paste Ready)

```
DP FUNDAMENTALS:
1.  https://leetcode.com/problems/maximum-subarray
2.  https://leetcode.com/problems/house-robber
3.  https://leetcode.com/problems/house-robber-ii
4.  https://leetcode.com/problems/decode-ways
5.  https://leetcode.com/problems/coin-change
6.  https://leetcode.com/problems/longest-increasing-subsequence
7.  https://leetcode.com/problems/unique-paths
8.  https://leetcode.com/problems/minimum-path-sum
9.  https://leetcode.com/problems/longest-common-subsequence
10. https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii

GRAPH ESSENTIALS:
11. https://leetcode.com/problems/course-schedule
12. https://leetcode.com/problems/course-schedule-ii
13. https://leetcode.com/problems/network-delay-time
14. https://leetcode.com/problems/number-of-provinces
15. https://leetcode.com/problems/shortest-path-in-binary-matrix

TREE COMPLETION:
16. https://leetcode.com/problems/path-sum-ii
17. https://leetcode.com/problems/binary-tree-maximum-path-sum
18. https://leetcode.com/problems/kth-smallest-element-in-a-bst

TWO POINTERS:
19. https://leetcode.com/problems/3sum
20. https://leetcode.com/problems/container-with-most-water
21. https://leetcode.com/problems/trapping-rain-water

DESIGN:
22. https://leetcode.com/problems/lru-cache
```

---

## SLICE 2: PATTERN DEPTH (18 Problems)

**Goal:** After Slice 1 + Slice 2, you pass 85% of coding rounds.

```
YOUR SLICE 2 PROGRESS
================================================================================
Completed:  0/18 problems (0%)
Remaining: 18 problems

Prerequisites: Complete Slice 1 first (especially DP fundamentals)
================================================================================
```

**What this adds:**
- Advanced DP patterns (Knapsack variants, Edit Distance)
- Backtracking fundamentals (Google loves N-Queens, Word Search)
- Heap patterns (Top-K, Merge K, Two-Heap)
- Linked Lists (Reverse, Merge - foundation for design)
- Monotonic stack (Histogram, temperatures)

```
SLICE 2: PATTERN DEPTH
================================================================================
18 problems | ~30-35 hours | Cumulative interview-ready: 85%
================================================================================

PRIORITY 6: ADVANCED DP (5 problems)
────────────────────────────────────────────────────────────────────────────────
Build on Slice 1 DP foundation with harder patterns.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│23 │ Partition Equal Subset Sum   │ Medium │ 0/1 Knapsack   │ ○ TODO │
│24 │ Edit Distance                │ Medium │ String DP      │ ○ TODO │
│25 │ Coin Change 2                │ Medium │ Count Combos   │ ○ TODO │
│26 │ Target Sum                   │ Medium │ Subset Sum     │ ○ TODO │
│27 │ Maximal Square               │ Medium │ 2D Different   │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

PRIORITY 7: RECURSION BRIDGE (1 problem)
────────────────────────────────────────────────────────────────────────────────
You have 45% recursion. This bridges to backtracking.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│28 │ Generate Parentheses         │ Medium │ Constraint Rec │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

PRIORITY 8: BACKTRACKING (5 problems) ⭐ NEW PATTERN
────────────────────────────────────────────────────────────────────────────────
You have 0% here. Google loves constraint satisfaction problems.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│29 │ Subsets                      │ Medium │ Include/Exclude│ ○ TODO │
│30 │ Permutations                 │ Medium │ Arrangement    │ ○ TODO │
│31 │ Combination Sum              │ Medium │ With Repeats   │ ○ TODO │
│32 │ Word Search                  │ Medium │ Grid + BT      │ ○ TODO │
│33 │ N-Queens                     │ Hard   │ Constraint     │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

PRIORITY 9: HEAPS (4 problems) ⭐ NEW PATTERN
────────────────────────────────────────────────────────────────────────────────
Priority queues appear in scheduling, top-K, and merge problems.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│34 │ Kth Largest Element          │ Medium │ Min Heap       │ ○ TODO │
│35 │ Merge K Sorted Lists         │ Hard   │ Heap + Merge   │ ○ TODO │
│36 │ Find Median Data Stream      │ Hard   │ Two Heaps      │ ○ TODO │
│37 │ Task Scheduler               │ Medium │ Heap + Greedy  │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

PRIORITY 10: LINKED LISTS (2 problems)
────────────────────────────────────────────────────────────────────────────────
Foundation for design problems and pointer manipulation.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│38 │ Reverse Linked List          │ Easy   │ Reversal       │ ○ TODO │
│39 │ Merge Two Sorted Lists       │ Easy   │ Basic Merge    │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

PRIORITY 11: MONOTONIC STACK (2 problems)
────────────────────────────────────────────────────────────────────────────────
"Next greater/smaller" pattern appears more than you'd expect.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│40 │ Daily Temperatures           │ Medium │ Next Greater   │ ○ TODO │
│41 │ Largest Rectangle Histogram  │ Hard   │ Area Problems  │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

================================================================================
SLICE 2 SUMMARY (adds to Slice 1):
├── Advanced DP: 5 problems (foundation → intermediate)
├── Recursion Bridge: 1 problem (→ backtracking)
├── Backtracking: 5 problems (0% → competent)
├── Heaps: 4 problems (0% → solid)
├── Linked Lists: 2 problems (foundation)
└── Monotonic Stack: 2 problems (pattern known)

Your current progress toward Slice 2: 0/18 (0%)
Cumulative after Slice 1+2: 40 problems

Time estimate at YOUR pace:
├── Current (5/week): +3.5 weeks (8 weeks total)
├── Moderate (7/week): +2.5 weeks (5.5 weeks total)
└── Sprint (14/week): +1.5 weeks (3 weeks total)
================================================================================
```

### Slice 2 Links

```
ADVANCED DP:
23. https://leetcode.com/problems/partition-equal-subset-sum
24. https://leetcode.com/problems/edit-distance
25. https://leetcode.com/problems/coin-change-2
26. https://leetcode.com/problems/target-sum
27. https://leetcode.com/problems/maximal-square

RECURSION BRIDGE:
28. https://leetcode.com/problems/generate-parentheses

BACKTRACKING:
29. https://leetcode.com/problems/subsets
30. https://leetcode.com/problems/permutations
31. https://leetcode.com/problems/combination-sum
32. https://leetcode.com/problems/word-search
33. https://leetcode.com/problems/n-queens

HEAPS:
34. https://leetcode.com/problems/kth-largest-element-in-an-array
35. https://leetcode.com/problems/merge-k-sorted-lists
36. https://leetcode.com/problems/find-median-from-data-stream
37. https://leetcode.com/problems/task-scheduler

LINKED LISTS:
38. https://leetcode.com/problems/reverse-linked-list
39. https://leetcode.com/problems/merge-two-sorted-lists

MONOTONIC STACK:
40. https://leetcode.com/problems/daily-temperatures
41. https://leetcode.com/problems/largest-rectangle-in-histogram
```

---

## SLICE 3: MASTERY & EDGE CASES (13 Problems)

**Goal:** After all slices, you pass 93%+ of coding rounds.

```
YOUR SLICE 3 PROGRESS
================================================================================
Completed:  0/13 problems (0%)
Remaining: 13 problems

Prerequisites: Complete Slice 1 and Slice 2 first
================================================================================
```

**What this adds:**
- Hard DP variants (State Machine, Tree DP)
- Graph advanced (Alien Dictionary, Accounts Merge)
- Linked Lists advanced (Reorder, Copy Random)
- Intervals (scheduling problems)
- Trie (prefix tree pattern)
- Greedy (Jump Game)

```
SLICE 3: MASTERY & EDGE CASES
================================================================================
13 problems | ~25 hours | Cumulative interview-ready: 93%+
================================================================================

PRIORITY 12: HARD DP (3 problems)
────────────────────────────────────────────────────────────────────────────────
These separate "good" from "excellent" candidates.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│42 │ Best Time Stock w/ Cooldown  │ Medium │ State Machine  │ ○ TODO │
│43 │ House Robber III             │ Medium │ DP on Trees    │ ○ TODO │
│44 │ Dungeon Game                 │ Hard   │ Backward DP    │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

PRIORITY 13: ADVANCED GRAPHS (3 problems)
────────────────────────────────────────────────────────────────────────────────
│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│45 │ Alien Dictionary             │ Hard   │ Build+TopoSort │ ○ TODO │
│46 │ Accounts Merge               │ Medium │ Union-Find App │ ○ TODO │
│47 │ Cheapest Flights K Stops     │ Medium │ Constrained BFS│ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

PRIORITY 14: LINKED LISTS ADVANCED (2 problems)
────────────────────────────────────────────────────────────────────────────────
│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│48 │ Reorder List                 │ Medium │ Multi-step     │ ○ TODO │
│49 │ Copy List Random Pointer     │ Medium │ Deep Copy      │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

PRIORITY 15: INTERVALS (3 problems)
────────────────────────────────────────────────────────────────────────────────
Scheduling problems are practical and common.

│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│50 │ Merge Intervals              │ Medium │ Sort + Merge   │ ○ TODO │
│51 │ Meeting Rooms II             │ Medium │ Heap/Sweep     │ ○ TODO │
│52 │ Non-overlapping Intervals    │ Medium │ Greedy         │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

PRIORITY 16: TRIE + GREEDY (2 problems)
────────────────────────────────────────────────────────────────────────────────
│ # │ Problem                      │ Diff   │ Pattern        │ Status │
├───┼──────────────────────────────┼────────┼────────────────┼────────┤
│53 │ Implement Trie               │ Medium │ Prefix Tree    │ ○ TODO │
│54 │ Jump Game                    │ Medium │ Greedy/DP      │ ○ TODO │
└───┴──────────────────────────────┴────────┴────────────────┴────────┘

================================================================================
SLICE 3 SUMMARY (adds to Slice 1+2):
├── Hard DP: 3 problems (intermediate → advanced)
├── Advanced Graphs: 3 problems (solid → expert)
├── Linked Lists Advanced: 2 problems (foundation → competent)
├── Intervals: 3 problems (0% → solid)
└── Trie + Greedy: 2 problems (new patterns)

Your current progress toward Slice 3: 0/13 (0%)
Cumulative after all slices: 53 problems (was 55, optimized to 53)

Time estimate at YOUR pace:
├── Current (5/week): +2.5 weeks (10.5 weeks total)
├── Moderate (7/week): +2 weeks (7.5 weeks total)
└── Sprint (14/week): +1 week (4 weeks total)
================================================================================
```

### Slice 3 Links

```
HARD DP:
42. https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown
43. https://leetcode.com/problems/house-robber-iii
44. https://leetcode.com/problems/dungeon-game

ADVANCED GRAPHS:
45. https://leetcode.com/problems/alien-dictionary
46. https://leetcode.com/problems/accounts-merge
47. https://leetcode.com/problems/cheapest-flights-within-k-stops

LINKED LISTS ADVANCED:
48. https://leetcode.com/problems/reorder-list
49. https://leetcode.com/problems/copy-list-with-random-pointer

INTERVALS:
50. https://leetcode.com/problems/merge-intervals
51. https://leetcode.com/problems/meeting-rooms-ii
52. https://leetcode.com/problems/non-overlapping-intervals

TRIE + GREEDY:
53. https://leetcode.com/problems/implement-trie-prefix-tree
54. https://leetcode.com/problems/jump-game
```

---

## Complete Progress Dashboard

```
OVERALL PROGRESS SUMMARY
================================================================================

YOUR COMPLETED (26 problems - outside slices, already mastered):
────────────────────────────────────────────────────────────────────────────────
These problems overlap with fast_track curriculum but are NOT in Google L6
slices because:
  • Slice 1 focuses on your GAPS (DP=0%, advanced graphs, hard trees)
  • Your mastered patterns don't need repetition

Completed patterns that give you a HEAD START:
  ✓ Sliding Window (100%) - Rate limiting concepts, Google loves this
  ✓ Basic Trees (100%) - You can skip easy tree problems
  ✓ Basic Graphs DFS (4 done) - Number of Islands, Clone Graph, etc.
  ✓ Binary Search (75%) - Strong foundation
  ✓ Arrays/Hashing (81%) - Fundamentals solid

SLICE PROGRESS:
────────────────────────────────────────────────────────────────────────────────
                    Problems    Done    Remaining   Progress
Slice 1 (Survival)     22        0         22         0%
Slice 2 (Depth)        18        0         18         0%
Slice 3 (Mastery)      13        0         13         0%
────────────────────────────────────────────────────────────────────────────────
TOTAL REMAINING:       53        0         53         0%

COMBINED VIEW (Your total DSA journey):
────────────────────────────────────────────────────────────────────────────────
Already completed:                26 problems (fast_track)
Google L6 Slices remaining:       53 problems
────────────────────────────────────────────────────────────────────────────────
Total unique problems after:      79 problems (some overlap)

================================================================================
```

---

## Timeline Matrix

```
INTERVIEW SCHEDULING GUIDE
================================================================================

                    YOUR CURRENT PACE (5/week)    FOCUSED PACE (10/week)
────────────────────────────────────────────────────────────────────────────────
After 2 weeks       10 problems (½ Slice 1)       22 problems (Slice 1) ✓
After 4 weeks       20 problems (Slice 1) ✓       40 problems (Slice 1+2) ✓
After 6 weeks       30 problems (Slice 1+½2)      53 problems (ALL) ✓
After 8 weeks       40 problems (Slice 1+2) ✓     -
After 10.5 weeks    53 problems (ALL) ✓           -
────────────────────────────────────────────────────────────────────────────────

WHEN TO SCHEDULE INTERVIEW:
================================================================================

"I can go moderate focus (7/week)":
├── Minimum: 3 weeks (Slice 1 done, 70% ready)
├── Recommended: 5.5 weeks (Slice 1+2 done, 85% ready)
└── Ideal: 7.5 weeks (All slices + review week, 93%+ ready)

"I can sprint (10-14/week)":
├── Minimum: 2 weeks (Slice 1 done, 70% ready)
├── Recommended: 4 weeks (Slice 1+2 done, 85% ready)
└── Ideal: 5-6 weeks (All slices + mock interviews, 93%+ ready)

"I'll maintain current pace (5/week)":
├── Minimum: 4.5 weeks (Slice 1 done, 70% ready)
├── Recommended: 8 weeks (Slice 1+2 done, 85% ready)
└── Ideal: 10.5 weeks (All slices, 93%+ ready)

================================================================================
```

---

## How to Talk to Your Recruiter

```
SCRIPT FOR RECRUITER CONVERSATION:
================================================================================

"I want to make sure I'm fully prepared to represent myself well in the
interview. I've been actively preparing and would feel most confident
with an interview date [X weeks] from now. Is there flexibility in
scheduling?"

RECOMMENDED ASK: 6 weeks
├── Gives you Slice 1 + Slice 2 at moderate pace
├── Buffer for work/life interruptions
├── 1 week for review before interview
└── Shows you're serious but not stalling

IF THEY PUSH FOR SOONER:
├── 4 weeks: Doable with focused effort (Slice 1 + partial Slice 2)
├── 3 weeks: Tight but possible (complete Slice 1)
├── 2 weeks: Request more time, explain active prep
└── <2 weeks: Consider if you want to proceed or defer

================================================================================
```

---

## The Final Week Protocol

```
FINAL WEEK BEFORE INTERVIEW (NO NEW PROBLEMS)
================================================================================

Day 7: Review Slice 1 DP problems (redo 3-4)
Day 6: Review Slice 1 Graphs (redo 2-3)
Day 5: Review Slice 2 Backtracking + Heaps (redo 3-4)
Day 4: Review LRU Cache + Design (must be cold-perfect)
Day 3: Mock interview #1 (45 min, 1 medium)
Day 2: Mock interview #2 (45 min, 1 medium-hard)
Day 1: Light review, rest, prepare behavioral stories

DO NOT:
├── Learn new problems
├── Cram until 3am
├── Skip sleep
└── Panic-study morning of

================================================================================
```

---

## Quick Reference Card

```
================================================================================
GOOGLE L6 PREP: QUICK REFERENCE
================================================================================

YOUR STATUS:
├── Completed: 26 problems (fast_track patterns)
├── Mastered: Sliding Window (100%), Trees (100%)
├── Strong: Arrays (81%), Binary Search (75%)
├── Gap: DP (0%), Backtracking (0%), Heaps (0%), Design (0%)
└── Pace: 5.2 problems/week (can sprint to 14)

THE SLICES (53 total problems):
├── Slice 1: 22 problems → 70% ready (DP, Graphs, Trees hard, Two Pointers, LRU)
├── Slice 2: 18 problems → 85% ready (Adv DP, Backtracking, Heaps, Linked Lists)
└── Slice 3: 13 problems → 93% ready (Hard DP, Intervals, Trie, Greedy)

YOUR PROGRESS:
├── Slice 1: 0/22 (0%)
├── Slice 2: 0/18 (0%)
└── Slice 3: 0/13 (0%)

TIMELINE AT MODERATE PACE (7/week):
├── Week 3: Slice 1 done (interview-survivable)
├── Week 5.5: Slice 2 done (strong candidate)
└── Week 7.5: All done + review (excellent)

TOP 5 PROBLEMS IF YOU CAN ONLY DO 5:
1. Maximum Subarray (Kadane's - DP foundation)
2. Coin Change (DP unbounded knapsack)
3. Course Schedule (Graph cycles)
4. LRU Cache (Design, mandatory)
5. Binary Tree Max Path Sum (Tree DP, Google fav)

================================================================================
```

---

*Last updated: 2026-01-24*
*Total: 53 problems across 3 slices (optimized from 55)*
*Your completed: 26 problems (fast_track)*
*Your pace: 5.2/week sustained, 14/week sprint capable*

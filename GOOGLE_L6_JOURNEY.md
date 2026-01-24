# Google L6 Prep: Your Complete Learning Journey

## Purpose of This Document

This is your **learning path** document - it shows HOW to get from where you are to interview-ready.

**Two documents, two purposes:**
- `GOOGLE_L6_JOURNEY.md` (this file) = Pedagogical sequence (how to learn efficiently)
- `GOOGLE_L6_SLICES.md` = Interview priorities (what matters for passing)

**Key insight:** You can't jump directly into DP. This document shows the right sequence to GET THERE from your current position.

---

## 1. YOUR CURRENT POSITION

```
================================================================================
YOUR PROGRESS AT A GLANCE
================================================================================

COMPLETED: 26 problems across 8 patterns
You are NOT starting from zero - you have solid foundations!

================================================================================

PATTERN MAP (Visual Progress):

Trees           ████████████████████  100%  ✓ MASTERED
Sliding Window  ████████████████████  100%  ✓ MASTERED
Arrays/Hashing  ████████████████░░░░   81%  ✓ Strong
Big-O Analysis  ████████████████░░░░   80%  ✓ Strong (conceptual)
Binary Search   ███████████████░░░░░   75%  ✓ Strong
Graphs          ███████████░░░░░░░░░   55%  ◐ Partial (basics done, need advanced)
Recursion       █████████░░░░░░░░░░░   45%  ◐ CRITICAL for DP
Two Pointers    █████░░░░░░░░░░░░░░░   25%  ◐ Gap (foundation)
Dynamic Prog    ░░░░░░░░░░░░░░░░░░░░    0%  ○ MAIN TARGET
Backtracking    ░░░░░░░░░░░░░░░░░░░░    0%  ○ After DP
Heaps           ░░░░░░░░░░░░░░░░░░░░    0%  ○ New pattern

================================================================================
```

### Your 26 Completed Problems (Mapped by Pattern)

```
ARRAYS & HASHING (5 problems) - 81%
├── ✓ Two Sum
├── ✓ Group Anagrams
├── ✓ Top K Frequent Elements
├── ✓ Subarray Sum Equals K
├── ✓ Product of Array Except Self
└── ○ Rotate Image (remaining)

SLIDING WINDOW (3 problems) - 100% MASTERED
├── ✓ Longest Substring Without Repeating Characters
├── ✓ Minimum Window Substring
└── ✓ Permutation in String

BINARY SEARCH (3 problems) - 75%
├── ✓ Binary Search (template)
├── ✓ Search in Rotated Sorted Array
├── ✓ Koko Eating Bananas
└── ○ Capacity to Ship Packages (remaining)

TWO POINTERS (1 problem) - 25%
├── ✓ Linked List Cycle
└── ○ 3Sum, Container, Trapping Rain Water (remaining)

RECURSION (3 problems) - 45%
├── ✓ Fibonacci Number
├── ✓ Climbing Stairs
├── ✓ Power(x, n)
└── ○ Decode Ways, Generate Parentheses (remaining)

TREES (7 problems) - 100% confidence
├── ✓ Binary Tree Inorder Traversal
├── ✓ Maximum Depth of Binary Tree
├── ✓ Validate Binary Search Tree
├── ✓ Binary Tree Level Order Traversal
├── ✓ Lowest Common Ancestor of BST
├── ✓ Path Sum
├── ✓ Binary Tree Right Side View
└── ○ Kth Smallest BST, Max Path Sum (Slice 1 targets)

GRAPHS (4 problems) - 55%
├── ✓ Number of Islands
├── ✓ Clone Graph
├── ✓ Rotting Oranges
├── ✓ 01 Matrix
└── ○ Course Schedule, Dijkstra, Union-Find (Slice 1 targets)

DYNAMIC PROGRAMMING (0 problems) - 0%
└── ○ CRITICAL GAP - This is your main focus
```

### Which of Your Problems Are Prerequisites for Slice 1?

| Your Problem | Why It Matters for Slice 1 |
|--------------|---------------------------|
| Fibonacci | Foundation for DP thinking |
| Climbing Stairs | DP state transition template |
| Power(x,n) | Divide-conquer recursion |
| Number of Islands | DFS foundation for Course Schedule |
| Clone Graph | Graph traversal with visited set |
| Path Sum | Foundation for Path Sum II/III |
| Validate BST | BST property for Kth Smallest |
| All sliding window | Already mastered, skip in Slice 1 |

### Which Are Bonus (Not Directly in Slice 1)?

| Your Problem | Where It Fits |
|--------------|---------------|
| Two Sum | Arrays foundation (done) |
| Group Anagrams | Hashing pattern (done) |
| Rotting Oranges | Multi-source BFS (bonus) |
| 01 Matrix | BFS distance (bonus) |

**Bottom line:** Your 26 problems ARE the prerequisites. You just need 2-4 gap fillers before you're ready for Slice 1 core.

---

## 2. THE LEARNING MAP

### Pattern Dependency Graph

This shows how patterns build on each other. You can't skip levels.

```
THE DSA PATTERN DEPENDENCY MAP
================================================================================

                         ┌─────────────────┐
                         │  Big-O Analysis │  ✓ You have this (80%)
                         │   (Foundation)  │
                         └────────┬────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
    ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
    │  Arrays &   │ ✓81%   │   Binary    │ ✓75%   │  Recursion  │ ◐45%
    │   Hashing   │        │   Search    │        │             │
    └──────┬──────┘        └─────────────┘        └──────┬──────┘
           │                                              │
    ┌──────┴──────┐                          ┌───────────┼───────────┐
    │             │                          │           │           │
    ▼             ▼                          ▼           ▼           ▼
┌────────┐  ┌────────────┐              ┌────────┐  ┌────────┐  ┌────────────┐
│  Two   │  │  Sliding   │  ✓100%       │ Trees  │  │   DP   │  │Backtracking│
│Pointers│  │   Window   │  MASTERED    │        │  │        │  │            │
│ ◐25%   │  │            │              │ ✓100%  │  │  ○0%   │  │    ○0%     │
└────────┘  └────────────┘              └───┬────┘  └────────┘  └────────────┘
                                            │
                                            ▼
                                       ┌────────┐
                                       │ Graphs │  ◐55%
                                       └────────┘


LEGEND:
  ✓ Mastered (75%+)    ◐ Partial (25-74%)    ○ Not started (0%)

================================================================================
```

### YOUR Position on the Map

```
================================================================================
                           WHERE YOU ARE
================================================================================

COMPLETED PATTERNS (can skip):
┌─────────────────────────────────────────────────────────────────────────────┐
│  ✓ Sliding Window (100%) - Skip in Slice 1                                  │
│  ✓ Trees basics (100%) - Just need hard problems                            │
│  ✓ Binary Search (75%) - Strong foundation                                  │
│  ✓ Arrays/Hashing (81%) - Fundamentals solid                                │
└─────────────────────────────────────────────────────────────────────────────┘

PARTIAL PATTERNS (need completion):
┌─────────────────────────────────────────────────────────────────────────────┐
│  ◐ Recursion (45%) - CRITICAL: Must complete before DP                      │
│  ◐ Two Pointers (25%) - 3Sum, Container are in Slice 1 anyway               │
│  ◐ Graphs (55%) - Basic DFS done, need cycle detection + Dijkstra           │
└─────────────────────────────────────────────────────────────────────────────┘

NOT STARTED (your main targets):
┌─────────────────────────────────────────────────────────────────────────────┐
│  ○ Dynamic Programming (0%) - Google's #1 pattern, CRITICAL GAP             │
│  ○ Backtracking (0%) - Requires DP/Recursion first                          │
│  ○ Heaps (0%) - New pattern, independent                                    │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                      ↓ YOU ARE HERE ↓
================================================================================

    [Recursion 45%] ──bridge──> [DP 0%] ──then──> [Backtracking 0%]
         │                          │
         └── You need 2-4 problems ─┘
             to cross this bridge

================================================================================
```

### The Critical Path: Recursion → DP

This is the most important dependency in your journey:

```
THE RECURSION → DP BRIDGE
================================================================================

Your current recursion skills:
  ✓ Fibonacci Number         (basic recursion + memoization)
  ✓ Climbing Stairs          (counting paths = DP pattern)
  ✓ Power(x, n)              (divide and conquer)

What you're missing for DP readiness:
  ○ Decode Ways              Recursion with constraints → direct DP bridge
  ○ Generate Parentheses     Constraint-based recursion → backtracking bridge

Why this matters:
┌─────────────────────────────────────────────────────────────────────────────┐
│ DP is just "recursion + memoization + bottom-up thinking"                   │
│                                                                             │
│ If you can't write clean recursive solutions, you'll struggle with DP.     │
│ Decode Ways forces you to think about state transitions - exactly what     │
│ you need for House Robber, Coin Change, etc.                               │
└─────────────────────────────────────────────────────────────────────────────┘

AFTER these 2 problems, you'll have:
  • Constraint-based recursion
  • Overlapping subproblems recognition
  • State transition thinking

Then Maximum Subarray (Kadane's) becomes intuitive.

================================================================================
```

---

## 3. COMPLETE TIMELINE: Your Full Journey

```
================================================================================
YOUR COMPLETE LEARNING JOURNEY
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 0: COMPLETED                                                         │
│  26 problems | You are HERE                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Arrays/Hashing (5): Two Sum, Group Anagrams, Top K Frequent,               │
│                      Subarray Sum K, Product Except Self                    │
│                                                                             │
│  Sliding Window (3): Longest Substring, Min Window, Permutation - MASTERED  │
│                                                                             │
│  Binary Search (3): Binary Search, Rotated Array, Koko Bananas              │
│                                                                             │
│  Two Pointers (1): Linked List Cycle                                        │
│                                                                             │
│  Recursion (3): Fibonacci, Climbing Stairs, Power(x,n)                      │
│                                                                             │
│  Trees (7): Inorder, Max Depth, Validate BST, Level Order,                  │
│             LCA BST, Path Sum, Right Side View - MASTERED                   │
│                                                                             │
│  Graphs (4): Number of Islands, Clone Graph, Rotting Oranges, 01 Matrix     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: GAP FILLERS                                                       │
│  2-4 problems | ~1 week                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CRITICAL (do these first):                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 1. Decode Ways (Medium)                                                │ │
│  │    • Recursion → DP bridge                                             │ │
│  │    • Fibonacci with constraints                                        │ │
│  │    • https://leetcode.com/problems/decode-ways                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  RECOMMENDED (will be in Slice 1 anyway):                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 2. 3Sum (Medium)                                                       │ │
│  │    • Two pointers completion                                           │ │
│  │    • Classic interview problem                                         │ │
│  │    • https://leetcode.com/problems/3sum                                │ │
│  │                                                                        │ │
│  │ 3. Container With Most Water (Medium)                                  │ │
│  │    • Optimization with two pointers                                    │ │
│  │    • https://leetcode.com/problems/container-with-most-water           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  OPTIONAL (for backtracking later):                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 4. Generate Parentheses (Medium)                                       │ │
│  │    • Recursion → backtracking bridge                                   │ │
│  │    • Can defer to Slice 2 if time-pressed                              │ │
│  │    • https://leetcode.com/problems/generate-parentheses                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  After Phase 1: You're ready for Slice 1 DP!                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: SLICE 1 (SURVIVAL)                                                │
│  22 problems | ~4 weeks at current pace | 70% interview-ready               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DP Fundamentals (10):           Graph Advanced (5):                        │
│    1. Maximum Subarray             11. Course Schedule                      │
│    2. House Robber                 12. Course Schedule II                   │
│    3. House Robber II              13. Network Delay Time (Dijkstra)        │
│    4. Decode Ways*                 14. Number of Provinces                  │
│    5. Coin Change                  15. Shortest Path Binary Matrix          │
│    6. Longest Increasing Subseq                                             │
│    7. Unique Paths                Tree Hard (3):                            │
│    8. Minimum Path Sum              16. Path Sum II                         │
│    9. Longest Common Subseq        17. Binary Tree Max Path Sum             │
│   10. Best Time Stock II           18. Kth Smallest BST                     │
│                                                                             │
│  Two Pointers (3):               Design (1):                                │
│   19. 3Sum*                        22. LRU Cache (MANDATORY)                │
│   20. Container*                                                            │
│   21. Trapping Rain Water                                                   │
│                                                                             │
│  * = If done in Phase 1, skip here (that's why 2-4 gap fillers)             │
│                                                                             │
│  See GOOGLE_L6_SLICES.md for full details and LeetCode links                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: SLICE 2 (DEPTH)                                                   │
│  18 problems | +3.5 weeks | 85% interview-ready                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Advanced DP (5):                Backtracking (5):                          │
│   23. Partition Equal Subset       29. Subsets                              │
│   24. Edit Distance                30. Permutations                         │
│   25. Coin Change 2                31. Combination Sum                      │
│   26. Target Sum                   32. Word Search                          │
│   27. Maximal Square               33. N-Queens                             │
│                                                                             │
│  Recursion Bridge (1):           Heaps (4):                                 │
│   28. Generate Parentheses*        34. Kth Largest Element                  │
│                                    35. Merge K Sorted Lists                 │
│  Linked Lists (2):                 36. Find Median Data Stream              │
│   38. Reverse Linked List          37. Task Scheduler                       │
│   39. Merge Two Sorted Lists                                                │
│                                  Monotonic Stack (2):                       │
│                                    40. Daily Temperatures                   │
│                                    41. Largest Rectangle Histogram          │
│                                                                             │
│  * = If done in Phase 1, skip here                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: SLICE 3 (MASTERY)                                                 │
│  13 problems | +2.5 weeks | 93% interview-ready                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Hard DP (3):                    Advanced Graphs (3):                       │
│   42. Stock w/ Cooldown            45. Alien Dictionary                     │
│   43. House Robber III             46. Accounts Merge                       │
│   44. Dungeon Game                 47. Cheapest Flights K Stops             │
│                                                                             │
│  Linked Lists Advanced (2):      Intervals (3):                             │
│   48. Reorder List                 50. Merge Intervals                      │
│   49. Copy Random Pointer          51. Meeting Rooms II                     │
│                                    52. Non-overlapping Intervals            │
│  Trie + Greedy (2):                                                         │
│   53. Implement Trie                                                        │
│   54. Jump Game                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
TOTAL JOURNEY:
├── Phase 0 (DONE):  26 problems
├── Phase 1 (GAP):   2-4 problems  (~1 week)
├── Phase 2 (S1):    22 problems   (~4 weeks) → 70% ready
├── Phase 3 (S2):    18 problems   (+3.5 weeks) → 85% ready
└── Phase 4 (S3):    13 problems   (+2.5 weeks) → 93% ready
────────────────────────────────────────────────────────────────────────────────
TOTAL: 26 (done) + 2-4 (gaps) + 53 (slices) = 81-83 unique problems
================================================================================
```

---

## 4. PEDAGOGICAL NOTES

### How to Learn DP (The Right Sequence)

```
================================================================================
DP LEARNING SEQUENCE (within Slice 1)
================================================================================

WEEK 1: 1D DP Foundation
────────────────────────────────────────────────────────────────────────────────
Day 1-2: Maximum Subarray (Kadane's)
  • Simplest DP problem
  • "Keep or start fresh" decision
  • No array needed (just O(1) space)

Day 3-4: House Robber
  • Take/skip pattern
  • dp[i] = max(dp[i-1], dp[i-2] + nums[i])
  • This pattern appears EVERYWHERE

Day 5: House Robber II (circular variant)
  • Same pattern, handle edge case
  • Shows how to modify base DP

WEEK 2: 1D DP with Constraints
────────────────────────────────────────────────────────────────────────────────
Day 1-2: Decode Ways
  • Fibonacci + validity constraints
  • You did this as gap filler, review pattern

Day 3-4: Coin Change
  • Unbounded knapsack
  • "Ways to reach target" template

Day 5: Longest Increasing Subsequence
  • O(n²) DP → O(n log n) with binary search
  • Classic pattern, many variants

WEEK 3: 2D DP
────────────────────────────────────────────────────────────────────────────────
Day 1-2: Unique Paths
  • Grid DP template
  • dp[i][j] = dp[i-1][j] + dp[i][j-1]

Day 3-4: Minimum Path Sum
  • Grid DP with weights
  • Same structure, min instead of count

Day 5: Longest Common Subsequence
  • String DP template
  • Two-string comparison pattern

WEEK 4: Variations + Review
────────────────────────────────────────────────────────────────────────────────
Day 1-2: Best Time Stock II (unlimited transactions)
  • State machine DP (hold/not hold)

Day 3-5: Review problematic patterns, redo 2-3 problems

================================================================================

KEY MENTAL MODELS:
────────────────────────────────────────────────────────────────────────────────
1. "What decision do I make at each step?"
   • Take or skip (House Robber)
   • Include or exclude (Knapsack)
   • Match or don't match (LCS)

2. "What's my state?"
   • Position in array/grid
   • Remaining capacity/target
   • Previous decision (for constraints)

3. "What's my recurrence?"
   • How does dp[i] relate to dp[i-1], dp[i-2], etc.?
   • Base cases: dp[0], dp[1]

================================================================================
```

### Interleaving Strategy (Avoid DP Fatigue)

```
================================================================================
RECOMMENDED DAILY SCHEDULE FOR SLICE 1
================================================================================

Don't do 10 DP problems in a row. Interleave to:
  • Avoid mental fatigue
  • Reinforce patterns through contrast
  • Keep motivation high

SAMPLE 4-WEEK SCHEDULE:
────────────────────────────────────────────────────────────────────────────────
WEEK 1:
  Mon: Maximum Subarray (DP)
  Tue: House Robber (DP)
  Wed: Course Schedule (Graph) ← break from DP
  Thu: House Robber II (DP)
  Fri: Path Sum II (Tree) ← break from DP
  Sat: Decode Ways (DP)
  Sun: Review / Light day

WEEK 2:
  Mon: Coin Change (DP)
  Tue: Course Schedule II (Graph)
  Wed: LIS (DP)
  Thu: Network Delay Time (Graph)
  Fri: Unique Paths (DP)
  Sat: 3Sum (Two Pointers)
  Sun: Review / Light day

WEEK 3:
  Mon: Minimum Path Sum (DP)
  Tue: Number of Provinces (Graph)
  Wed: LCS (DP)
  Thu: Container With Most Water (Two Pointers)
  Fri: Kth Smallest BST (Tree)
  Sat: Stock II (DP)
  Sun: Review / Light day

WEEK 4:
  Mon: Shortest Path Binary Matrix (Graph)
  Tue: Binary Tree Max Path Sum (Tree)
  Wed: Trapping Rain Water (Two Pointers)
  Thu: LRU Cache (Design) ← PRACTICE UNTIL COLD-PERFECT
  Fri: LRU Cache (Design) ← Yes, again
  Sat: Review weak DP problems
  Sun: Review / Mock interview

================================================================================
```

---

## 5. QUICK REFERENCE

```
================================================================================
WHAT DO I DO TOMORROW?
================================================================================

IF YOU HAVEN'T STARTED PHASE 1:
────────────────────────────────────────────────────────────────────────────────
  → Do: Decode Ways
  → URL: https://leetcode.com/problems/decode-ways
  → Why: It bridges your recursion skills to DP

IF YOU'VE DONE DECODE WAYS BUT NOT 3SUM:
────────────────────────────────────────────────────────────────────────────────
  → Do: 3Sum
  → URL: https://leetcode.com/problems/3sum
  → Why: Completes your two pointers foundation

IF YOU'VE DONE GAP FILLERS:
────────────────────────────────────────────────────────────────────────────────
  → Do: Maximum Subarray (Kadane's)
  → URL: https://leetcode.com/problems/maximum-subarray
  → Why: Simplest DP, start your Slice 1 journey

================================================================================

YOUR WEEKLY CHECKLIST:
────────────────────────────────────────────────────────────────────────────────
[ ] 5-7 new problems (adjust based on your pace)
[ ] 1-2 review problems (from previous weeks)
[ ] At least 2 different patterns per week
[ ] LRU Cache practice if you're past Week 3

================================================================================

TOP 5 "MUST KNOW COLD" PROBLEMS:
────────────────────────────────────────────────────────────────────────────────
1. LRU Cache - THE most asked design problem, must be instant
2. Maximum Subarray (Kadane's) - DP foundation, asked constantly
3. Course Schedule - Graph cycles, topo sort
4. Binary Tree Max Path Sum - Tree DP, Google favorite
5. Coin Change - DP template, unbounded knapsack

================================================================================

PROGRESS TRACKING:
────────────────────────────────────────────────────────────────────────────────
After each session, update this:

Phase 1 Gap Fillers: [ ] / 4
  [ ] Decode Ways
  [ ] 3Sum
  [ ] Container With Most Water
  [ ] Generate Parentheses (optional)

Slice 1: [ ] / 22
Slice 2: [ ] / 18
Slice 3: [ ] / 13

================================================================================
```

---

## Summary: Your Learning Path

```
================================================================================
THE BIG PICTURE
================================================================================

YOU ARE NOT STARTING FROM ZERO.

Your 26 completed problems are PREREQUISITES for Slice 1.
You just need 2-4 gap fillers to bridge recursion → DP.

THE PATH:
────────────────────────────────────────────────────────────────────────────────

[YOU ARE HERE]
      │
      │ ← Do Decode Ways (recursion → DP bridge)
      │ ← Do 3Sum, Container (two pointers completion)
      ▼
[PHASE 1 DONE - Ready for Slice 1 DP]
      │
      │ ← 22 problems: DP fundamentals + advanced graphs + tree hard
      │ ← ~4 weeks at your pace
      ▼
[SLICE 1 DONE - 70% interview ready]
      │
      │ ← 18 problems: advanced DP + backtracking + heaps
      │ ← ~3.5 weeks more
      ▼
[SLICE 2 DONE - 85% interview ready]
      │
      │ ← 13 problems: hard DP + intervals + trie
      │ ← ~2.5 weeks more
      ▼
[SLICE 3 DONE - 93%+ interview ready]

────────────────────────────────────────────────────────────────────────────────
TOTAL TIMELINE (at your current 5/week pace):
  • Phase 1 (gaps):  ~1 week
  • Slice 1:         ~4 weeks   → Interview survivable (70%)
  • Slice 2:         ~3.5 weeks → Strong candidate (85%)
  • Slice 3:         ~2.5 weeks → Excellent (93%+)

TOTAL: ~11 weeks to full preparation

If you sprint (10/week): ~6 weeks total
If you focus (7/week):   ~8 weeks total

================================================================================
```

---

*Last updated: 2025-01-24*
*Companion document: GOOGLE_L6_SLICES.md (interview priorities)*
*Your progress: 26 problems completed, 2-4 gap fillers + 53 slice problems remaining*

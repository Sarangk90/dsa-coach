import json
from pathlib import Path

# Define the learning sequence
PATTERN_SEQUENCE = [
    "hash_map",
    "two_pointers",
    "sliding_window",
    "prefix_sum",
    "stack",
    "linked_list",
    "fast_slow_pointers",
    "binary_search",
    "heap",
    "two_heaps",
    "bfs",
    "dfs",
    "backtracking",
    "merge_intervals",
    "cyclic_sort",
    "topological_sort",
    "union_find",
    "dijkstra",
    "dynamic_programming"
]

# Pattern Metadata updates
PATTERN_METADATA = {
    "hash_map": {
        "title": "Hash Map",
        "description": "Key-value lookups for O(1) access. Essential for counting, caching, and quick checks.",
        "concepts": ["Hash Function", "Collisions", "Counting", "Index Mapping"]
    },
    "two_pointers": {
        "title": "Two Pointers",
        "description": "Two cursors moving through a data structure (usually array/string) to satisfy constraints.",
        "concepts": ["Opposite Ends (Sorted)", "Same Direction (Merge/Remove)", "Partitioning"]
    },
    "sliding_window": {
        "title": "Sliding Window",
        "description": "A window that slides over data to find a subarray satisfying a condition.",
        "concepts": ["Fixed Size", "Variable Size", "Auxiliary Structure", "Shrinking Condition"]
    },
    "prefix_sum": {
        "title": "Prefix Sum",
        "description": "Pre-computing cumulative sums to answer range queries in O(1).",
        "concepts": ["Range Sum", "Running Total", "Subarray Sum Equals K"]
    },
    "stack": {
        "title": "Stack",
        "description": "LIFO (Last-In-First-Out) structure. Good for parsing, nested structures, and backtracking.",
        "concepts": ["LIFO", "Monotonic Stack", "Parentheses Matching", "DFS Helper"]
    },
    "linked_list": {
        "title": "Linked List",
        "description": "Nodes with pointers. Mastery requires pointer manipulation without losing references.",
        "concepts": ["Dummy Node", "Fast/Slow Pointers", "Reversal", "Merge"]
    },
    "fast_slow_pointers": {
        "title": "Fast & Slow Pointers",
        "description": "Cycle detection and finding middle elements in linked lists or arrays.",
        "concepts": ["Cycle Detection (Floyd's)", "Middle Finding", "Happy Number"]
    },
    "binary_search": {
        "title": "Binary Search",
        "description": "O(log N) search on sorted data or search spaces.",
        "concepts": ["Search Space Reduction", "Lower/Upper Bound", "Rotated Arrays", "Answer Range"]
    },
    "heap": {
        "title": "Heap / Priority Queue",
        "description": "O(1) access to min/max element. O(log N) insert/delete.",
        "concepts": ["Min/Max Heap", "Top K Elements", "K-way Merge"]
    },
    "two_heaps": {
        "title": "Two Heaps",
        "description": "Using a Min-Heap and Max-Heap together, often to track median.",
        "concepts": ["Median Finding", "Balancing Heaps"]
    },
    "bfs": {
        "title": "Breadth-First Search",
        "description": "Level-by-level traversal. Best for shortest paths in unweighted graphs.",
        "concepts": ["Queue", "Level Tracking", "Shortest Path", "Connected Components"]
    },
    "dfs": {
        "title": "Depth-First Search",
        "description": "Deep traversal. Best for exhaustive search, tree properties, and backtracking.",
        "concepts": ["Recursion", "Stack", "Path Finding", "Tree Properties"]
    },
    "backtracking": {
        "title": "Backtracking",
        "description": "DFS with state management (Choose-Explore-Unchoose). Generates all possibilities.",
        "concepts": ["Combinations", "Permutations", "Subsets", "Pruning"]
    },
    "merge_intervals": {
        "title": "Merge Intervals",
        "description": "Handling overlapping intervals. Usually requires sorting by start time first.",
        "concepts": ["Sorting", "Overlap Detection", "Merging", "Insertion"]
    },
    "cyclic_sort": {
        "title": "Cyclic Sort",
        "description": "Sorting arrays containing numbers in range 1 to N in O(N) time.",
        "concepts": ["In-place Swap", "Missing Number", "Duplicate Finding"]
    },
    "topological_sort": {
        "title": "Topological Sort",
        "description": "Linear ordering of vertices in a DAG. Used for dependency resolution.",
        "concepts": ["Kahn's Algorithm (BFS)", "DFS Post-order", "Cycle Detection"]
    },
    "union_find": {
        "title": "Union Find (Disjoint Set)",
        "description": "Efficiently tracking connected components and cycles.",
        "concepts": ["Find with Path Compression", "Union by Rank", "Connected Components"]
    },
    "dijkstra": {
        "title": "Dijkstra's Algorithm",
        "description": "Shortest path in weighted graphs.",
        "concepts": ["Priority Queue", "Relaxation", "Shortest Path"]
    },
    "dynamic_programming": {
        "title": "Dynamic Programming",
        "description": "Breaking problems into overlapping subproblems with optimal substructure.",
        "concepts": ["Memoization", "Tabulation", "1D Recurrence", "2D Grid/Sequence"]
    }
}

# New Quests to Add
NEW_QUESTS = [
    # Hash Map
    {
        "id": "contains_duplicate",
        "title": "Contains Duplicate",
        "difficulty": "easy",
        "pattern": "hash_map",
        "link": "https://leetcode.com/problems/contains-duplicate/",
        "xp": 50,
        "type": "code",
        "hints": {
            "low": "Use a hash set to store elements you've seen.",
            "medium": "Iterate through the array. If element is in set, return true. Else add it.",
            "high": "Time O(N), Space O(N)."
        },
        "template": "def contains_duplicate(nums: list[int]) -> bool:\n    # Your code here\n    pass"
    },
    {
        "id": "valid_anagram",
        "title": "Valid Anagram",
        "difficulty": "easy",
        "pattern": "hash_map",
        "link": "https://leetcode.com/problems/valid-anagram/",
        "xp": 50,
        "type": "code",
        "hints": {
            "low": "Count character frequencies for both strings.",
            "medium": "Use a hash map or fixed-size array (26 chars). Increment for s, decrement for t.",
            "high": "If counts match (all zero at end), they are anagrams."
        },
        "template": "def is_anagram(s: str, t: str) -> bool:\n    # Your code here\n    pass"
    },

    # Two Pointers
    {
        "id": "valid_palindrome",
        "title": "Valid Palindrome",
        "difficulty": "easy",
        "pattern": "two_pointers",
        "link": "https://leetcode.com/problems/valid-palindrome/",
        "xp": 50,
        "type": "code",
        "hints": {
            "low": "Use two pointers, one at start, one at end.",
            "medium": "Move inward, skipping non-alphanumeric chars. Compare characters case-insensitively.",
            "high": "If chars mismatch, not a palindrome."
        },
        "template": "def is_palindrome(s: str) -> bool:\n    # Your code here\n    pass"
    },
    {
        "id": "container_with_most_water",
        "title": "Container With Most Water",
        "difficulty": "medium",
        "pattern": "two_pointers",
        "link": "https://leetcode.com/problems/container-with-most-water/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "Area = width * min(height_left, height_right). Start pointers at edges.",
            "medium": "Move the pointer with the SMALLER height to try and find a taller line.",
            "high": "Greedy approach works because width decreases, so we need higher lines."
        },
        "template": "def max_area(height: list[int]) -> int:\n    # Your code here\n    pass"
    },
    {
        "id": "3sum",
        "title": "3Sum",
        "difficulty": "medium",
        "pattern": "two_pointers",
        "link": "https://leetcode.com/problems/3sum/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "Sort the array first. Iterate i, then use 2-sum (sorted) on the rest.",
            "medium": "Fix nums[i], then find pairs (l, r) that sum to -nums[i].",
            "high": "Skip duplicates carefully to avoid repeating triplets."
        },
        "template": "def three_sum(nums: list[int]) -> list[list[int]]:\n    # Your code here\n    pass"
    },

    # Sliding Window
    {
        "id": "best_time_stock",
        "title": "Best Time to Buy and Sell Stock",
        "difficulty": "easy",
        "pattern": "sliding_window",
        "link": "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/",
        "xp": 50,
        "type": "code",
        "hints": {
            "low": "Track the minimum price seen so far.",
            "medium": "Profit = current_price - min_price_so_far.",
            "high": "One pass O(N). Update max_profit at each step."
        },
        "template": "def max_profit(prices: list[int]) -> int:\n    # Your code here\n    pass"
    },
    {
        "id": "longest_repeating_char_replacement",
        "title": "Longest Repeating Character Replacement",
        "difficulty": "medium",
        "pattern": "sliding_window",
        "link": "https://leetcode.com/problems/longest-repeating-character-replacement/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "Valid window: length - max_count <= k. Expand right.",
            "medium": "Track frequency of chars in window. 'max_count' is freq of most common char in window.",
            "high": "If invalid, shrink left. Maximize window size."
        },
        "template": "def character_replacement(s: str, k: int) -> int:\n    # Your code here\n    pass"
    },

    # Stack
    {
        "id": "daily_temperatures",
        "title": "Daily Temperatures",
        "difficulty": "medium",
        "pattern": "stack",
        "link": "https://leetcode.com/problems/daily-temperatures/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "Monotonic decreasing stack. Store indices.",
            "medium": "When current temp > stack top temp, we found a warmer day for stack top.",
            "high": "Pop from stack and calculate difference in indices."
        },
        "template": "def daily_temperatures(temperatures: list[int]) -> list[int]:\n    # Your code here\n    pass"
    },

    # Binary Search
    {
        "id": "find_min_rotated_sorted_array",
        "title": "Find Minimum in Rotated Sorted Array",
        "difficulty": "medium",
        "pattern": "binary_search",
        "link": "https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "Binary search. Compare mid with right neighbor or end.",
            "medium": "If nums[mid] > nums[right], min is to the right.",
            "high": "Otherwise, min is at mid or left."
        },
        "template": "def find_min(nums: list[int]) -> int:\n    # Your code here\n    pass"
    },

    # Cyclic Sort
    {
        "id": "find_duplicate_number",
        "title": "Find the Duplicate Number",
        "difficulty": "medium",
        "pattern": "cyclic_sort",
        "link": "https://leetcode.com/problems/find-the-duplicate-number/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "Treat array values as pointers to indices.",
            "medium": "Use Floyd's Cycle Detection (Fast/Slow pointers) on the array indices.",
            "high": "Or modify array (negate values) if modification allowed."
        },
        "template": "def find_duplicate(nums: list[int]) -> int:\n    # Your code here\n    pass"
    },

    # Two Heaps
    {
        "id": "sliding_window_median",
        "title": "Sliding Window Median",
        "difficulty": "hard",
        "pattern": "two_heaps",
        "link": "https://leetcode.com/problems/sliding-window-median/",
        "xp": 150,
        "type": "code",
        "hints": {
            "low": "Maintain two heaps: max-heap for lower half, min-heap for upper half.",
            "medium": "Balance heaps as window slides. Removing from heap is O(N) or O(log N) with lazy removal.",
            "high": "Lazy removal: keep track of invalid elements in a map."
        },
        "template": "def median_sliding_window(nums: list[int], k: int) -> list[float]:\n    # Your code here\n    pass"
    },

    # BFS
    {
        "id": "word_ladder",
        "title": "Word Ladder",
        "difficulty": "hard",
        "pattern": "bfs",
        "link": "https://leetcode.com/problems/word-ladder/",
        "xp": 150,
        "type": "code",
        "hints": {
            "low": "Shortest path in unweighted graph -> BFS.",
            "medium": "Nodes are words. Edges if words differ by 1 char.",
            "high": "Pre-process words with wildcard pattern for O(1) neighbor lookup."
        },
        "template": "def ladder_length(begin_word: str, end_word: str, word_list: list[str]) -> int:\n    # Your code here\n    pass"
    },

    # DFS
    {
        "id": "diameter_binary_tree",
        "title": "Diameter of Binary Tree",
        "difficulty": "easy",
        "pattern": "dfs",
        "link": "https://leetcode.com/problems/diameter-of-binary-tree/",
        "xp": 50,
        "type": "code",
        "hints": {
            "low": "DFS. For each node, longest path is left_depth + right_depth.",
            "medium": "Return max depth from each recursive call.",
            "high": "Update global maximum diameter at each node."
        },
        "template": "def diameter_of_binary_tree(root: Optional[TreeNode]) -> int:\n    # Your code here\n    pass"
    },
    {
        "id": "path_sum_ii",
        "title": "Path Sum II",
        "difficulty": "medium",
        "pattern": "dfs",
        "link": "https://leetcode.com/problems/path-sum-ii/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "DFS with current path list and current sum.",
            "medium": "At leaf: check if sum == target. Add path to results.",
            "high": "Backtrack: pop from path list after visiting children."
        },
        "template": "def path_sum(root: Optional[TreeNode], target_sum: int) -> list[list[int]]:\n    # Your code here\n    pass"
    },

    # Union Find
    {
        "id": "number_of_provinces",
        "title": "Number of Provinces",
        "difficulty": "medium",
        "pattern": "union_find",
        "link": "https://leetcode.com/problems/number-of-provinces/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "Each city is a node. 'isConnected' is adjacency matrix.",
            "medium": "Union connected cities. Count distinct parents at the end.",
            "high": "Can also use DFS/BFS to count components."
        },
        "template": "def find_circle_num(is_connected: list[list[int]]) -> int:\n    # Your code here\n    pass"
    },
    {
        "id": "redundant_connection",
        "title": "Redundant Connection",
        "difficulty": "medium",
        "pattern": "union_find",
        "link": "https://leetcode.com/problems/redundant-connection/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "Iterate edges. Use Union-Find.",
            "medium": "If two nodes are already in same set (find(u) == find(v)), this edge creates a cycle.",
            "high": "Return the first edge that creates a cycle."
        },
        "template": "def find_redundant_connection(edges: list[list[int]]) -> list[int]:\n    # Your code here\n    pass"
    },

    # Intervals
    {
        "id": "insert_interval",
        "title": "Insert Interval",
        "difficulty": "medium",
        "pattern": "merge_intervals",
        "link": "https://leetcode.com/problems/insert-interval/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "List is sorted. Iterate and add non-overlapping intervals.",
            "medium": "Merge overlapping intervals with the new one: min(start), max(end).",
            "high": "Add remaining intervals after."
        },
        "template": "def insert(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:\n    # Your code here\n    pass"
    },
    
    # Heap
    {
        "id": "k_closest_points",
        "title": "K Closest Points to Origin",
        "difficulty": "medium",
        "pattern": "heap",
        "link": "https://leetcode.com/problems/k-closest-points-to-origin/",
        "xp": 100,
        "type": "code",
        "hints": {
            "low": "Calculate distances. Need K smallest.",
            "medium": "Max-Heap of size K. If new point is smaller than heap top, pop and push.",
            "high": "Or Min-Heap with all points (O(N log N)). Max-heap is O(N log K)."
        },
        "template": "def k_closest(points: list[list[int]], k: int) -> list[list[int]]:\n    # Your code here\n    pass"
    }
]

def hydrate():
    # Load existing
    quests_path = Path("quests.json")
    if not quests_path.exists():
        print("quests.json not found")
        return

    with open(quests_path, "r") as f:
        data = json.load(f)

    # Update metadata
    data["metadata"]["patterns"] = PATTERN_METADATA
    
    # Add sequences for sorting
    pattern_order_map = {p: i for i, p in enumerate(PATTERN_SEQUENCE)}
    difficulty_map = {"easy": 1, "medium": 2, "hard": 3}

    # Merge quests
    existing_quests = {q["id"]: q for q in data.get("quests", [])}
    
    # Add new quests if not exist
    added_count = 0
    for q in NEW_QUESTS:
        if q["id"] not in existing_quests:
            existing_quests[q["id"]] = q
            added_count += 1
        else:
            # Update sequence/metadata for existing if needed?
            # For now, trust existing, or maybe update pattern?
            pass

    final_quests = list(existing_quests.values())

    # Sort
    def sort_key(q):
        p_idx = pattern_order_map.get(q.get("pattern", "mixed"), 999)
        d_idx = difficulty_map.get(q.get("difficulty", "medium"), 2)
        return (p_idx, d_idx, q.get("title", ""))

    final_quests.sort(key=sort_key)

    data["quests"] = final_quests
    data["metadata"]["total_quests"] = len(final_quests)
    data["metadata"]["total_xp"] = sum(q.get("xp", 0) for q in final_quests)
    
    # Save
    with open(quests_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Hydrated quests.json. Added {added_count} new quests. Total: {len(final_quests)}")

if __name__ == "__main__":
    hydrate()




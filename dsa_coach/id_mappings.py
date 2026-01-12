"""
ID Mappings for migrating from cryptic IDs to human-readable IDs.

This module provides mappings from old ft_* IDs to new human-readable slugs.

Naming Conventions:
- Pattern IDs: lower_snake_case, derived from pattern_name (e.g., sliding_window)
- Concept IDs: <pattern_id>_<concept_slug> (e.g., sliding_window_variable_size)
- Problem IDs: <pattern_id>_<problem_slug> (e.g., sliding_window_minimum_window_substring)
"""

# Pattern ID mappings: old_id -> new_id
PATTERN_ID_MAP: dict[str, str] = {
    "ft_01": "big_o_analysis",
    "ft_02": "arrays_hashing",
    "ft_03": "two_pointers",
    "ft_04": "sliding_window",
    "ft_05": "binary_search",
    "ft_06": "recursion",
    "ft_07": "trees",
    "ft_08": "graphs",
    "ft_09": "dynamic_programming",
}

# Concept ID mappings: old_id -> new_id
CONCEPT_ID_MAP: dict[str, str] = {
    # Big-O Analysis (ft_01)
    "ft_01_c1": "big_o_analysis_time_complexity",
    "ft_01_c2": "big_o_analysis_space_complexity",
    "ft_02_c1": "arrays_hashing_hash_map_operations",
    "ft_02_c2": "arrays_hashing_prefix_sum",
    "ft_02_c3": "arrays_hashing_in_place_manipulation",
    # Two Pointers (ft_03)
    "ft_03_c1": "two_pointers_opposite_direction",
    "ft_03_c2": "two_pointers_same_direction",
    # Sliding Window (ft_04)
    "ft_04_c1": "sliding_window_variable_size",
    "ft_04_c2": "sliding_window_fixed_size",
    # Binary Search (ft_05)
    "ft_05_c1": "binary_search_standard",
    "ft_05_c2": "binary_search_answer_space",
    "ft_06_c1": "recursion_basic",
    "ft_06_c2": "recursion_memoization",
    "ft_07_c1": "trees_traversals_dfs",
    "ft_07_c2": "trees_bst_properties",
    "ft_07_c3": "trees_path_problems",
    "ft_07_c4": "trees_level_order_bfs",
    "ft_08_c1": "graphs_dfs_connected_components",
    "ft_08_c2": "graphs_bfs_shortest_paths",
    "ft_08_c3": "graphs_cycle_detection_topological_sort",
    "ft_08_c4": "graphs_union_find",
    # Dynamic Programming (ft_09)
    "ft_09_c1": "dynamic_programming_1d_linear",
    "ft_09_c2": "dynamic_programming_2d_grid",
    "ft_09_c3": "dynamic_programming_knapsack",
}

# Problem ID mappings: old_id -> new_id
PROBLEM_ID_MAP: dict[str, str] = {
    # Arrays & Hashing - Hash Map Operations
    "ft_02_c1_p1": "arrays_hashing_two_sum",
    "ft_02_c1_p2": "arrays_hashing_group_anagrams",
    "ft_02_c1_p3": "arrays_hashing_top_k_frequent_elements",
    # Arrays & Hashing - Prefix Sum
    "ft_02_c2_p1": "arrays_hashing_subarray_sum_equals_k",
    "ft_02_c2_p2": "arrays_hashing_product_of_array_except_self",
    # Arrays & Hashing - In-Place Manipulation
    "ft_02_c3_p1": "arrays_hashing_rotate_image",
    # Two Pointers - Opposite Direction
    "ft_03_c1_p1": "two_pointers_3sum",
    "ft_03_c1_p2": "two_pointers_container_with_most_water",
    # Two Pointers - Same Direction
    "ft_03_c2_p1": "two_pointers_linked_list_cycle",
    "ft_03_c2_p2": "two_pointers_find_duplicate_number",
    # Sliding Window - Variable Size
    "ft_04_c1_p1": "sliding_window_longest_substring_without_repeating",
    "ft_04_c1_p2": "sliding_window_minimum_window_substring",
    # Sliding Window - Fixed Size
    "ft_04_c2_p1": "sliding_window_permutation_in_string",
    # Binary Search - Standard
    "ft_05_c1_p1": "binary_search_basic",
    "ft_05_c1_p2": "binary_search_rotated_sorted_array",
    # Binary Search - Answer Space
    "ft_05_c2_p1": "binary_search_koko_eating_bananas",
    "ft_05_c2_p2": "binary_search_capacity_ship_packages",
    # Recursion - Basic
    "ft_06_c1_p1": "recursion_fibonacci",
    "ft_06_c1_p2": "recursion_climbing_stairs",
    "ft_06_c1_p3": "recursion_power_x_n",
    # Recursion - Memoization
    "ft_06_c2_p1": "recursion_decode_ways",
    "ft_06_c2_p2": "recursion_unique_paths",
    # Trees - Traversals DFS
    "ft_07_c1_p1": "trees_inorder_traversal",
    "ft_07_c1_p2": "trees_maximum_depth",
    # Trees - BST Properties
    "ft_07_c2_p1": "trees_validate_bst",
    "ft_07_c2_p2": "trees_kth_smallest_bst",
    "ft_07_c2_p3": "trees_lowest_common_ancestor_bst",
    # Trees - Path Problems
    "ft_07_c3_p1": "trees_path_sum",
    "ft_07_c3_p2": "trees_max_path_sum",
    # Trees - Level Order BFS
    "ft_07_c4_p1": "trees_level_order_traversal",
    "ft_07_c4_p2": "trees_right_side_view",
    # Graphs - DFS Connected Components
    "ft_08_c1_p1": "graphs_number_of_islands",
    "ft_08_c1_p2": "graphs_clone_graph",
    # Graphs - BFS Shortest Paths
    "ft_08_c2_p1": "graphs_rotting_oranges",
    "ft_08_c2_p2": "graphs_01_matrix",
    # Graphs - Cycle Detection & Topological Sort
    "ft_08_c3_p1": "graphs_course_schedule",
    "ft_08_c3_p2": "graphs_course_schedule_ii",
    # Graphs - Union Find
    "ft_08_c4_p1": "graphs_number_of_provinces",
    "ft_08_c4_p2": "graphs_redundant_connection",
    # Dynamic Programming - 1D Linear
    "ft_09_c1_p1": "dynamic_programming_house_robber",
    "ft_09_c1_p2": "dynamic_programming_longest_increasing_subsequence",
    # Dynamic Programming - 2D Grid
    "ft_09_c2_p1": "dynamic_programming_unique_paths",
    "ft_09_c2_p2": "dynamic_programming_minimum_path_sum",
    # Dynamic Programming - Knapsack
    "ft_09_c3_p1": "dynamic_programming_coin_change",
    "ft_09_c3_p2": "dynamic_programming_partition_equal_subset_sum",
    "ft_09_c3_p3": "dynamic_programming_target_sum",
}

# Reverse mappings for lookup
PATTERN_ID_REVERSE_MAP: dict[str, str] = {v: k for k, v in PATTERN_ID_MAP.items()}
CONCEPT_ID_REVERSE_MAP: dict[str, str] = {v: k for k, v in CONCEPT_ID_MAP.items()}
PROBLEM_ID_REVERSE_MAP: dict[str, str] = {v: k for k, v in PROBLEM_ID_MAP.items()}


def get_new_pattern_id(old_id: str) -> str:
    """Convert old pattern ID to new human-readable ID."""
    return PATTERN_ID_MAP.get(old_id, old_id)


def get_new_concept_id(old_id: str) -> str:
    """Convert old concept ID to new human-readable ID."""
    return CONCEPT_ID_MAP.get(old_id, old_id)


def get_new_problem_id(old_id: str) -> str:
    """Convert old problem ID to new human-readable ID."""
    return PROBLEM_ID_MAP.get(old_id, old_id)


def is_old_format_id(id_str: str) -> bool:
    """Check if an ID is in the old ft_* format."""
    return id_str.startswith("ft_")

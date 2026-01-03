from dsa_coach import solution


def test_create_solution_file(mock_workspace):
    quest = {
        "problem_id": "test_quest",
        "problem_name": "Test Quest",
        "pattern_name": "Sliding Window",
        "difficulty": "easy",
        "url": "http://example.com",
        "template": "# Code here",
    }

    filepath = solution.create_solution_file(quest)

    assert filepath.exists()
    assert filepath.name == "test_quest.py"
    assert "sliding_window" in str(filepath)

    content = filepath.read_text()
    assert "# Code here" in content
    assert "Quest: Test Quest" in content


def test_create_solution_file_no_template(mock_workspace):
    quest = {
        "problem_id": "test_quest_2",
        "problem_name": "Test Quest 2",
        "pattern_name": "Arrays",
    }

    filepath = solution.create_solution_file(quest)

    content = filepath.read_text()
    assert "# Your solution here" in content

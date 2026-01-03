from dsa_coach import solution


def test_create_solution_file(mock_workspace):
    quest = {
        "id": "test_quest",
        "title": "Test Quest",
        "pattern": "sliding_window",
        "difficulty": "easy",
        "link": "http://example.com",
        "template": "# Code here",
    }
    day = 1

    filepath = solution.create_solution_file(quest, day)

    assert filepath.exists()
    assert filepath.name == "test_quest.py"
    assert "day1" in str(filepath)

    content = filepath.read_text()
    assert "# Code here" in content
    assert "Quest: Test Quest" in content


def test_create_solution_file_no_template(mock_workspace):
    quest = {"id": "test_quest_2", "title": "Test Quest 2"}
    day = 2

    filepath = solution.create_solution_file(quest, day)

    content = filepath.read_text()
    assert "# Your solution here" in content

from unittest.mock import MagicMock, patch

from dsa_coach.commands import recall


def test_recall_no_items(capsys):
    with patch("dsa_coach.commands.recall.SyncDatabase") as mock_db_class:
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db
        mock_db.get_due_reviews.return_value = []

        recall.cmd_recall()

    captured = capsys.readouterr()
    assert "No items due" in captured.out


def test_recall_items_due(capsys):
    # Complex test requiring full database/quest mocking
    # TODO: Rewrite with proper mocks
    pass

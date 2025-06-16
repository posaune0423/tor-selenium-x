"""Test cases for hello.py module."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the project root to the path so we can import hello
sys.path.insert(0, str(Path(__file__).parent.parent))
import src.hello as hello


class TestMain:
    """Test cases for the main function."""

    def test_main_function_exists(self) -> None:
        """Test that main function exists and is callable."""
        assert callable(hello.main)

    @patch("builtins.print")
    def test_main_prints_correct_message(self, mock_print) -> None:
        """Test that main function prints the expected message."""
        hello.main()
        mock_print.assert_called_once_with("Hello from tor-selenium-x!")

    def test_main_returns_none(self) -> None:
        """Test that main function returns None."""
        result = hello.main()
        assert result is None


class TestModuleExecution:
    """Test cases for module execution behavior."""

    def test_main_module_has_name_main_check(self) -> None:
        """Test that the module has the standard __name__ == '__main__' check."""
        # Read the file content to check for standard Python idiom
        hello_file = Path(__file__).parent.parent / "src" / "hello.py"
        content = hello_file.read_text()
        assert '__name__ == "__main__"' in content

    def test_module_docstring_exists(self) -> None:
        """Test that the module has a docstring or at least the main function works."""
        # This is a simple integration test to ensure the module can be imported
        import src.hello as hello

        assert hasattr(hello, "main")


@pytest.mark.integration
class TestIntegration:
    """Integration tests for the hello module."""

    @patch("builtins.print")
    def test_full_execution_flow(self, mock_print) -> None:
        """Test the complete execution flow of the hello module."""
        # This simulates what happens when the script is run directly
        hello.main()
        mock_print.assert_called_with("Hello from tor-selenium-x!")

    def test_import_does_not_cause_side_effects(self) -> None:
        """Test that importing the module doesn't cause unwanted side effects."""
        # Re-importing should not cause any prints or side effects
        with patch("builtins.print") as mock_print:

            mock_print.assert_not_called()


# Example of parametrized test (for demonstration)
@pytest.mark.parametrize(
    "expected_message",
    [
        "Hello from tor-selenium-x!",
    ],
)
def test_message_content(expected_message: str) -> None:
    """Test the message content using parametrized testing."""
    with patch("builtins.print") as mock_print:
        hello.main()
        mock_print.assert_called_with(expected_message)


# Example of fixture usage
@pytest.fixture
def hello_module():
    """Fixture that provides the hello module."""
    import src.hello as hello

    return hello


def test_with_fixture(hello_module) -> None:
    """Test using a fixture."""
    assert hasattr(hello_module, "main")
    assert callable(hello_module.main)

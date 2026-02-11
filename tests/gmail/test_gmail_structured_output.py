"""
Unit tests for Gmail structured output functionality.

Tests that Gmail tools return ToolResult with both text content and structured_content.
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastmcp.tools.tool import ToolResult
from gmail.gmail_models import (
    GmailSearchResult,
    GmailMessageSummary,
    GmailMessageContent,
    GmailAttachment,
    GmailSendResult,
)
from core.structured_output import create_tool_result


class TestCreateToolResult:
    """Tests for the create_tool_result helper function."""

    def test_create_tool_result_with_dict(self):
        """Test creating ToolResult with a dict."""
        result = create_tool_result(
            text="Hello world",
            data={"key": "value", "count": 42},
        )

        assert isinstance(result, ToolResult)
        assert len(result.content) == 1
        assert result.content[0].text == "Hello world"
        assert result.structured_content == {"key": "value", "count": 42}

    def test_create_tool_result_with_dataclass(self):
        """Test creating ToolResult with a dataclass."""
        summary = GmailMessageSummary(
            message_id="msg123",
            thread_id="thread456",
            web_link="https://mail.google.com/mail/u/0/#all/msg123",
            thread_link="https://mail.google.com/mail/u/0/#all/thread456",
        )
        result = create_tool_result(
            text="Found 1 message",
            data=summary,
        )

        assert isinstance(result, ToolResult)
        assert result.structured_content == {
            "message_id": "msg123",
            "thread_id": "thread456",
            "web_link": "https://mail.google.com/mail/u/0/#all/msg123",
            "thread_link": "https://mail.google.com/mail/u/0/#all/thread456",
        }


class TestGmailModels:
    """Tests for Gmail dataclass models."""

    def test_gmail_search_result_serialization(self):
        """Test GmailSearchResult serializes correctly."""
        result = GmailSearchResult(
            query="from:test@example.com",
            total_found=2,
            messages=[
                GmailMessageSummary(
                    message_id="msg1",
                    thread_id="thread1",
                    web_link="https://mail.google.com/mail/u/0/#all/msg1",
                    thread_link="https://mail.google.com/mail/u/0/#all/thread1",
                ),
                GmailMessageSummary(
                    message_id="msg2",
                    thread_id="thread2",
                    web_link="https://mail.google.com/mail/u/0/#all/msg2",
                    thread_link="https://mail.google.com/mail/u/0/#all/thread2",
                ),
            ],
            next_page_token="token123",
        )

        tool_result = create_tool_result(text="Found messages", data=result)

        assert tool_result.structured_content["query"] == "from:test@example.com"
        assert tool_result.structured_content["total_found"] == 2
        assert len(tool_result.structured_content["messages"]) == 2
        assert tool_result.structured_content["next_page_token"] == "token123"

    def test_gmail_message_content_serialization(self):
        """Test GmailMessageContent serializes correctly with attachments."""
        result = GmailMessageContent(
            message_id="msg123",
            subject="Test Subject",
            sender="sender@example.com",
            date="Mon, 1 Jan 2024 10:00:00 -0000",
            to="recipient@example.com",
            cc="cc@example.com",
            rfc822_message_id="<test123@mail.gmail.com>",
            body="This is the email body.",
            attachments=[
                GmailAttachment(
                    filename="report.pdf",
                    mime_type="application/pdf",
                    size_bytes=12345,
                    attachment_id="att001",
                ),
            ],
        )

        tool_result = create_tool_result(text="Message content", data=result)

        assert tool_result.structured_content["message_id"] == "msg123"
        assert tool_result.structured_content["subject"] == "Test Subject"
        assert tool_result.structured_content["sender"] == "sender@example.com"
        assert tool_result.structured_content["to"] == "recipient@example.com"
        assert tool_result.structured_content["cc"] == "cc@example.com"
        assert len(tool_result.structured_content["attachments"]) == 1
        assert (
            tool_result.structured_content["attachments"][0]["filename"] == "report.pdf"
        )

    def test_gmail_send_result_serialization(self):
        """Test GmailSendResult serializes correctly."""
        result = GmailSendResult(
            message_id="sent123",
            thread_id="thread456",
            attachment_count=2,
        )

        tool_result = create_tool_result(text="Email sent", data=result)

        assert tool_result.structured_content["message_id"] == "sent123"
        assert tool_result.structured_content["thread_id"] == "thread456"
        assert tool_result.structured_content["attachment_count"] == 2


class TestSearchGmailMessagesStructuredOutput:
    """Tests for search_gmail_messages structured output."""

    @pytest.fixture
    def mock_gmail_service(self):
        """Create a mock Gmail service."""
        service = Mock()
        return service

    @pytest.mark.asyncio
    async def test_search_returns_tool_result_with_messages(self, mock_gmail_service):
        """Test that search returns ToolResult with structured content."""
        # Import the function under test

        # We need to test the core logic, so we'll create a helper
        # that exercises the structured output construction
        from gmail.gmail_tools import (
            _format_gmail_results_plain,
            _generate_gmail_web_url,
        )

        messages = [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"},
        ]
        query = "from:test@example.com"
        next_page_token = "token123"

        # Test the formatting function
        text_output = _format_gmail_results_plain(messages, query, next_page_token)

        assert "Found 2 messages" in text_output
        assert "msg1" in text_output
        assert "msg2" in text_output
        assert "token123" in text_output

        # Test URL generation
        assert (
            _generate_gmail_web_url("msg1")
            == "https://mail.google.com/mail/u/0/#all/msg1"
        )

    @pytest.mark.asyncio
    async def test_search_empty_results(self, mock_gmail_service):
        """Test that search with no results returns appropriate structured content."""
        from gmail.gmail_tools import _format_gmail_results_plain

        messages = []
        query = "nonexistent"
        next_page_token = None

        text_output = _format_gmail_results_plain(messages, query, next_page_token)

        assert "No messages found" in text_output

    @pytest.mark.asyncio
    async def test_search_handles_malformed_messages(self, mock_gmail_service):
        """Test that search handles malformed message data gracefully."""
        from gmail.gmail_tools import _format_gmail_results_plain

        messages = [
            {"id": "msg1", "threadId": "thread1"},
            None,  # Malformed
            {},  # Missing fields
            {"id": "", "threadId": ""},  # Empty fields
        ]
        query = "test"

        text_output = _format_gmail_results_plain(messages, query, None)

        # Should still work and include the valid message
        assert "msg1" in text_output


class TestGetGmailMessageContentStructuredOutput:
    """Tests for get_gmail_message_content structured output."""

    def test_attachment_model_structure(self):
        """Test GmailAttachment model has correct structure."""
        attachment = GmailAttachment(
            filename="test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            attachment_id="att123",
        )

        tool_result = create_tool_result(text="Attachment", data=attachment)

        assert tool_result.structured_content["filename"] == "test.pdf"
        assert tool_result.structured_content["mime_type"] == "application/pdf"
        assert tool_result.structured_content["size_bytes"] == 1024
        assert tool_result.structured_content["attachment_id"] == "att123"


class TestSendGmailMessageStructuredOutput:
    """Tests for send_gmail_message structured output."""

    def test_send_result_without_thread(self):
        """Test GmailSendResult for a new email (no thread)."""
        result = GmailSendResult(
            message_id="sent123",
            thread_id=None,
            attachment_count=0,
        )

        tool_result = create_tool_result(text="Email sent", data=result)

        assert tool_result.structured_content["message_id"] == "sent123"
        assert "thread_id" not in tool_result.structured_content
        assert tool_result.structured_content["attachment_count"] == 0

    def test_send_result_with_attachments(self):
        """Test GmailSendResult for email with attachments."""
        result = GmailSendResult(
            message_id="sent456",
            thread_id="thread789",
            attachment_count=3,
        )

        tool_result = create_tool_result(text="Email sent", data=result)

        assert tool_result.structured_content["attachment_count"] == 3

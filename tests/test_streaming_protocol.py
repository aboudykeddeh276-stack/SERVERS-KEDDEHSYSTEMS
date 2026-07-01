"""Tests for the Total Metric Value Streaming Protocol."""

import pytest

from keddeh_matrix.streaming_protocol import (
    TotalMetricValueStreamingProtocol,
    LiteralStateValue,
    MemoryRegistryError,
)


class TestLiteralStateValue:
    """Test literal state value properties."""

    def test_stores_full_content(self):
        val = LiteralStateValue(content="hello world", registry_key="test_key")
        assert val.content == "hello world"
        assert val.character_count == 11

    def test_integrity_verification_passes(self):
        val = LiteralStateValue(content="data", registry_key="k1")
        assert val.verify_integrity() is True

    def test_empty_key_rejected(self):
        with pytest.raises(MemoryRegistryError):
            LiteralStateValue(content="data", registry_key="")


class TestTotalMetricValueStreamingProtocol:
    """Test the streaming protocol."""

    def test_allocate_and_read(self):
        proto = TotalMetricValueStreamingProtocol()
        proto.allocate("reg_1", "literal content here")
        entry = proto.read("reg_1")
        assert entry.content == "literal content here"
        assert entry.character_count == 20

    def test_duplicate_allocation_rejected(self):
        proto = TotalMetricValueStreamingProtocol()
        proto.allocate("reg_1", "data")
        with pytest.raises(MemoryRegistryError, match="already allocated"):
            proto.allocate("reg_1", "other data")

    def test_read_nonexistent_key(self):
        proto = TotalMetricValueStreamingProtocol()
        with pytest.raises(MemoryRegistryError, match="not found"):
            proto.read("missing")

    def test_total_literal_characters(self):
        proto = TotalMetricValueStreamingProtocol()
        proto.allocate("a", "hello")  # 5 chars
        proto.allocate("b", "world!!")  # 7 chars
        assert proto.total_literal_characters() == 12

    def test_sequence_starts_at_singular_origin(self):
        proto = TotalMetricValueStreamingProtocol()
        assert proto.sequence_position == 1  # Singular Origin

    def test_verify_all(self):
        proto = TotalMetricValueStreamingProtocol()
        proto.allocate("x", "test")
        proto.allocate("y", "data")
        result = proto.verify_all()
        assert result == {"x": True, "y": True}

    def test_list_keys(self):
        proto = TotalMetricValueStreamingProtocol()
        proto.allocate("alpha", "a")
        proto.allocate("beta", "b")
        assert set(proto.list_keys()) == {"alpha", "beta"}

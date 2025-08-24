"""Additional tests for ReportSink coverage gaps."""

import pytest

from ovmobilebench.report.sink import ReportSink


class TestReportSinkAdditional:
    """Test remaining gaps in ReportSink."""

    def test_abstract_write_method(self):
        """Test that ReportSink cannot be instantiated without implementing write."""

        # Try to create a class without implementing the abstract method
        class MinimalSink(ReportSink):
            pass

        # Should not be able to instantiate without implementing abstract method
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            MinimalSink()

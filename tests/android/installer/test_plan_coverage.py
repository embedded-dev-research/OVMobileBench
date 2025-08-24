"""Additional tests for Planner coverage gaps."""

from pathlib import Path

import pytest

from ovmobilebench.android.installer.plan import Planner


class TestPlannerAdditional:
    """Test remaining gaps in Planner."""

    def test_validate_dry_run_with_invalid_config(self):
        """Test dry run validation with invalid configuration."""
        planner = Planner(Path("/test/sdk"))

        # Test invalid API level by trying to build a plan with invalid parameters
        from ovmobilebench.android.installer.errors import InvalidArgumentError
        from ovmobilebench.android.installer.types import NdkSpec

        with pytest.raises(InvalidArgumentError, match="API level"):
            planner.build_plan(
                api=15,
                target="google_apis",
                arch="arm64-v8a",
                install_platform_tools=True,
                install_emulator=True,
                ndk=NdkSpec(alias="r26d"),
            )

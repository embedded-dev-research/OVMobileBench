"""Tests to improve schema coverage to 100%."""

from ovmobilebench.config.schema import DeviceConfig


def test_device_type_to_kind_migration():
    """Test that 'type' field is migrated to 'kind'."""
    # Test when only 'type' is provided (this covers line 118)
    device = DeviceConfig(type="android", serials=["test"])
    assert device.kind == "android"
    assert device.type == "android"

    # Test when only 'kind' is provided (this covers line 120)
    device2 = DeviceConfig(kind="linux_ssh", serials=["test"])
    assert device2.kind == "linux_ssh"
    assert device2.type == "linux_ssh"

    # Test when both are provided (neither branch taken)
    device3 = DeviceConfig(kind="android", type="linux_ssh", serials=["test"])
    assert device3.kind == "android"
    assert device3.type == "linux_ssh"

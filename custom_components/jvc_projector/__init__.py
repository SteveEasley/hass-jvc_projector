"""The jvc_projector integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from jvcprojector import JvcProjector, JvcProjectorAuthError, JvcProjectorConnectError

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import JvcProjectorDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS = [Platform.REMOTE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up integration from a config entry."""
    device = JvcProjector(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        password=entry.data[CONF_PASSWORD],
    )

    try:
        await device.connect(True)
    except JvcProjectorConnectError as err:
        raise ConfigEntryNotReady(
            f"Unable to connect to {entry.data[CONF_HOST]}"
        ) from err
    except JvcProjectorAuthError as err:
        raise ConfigEntryAuthFailed("Password authentication failed") from err

    coordinator = JvcProjectorDataUpdateCoordinator(hass, device)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def disconnect(event: Event) -> None:
        await device.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, disconnect)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await hass.data[DOMAIN][entry.entry_id].device.disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def get_mac_address(host: str, port: int, password: str | None) -> str:
    """Get device mac address for config flow."""
    device = JvcProjector(host, port=port, password=password)
    try:
        await device.connect(True)
    finally:
        await device.disconnect()
    return device.mac

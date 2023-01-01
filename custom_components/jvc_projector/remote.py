"""Remote platform for the jvc_projector integration."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
import logging
from typing import Any

from jvcprojector import const
import voluptuous as vol

from homeassistant.components.remote import RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_COMMAND
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)

from .const import DOMAIN
from .coordinator import JvcProjectorDataUpdateCoordinator
from .entity import JvcProjectorEntity

COMMANDS = {
    "menu": const.REMOTE_MENU,
    "up": const.REMOTE_UP,
    "down": const.REMOTE_DOWN,
    "left": const.REMOTE_LEFT,
    "right": const.REMOTE_RIGHT,
    "ok": const.REMOTE_OK,
    "back": const.REMOTE_BACK,
    "mpc": const.REMOTE_MPC,
    "hide": const.REMOTE_HIDE,
    "info": const.REMOTE_INFO,
    "input": const.REMOTE_INPUT,
    "cmd": const.REMOTE_CMD,
    "advanced_menu": const.REMOTE_ADVANCED_MENU,
    "picture_mode": const.REMOTE_PICTURE_MODE,
    "color_profile": const.REMOTE_COLOR_PROFILE,
    "lens_control": const.REMOTE_LENS_CONTROL,
    "setting_memory": const.REMOTE_SETTING_MEMORY,
    "gamma_settings": const.REMOTE_GAMMA_SETTINGS,
}

ON_STATES = [const.ON, const.WARMING]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the JVC Projector platform from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entity = JvcProjectorRemote(coordinator)
    async_add_entities([entity], True)

    platform = async_get_current_platform()

    platform.async_register_entity_service(
        "send_command",
        {vol.Required(ATTR_COMMAND): cv.string},
        "async_send_operation_command",
    )


class JvcProjectorRemote(JvcProjectorEntity, RemoteEntity):
    """Representation of a JVC Projector device."""

    def __init__(self, coordinator: JvcProjectorDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_is_on = coordinator.data[const.POWER] in ON_STATES

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        await self.device.power_on()
        await asyncio.sleep(1)
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self.device.power_off()
        await asyncio.sleep(1)
        await self.coordinator.async_refresh()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a remote control command to the device."""
        for cmd in command:
            if cmd not in COMMANDS:
                raise HomeAssistantError(f"{cmd} is not a known command")
            await self.async_send_operation_command(f"RC{COMMANDS[cmd]}")

    async def async_send_operation_command(self, command: str) -> None:
        """Send a raw operation command to the device."""
        _LOGGER.debug("Sending command '%s'", command)
        await self.device.op(command)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data[const.POWER] in ON_STATES
        super()._handle_coordinator_update()

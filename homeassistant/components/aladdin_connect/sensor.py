"""Support for Aladdin Connect Garage Door sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from genie_partner_sdk.client import AladdinConnectClient

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import api
from .const import DOMAIN
from .model import GarageDoor


@dataclass(frozen=True, kw_only=True)
class AccSensorEntityDescription(SensorEntityDescription):
    """Describes AladdinConnect sensor entity."""

    value_fn: Callable


SENSORS: tuple[AccSensorEntityDescription, ...] = (
    AccSensorEntityDescription(
        key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=AladdinConnectClient.get_battery_status,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aladdin Connect sensor devices."""

    session: api.AsyncConfigEntryAuth = hass.data[DOMAIN][entry.entry_id]
    acc = AladdinConnectClient(session)

    entities = []
    doors = await acc.get_doors()

    for door in doors:
        entities.extend(
            [AladdinConnectSensor(acc, door, description) for description in SENSORS]
        )

    async_add_entities(entities)


class AladdinConnectSensor(SensorEntity):
    """A sensor implementation for Aladdin Connect devices."""

    entity_description: AccSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        acc: AladdinConnectClient,
        device: GarageDoor,
        description: AccSensorEntityDescription,
    ) -> None:
        """Initialize a sensor for an Aladdin Connect device."""
        self._device_id = device.device_id
        self._number = device.door_number
        self._acc = acc
        self.entity_description = description
        self._attr_unique_id = f"{device.unique_id}-{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.unique_id)},
            name=device.name,
            manufacturer="Overhead Door",
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return cast(
            float,
            self.entity_description.value_fn(self._acc, self._device_id, self._number),
        )

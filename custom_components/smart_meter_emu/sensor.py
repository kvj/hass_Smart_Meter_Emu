from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from homeassistant.const import (
    EntityCategory,
)
from homeassistant.components import sensor

import logging

from .constants import DOMAIN
from .coordinator import Coordinator, BaseEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, add_entities):
    coordinator = entry.runtime_data
    add_entities([_LastConnect(coordinator), _TotalPower(coordinator)])
    return True


class _LastConnect(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)
        self.with_name("last_connect", "Last Connected")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = sensor.SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        return self.coordinator.data.get("last_connect")
    
class _TotalPower(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)
        self.with_name("total_power", "Total Power")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_state_class = sensor.SensorStateClass.MEASUREMENT
        self._attr_device_class = sensor.SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = "W"

    @property
    def native_value(self):
        return self.coordinator.data.get("total_power")
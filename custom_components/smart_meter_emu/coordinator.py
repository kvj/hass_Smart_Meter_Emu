from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from homeassistant.util import dt
from homeassistant.config_entries import ConfigEntry

from homeassistant.const import (
    CONF_NAME,
)

from anyio import create_udp_socket
import socket

from .constants import *

import logging
import json

_LOGGER = logging.getLogger(__name__)

class _Emulator():

    def __init__(self, get_callback, on_connect_callback):
        self._get_callback = get_callback
        self._on_connect_callback = on_connect_callback

    def create_device_id(self, device_type: str, device_id: str):
        self._device_id = f"{device_type}-{device_id.lower()}"

    async def async_run(self):
        try:
            await self._async_do()
        except:
            _LOGGER.exception(f"async_run:")
    
    async def _async_do(self):
        pass

class _UdpEmulator(_Emulator):

    def __init__(self, get_callback, on_connect_callback, port: int):
        super().__init__(get_callback, on_connect_callback)
        self._port = port

    async def _async_do(self):
        _LOGGER.info(f"_async_do: creating UDP socket on port {self._port}")
        async with await create_udp_socket(family=socket.AF_INET, local_port=self._port, local_host="0.0.0.0") as udp:
            _LOGGER.debug(f"_async_do: created UDP socket: {udp}")
            async for packet, (host, port) in udp:
                _LOGGER.debug(f"_async_do: new UDP connection: from {host}:{port} with data {packet}")
                result = await self._async_handle(packet, host, port)
                _LOGGER.debug(f"_async_do: UDP response: {result}")
                if result:
                    await udp.sendto(result, host, port)

    async def _async_handle(self, data: bytes, host: str, port: int) -> bytes | None:
        return None

class _ShellyEmulator(_UdpEmulator):

    def __init__(self, get_callback, on_connect_callback, port: int):
        super().__init__(get_callback, on_connect_callback, port)

    def _prepare_em_response(self, id):
        if powers := self._get_callback():
            return {
                "id": id,
                "src": self._device_id,
                "dst": "unknown",
                "result": {
                    "a_act_power": powers[1],
                    "b_act_power": powers[2],
                    "c_act_power": powers[3],
                    "total_act_power": powers[0],
                },
            }
        return None
    
    def _prepare_em1_response(self, id):
        if powers := self._get_callback():
            return {
                "id": id,
                "src": self._device_id,
                "dst": "unknown",
                "result": {
                    "act_power": powers[0],
                },
            }
        return None

    async def _async_handle(self, data: bytes, host, port) -> bytes | None:
        _LOGGER.debug(f"_async_handle: [shelly] incoming packet: {data}")
        try:
            request = json.loads(data)
            _LOGGER.debug(f"_async_handle: [shelly] incoming json: {request}")
            if isinstance(request.get("params", {}).get("id"), int):
                method = request.get("method")
                self._on_connect_callback()
                response = None
                if method == "EM.GetStatus":
                    response = self._prepare_em_response(request.get("id"))
                elif method == "EM1.GetStatus":
                    response = self._prepare_em1_response(request.get("id"))
                else:
                    _LOGGER.exception(f"_async_handle: [shelly] unknown method: {method}")
                if response != None:
                    _LOGGER.debug(f"_async_handle: [shelly] response: {response}")
                    return json.dumps(response, separators=(",", ":")).encode()
        except:
            _LOGGER.exception(f"_async_handle: [shelly] error handing packet")
        return None


class Coordinator(DataUpdateCoordinator):

    def __init__(self, hass, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            setup_method=self._async_setup,
            update_method=self._async_update,
        )
        self._entry = entry
        self._entry_id = entry.entry_id
        self._emulator_task = None
        
    async def _async_setup(self):
        self._config = self._entry.as_dict()["options"]
        self.data = {
        }

    async def _async_update(self):
        return self.data

    def _update_state(self, data: dict):
        _LOGGER.debug(f"_update_state: new state: {data}")
        self.async_set_updated_data({
            **self.data,
            **data,
        })

    def _get_sensor_state(self, entity_id: str) -> int | None:
        if state := self.hass.states.get(entity_id):
            # _LOGGER.debug(f"_get_sensor_state: {entity_id} = {state}, {type(state.state)}")
            try:
              return float(state.state)
            except:
                return None
        return None
    
    def _get_power_values(self):
        shift = self._config.get(CONF_SHIFT, 0)
        if CONF_POWER_ENTITY_ID in self._config:
            _LOGGER.debug(f"_get_power_values: {self._get_sensor_state(self._config[CONF_POWER_ENTITY_ID])}")
            if (total := self._get_sensor_state(self._config[CONF_POWER_ENTITY_ID])) != None:
                total = total + shift
                ab = round(total / 3)
                c = round(total) - 2 * ab
                self._update_state({
                    "total_power": round(total),
                })
                return (round(total), ab, ab, c)
            return None
        a = self._get_sensor_state(self._config[CONF_POWER_P1_ENTITY_ID])
        b = self._get_sensor_state(self._config[CONF_POWER_P2_ENTITY_ID])
        c = self._get_sensor_state(self._config[CONF_POWER_P3_ENTITY_ID])
        if a != None and b != None and c != None:
            s3 = shift / 3
            a = round(a + s3)
            b = round(b + s3)
            c = round(c + s3)
            self._update_state({
                "total_power": a + b + c,
            })
            return (a + b + c, a, b, c)
        return None
    
    def _on_connect(self):
        _LOGGER.debug(f"_on_connect:")
        self._update_state({
            "last_connect": dt.now(),
        })

    async def async_load(self):
        self._config = self._entry.as_dict()["options"]
        _LOGGER.debug(f"async_load: {self._config}")
        port = self._config.get(CONF_PORT, UDP_PORT_MAP.get(self._config.get(CONF_TYPE)))
        self._emulator = _ShellyEmulator(self._get_power_values, self._on_connect, port)
        self._emulator.create_device_id(self._config.get(CONF_TYPE), self._entry_id)
        self._emulator_task = self._entry.async_create_background_task(self.hass, self._emulator.async_run(), "emulator", eager_start=False)

    async def async_unload(self):
        _LOGGER.debug(f"async_unload: {self._emulator_task}")
        if self._emulator_task:
            self._emulator_task.cancel("async_unload")
            self._emulator_task = None

    @property
    def entity_name(self):
        return self._config[CONF_NAME]

class BaseEntity(CoordinatorEntity[Coordinator]):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    def with_name(self, suffix: str, name: str):
        self._attr_has_entity_name = True
        entry_id = self.coordinator._entry_id
        self._attr_unique_id = f"_{DOMAIN}_{entry_id}_{suffix}"
        self._attr_name = name
        return self

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("config_entry", self.coordinator._entry_id)
            },
            "name": self.coordinator.entity_name,
        }

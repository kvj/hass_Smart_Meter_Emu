from collections.abc import Mapping
from typing import Any, cast

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector

from homeassistant.const import (
    CONF_NAME,
)

from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
    SchemaFlowError,
)

from .constants import *

import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

EMU_TYPES = [
    {"value": EMU_S_P3EM, "label": "Shelly Pro 3EM"},
    {"value": EMU_S_EM3G, "label": "Shelly EM Gen3"},
    {"value": EMU_S_PEM50, "label": "Shelly Pro EM 50"},
]

OPTIONS_SCHEMA = vol.Schema({
    vol.Required(CONF_TYPE, description={}, default=EMU_S_P3EM): selector({"select": {"options": EMU_TYPES, "mode": "list"}}),
    vol.Optional(CONF_POWER_ENTITY_ID, description={}): selector({"entity": {"filter": {"domain": "sensor", "device_class": "power"}}}),
    vol.Optional(CONF_POWER_P1_ENTITY_ID, description={}): selector({"entity": {"filter": {"domain": "sensor", "device_class": "power"}}}),
    vol.Optional(CONF_POWER_P2_ENTITY_ID, description={}): selector({"entity": {"filter": {"domain": "sensor", "device_class": "power"}}}),
    vol.Optional(CONF_POWER_P3_ENTITY_ID, description={}): selector({"entity": {"filter": {"domain": "sensor", "device_class": "power"}}}),
    vol.Optional(CONF_PORT, description={}): selector({"number": {"min": 0, "max": 65535, "step": 1, "mode": "box"}}),
    vol.Optional(CONF_SHIFT, description={"suggested_value": 0}): selector({"number": 
        {"min": -10000, "max": 10000, "step": 1, "mode": "box", "unit_of_measurement": "W"},
    }),
})

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): selector({"text": {}}),
}).extend(OPTIONS_SCHEMA.schema)

async def _validate_options(step, user_input):
    _LOGGER.debug(f"_validate_options: {user_input}, {step}, {step.options}")
    if CONF_POWER_ENTITY_ID in user_input:
        for key in CONF_P_ENTITY_IDS:
            if user_input.get(key):
                raise SchemaFlowError("only_power_entity")
    else:
        for key in CONF_P_ENTITY_IDS:
            if not user_input.get(key):
                raise SchemaFlowError("all_phase_entities")
    return user_input

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(CONFIG_SCHEMA, _validate_options),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA, _validate_options),
}

class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        return cast(str, options[CONF_NAME])

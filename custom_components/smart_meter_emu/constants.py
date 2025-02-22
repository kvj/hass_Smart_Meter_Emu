DOMAIN = "smart_meter_emu"
PLATFORMS = ["sensor"]

CONF_POWER_ENTITY_ID = "power_entity_id"
CONF_POWER_P1_ENTITY_ID = "p1_entity_id"
CONF_POWER_P2_ENTITY_ID = "p2_entity_id"
CONF_POWER_P3_ENTITY_ID = "p3_entity_id"

CONF_P_ENTITY_IDS = (CONF_POWER_P1_ENTITY_ID, CONF_POWER_P2_ENTITY_ID, CONF_POWER_P3_ENTITY_ID)

CONF_TYPE = "type"
CONF_PORT = "port"
CONF_SHIFT = "shift"

EMU_S_P3EM = "shellypro3em"
EMU_S_EM3G = "shellyemg3"
EMU_S_PEM50 = "shellyproem50"

UDP_PORT_MAP = {
    EMU_S_P3EM: 1010,
    EMU_S_EM3G: 2222,
    EMU_S_PEM50: 2223,
}

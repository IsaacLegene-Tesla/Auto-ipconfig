"""Shared parse/apply logic for SCALANCE .conf per-AMR fields."""

from __future__ import annotations

import re

SWITCH_IP_BLOCK = re.compile(
    r"(Name=snMspsIfIpAddr\r?\n"
    r"OID=1\.3\.6\.1\.4\.1\.4329\.20\.1\.1\.1\.1\.34\.5\.1\.2\(\.451\)\r?\n"
    r"Type=64\r?\n"
    r"Value=)([^\r\n]+)"
)

FIREWALL_DEST_1 = re.compile(
    r"(Name=snMspsFirewallNetmapDestinationAddr\r?\n"
    r"OID=1\.3\.6\.1\.4\.1\.4329\.20\.1\.1\.1\.1\.74\.1\.4\.1\.1\.21\(\.451\.450\.1\)\r?\n"
    r"Type=2000\r?\n"
    r"Value=)([^\r\n]+)"
)
FIREWALL_DEST_2 = re.compile(
    r"(Name=snMspsFirewallNetmapDestinationAddr\r?\n"
    r"OID=1\.3\.6\.1\.4\.1\.4329\.20\.1\.1\.1\.1\.74\.1\.4\.1\.1\.21\(\.451\.450\.2\)\r?\n"
    r"Type=2000\r?\n"
    r"Value=)([^\r\n]+)"
)
FIREWALL_XLATE_1 = re.compile(
    r"(Name=snMspsFirewallNetmapTranslatedSourceAddr\r?\n"
    r"OID=1\.3\.6\.1\.4\.1\.4329\.20\.1\.1\.1\.1\.74\.1\.4\.1\.1\.31\(\.450\.451\.1\)\r?\n"
    r"Type=2000\r?\n"
    r"Value=)([^\r\n]+)"
)
FIREWALL_XLATE_2 = re.compile(
    r"(Name=snMspsFirewallNetmapTranslatedSourceAddr\r?\n"
    r"OID=1\.3\.6\.1\.4\.1\.4329\.20\.1\.1\.1\.1\.74\.1\.4\.1\.1\.31\(\.450\.451\.2\)\r?\n"
    r"Type=2000\r?\n"
    r"Value=)([^\r\n]+)"
)

HEADER_MAC = re.compile(
    r"(MAC Address \(In-/Out-Band\)=)[0-9a-fA-F:]+(/)"
)
ENGINE_ID = re.compile(
    r"(Value=80:00:10:e9:03:)([0-9a-fA-F:]+)"
)

AMR_IN_FILENAME = re.compile(r"AMR[_\s-]*(\d+)", re.IGNORECASE)


def normalize_amr_id(raw: str) -> str:
    raw = raw.strip()
    match = re.match(r"AMR\s*(\d+)", raw, re.IGNORECASE)
    if match:
        return f"AMR {int(match.group(1))}"
    if raw.isdigit():
        return f"AMR {int(raw)}"
    return " ".join(raw.split())


def amr_id_from_filename(path_name: str) -> str | None:
    match = AMR_IN_FILENAME.search(path_name)
    if not match:
        return None
    return f"AMR {int(match.group(1))}"


def normalize_mac(mac: str) -> str:
    parts = mac.strip().lower().replace("-", ":").split(":")
    if len(parts) != 6:
        raise ValueError(f"expected 6 MAC octets, got {mac!r}")
    return ":".join(f"{int(p, 16):02x}" for p in parts)


def engine_id_mac(mac: str) -> str:
    parts = mac.split(":")
    last = int(parts[-1], 16)
    parts[-1] = f"{(last - 1) & 0xFF:02x}"
    return ":".join(parts)


def ip_to_hex_colon(ip: str) -> str:
    octets = [int(x) for x in ip.strip().split(".")]
    if len(octets) != 4:
        raise ValueError(f"invalid IPv4: {ip!r}")
    return ":".join(f"{o:02x}" for o in octets)


def hex_colon_to_ip(hex_value: str) -> str:
    value = hex_value.strip().lower()
    if value in ("", "00:00:00:00"):
        return ""
    parts = value.split(":")
    if len(parts) != 4:
        raise ValueError(f"expected 4 hex octets, got {hex_value!r}")
    return ".".join(str(int(p, 16)) for p in parts)


def mac_suffix_oid_decimals(mac: str) -> str:
    parts = [int(x, 16) for x in mac.split(":")]
    return ".".join(str(p) for p in parts[-3:])


def extract_fields(text: str) -> dict[str, str]:
    switch_m = SWITCH_IP_BLOCK.search(text)
    plc_m = FIREWALL_DEST_1.search(text)
    ipc_m = FIREWALL_DEST_2.search(text)
    engine_m = ENGINE_ID.search(text)
    header_m = re.search(r"MAC Address \(In-/Out-Band\)=([0-9a-fA-F:]+)", text)

    if not all([switch_m, plc_m, ipc_m, engine_m, header_m]):
        raise RuntimeError("missing required switch IP, firewall, or MAC fields")

    return {
        "mac": normalize_mac(header_m.group(1)),
        "switch_ip": switch_m.group(2).strip(),
        "ipc_ip": hex_colon_to_ip(ipc_m.group(2)),
        "plc_ip": hex_colon_to_ip(plc_m.group(2)),
        "engine_mac": normalize_mac(engine_m.group(2)),
    }


def read_template_ips(text: str) -> tuple[str, str, str]:
    switch_m = SWITCH_IP_BLOCK.search(text)
    plc_m = FIREWALL_DEST_1.search(text)
    ipc_m = FIREWALL_DEST_2.search(text)
    if not switch_m:
        raise RuntimeError("could not find switch IP block (snMspsIfIpAddr .451)")
    if not plc_m or not ipc_m:
        raise RuntimeError("could not find firewall IPC/PLC hex blocks")
    return switch_m.group(2), ipc_m.group(2), plc_m.group(2)


def read_template_macs(text: str) -> tuple[str, str]:
    engine_m = ENGINE_ID.search(text)
    header_m = re.search(r"MAC Address \(In-/Out-Band\)=([0-9a-fA-F:]+)", text)
    if not engine_m or not header_m:
        raise RuntimeError("could not find template MAC / SNMP engine ID")
    return normalize_mac(header_m.group(1)), normalize_mac(engine_m.group(2))


def apply_ips(
    text: str,
    switch_ip: str,
    ipc_ip: str,
    plc_ip: str,
) -> str:
    ipc_hex = ip_to_hex_colon(ipc_ip)
    plc_hex = ip_to_hex_colon(plc_ip)
    text = SWITCH_IP_BLOCK.sub(rf"\g<1>{switch_ip}", text, count=1)
    text = FIREWALL_DEST_1.sub(rf"\g<1>{plc_hex}", text, count=1)
    text = FIREWALL_DEST_2.sub(rf"\g<1>{ipc_hex}", text, count=1)
    text = FIREWALL_XLATE_1.sub(rf"\g<1>{plc_hex}", text, count=1)
    text = FIREWALL_XLATE_2.sub(rf"\g<1>{ipc_hex}", text, count=1)
    return text


def apply_mac(text: str, template_header: str, template_engine: str, header_mac: str) -> str:
    engine_mac = engine_id_mac(header_mac)
    text = HEADER_MAC.sub(rf"\g<1>{header_mac}\g<2>", text, count=1)
    text = ENGINE_ID.sub(rf"\g<1>{engine_mac}", text, count=1)

    old_suffix = mac_suffix_oid_decimals(template_engine)
    new_suffix = mac_suffix_oid_decimals(engine_mac)
    text = text.replace(f"116.252.69.{old_suffix}", f"116.252.69.{new_suffix}")
    text = text.replace(template_header, header_mac)
    text = text.replace(template_engine, engine_mac)
    return text

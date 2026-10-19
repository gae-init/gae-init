#!/usr/bin/env python3
import glob
import json
import os
import struct
import sys
from pathlib import Path

try:
    from google.appengine.api import datastore
    from google.appengine.datastore import entity_bytes_pb2

    HAS_APPENGINE = True
except ImportError:
    HAS_APPENGINE = False

try:
    from google.cloud.datastore_v1.types import Entity
    from google.protobuf.json_format import MessageToDict

    HAS_DATASTORE_V1 = True
except ImportError:
    HAS_DATASTORE_V1 = False

BLOCK_SIZE = 32768
HEADER_SIZE = 7


def read_varint32(stream):
    """Reads a protobuf varint32 from a binary stream."""
    value = 0
    shift = 0
    while True:
        byte_byte = stream.read(1)
        if not byte_byte:
            return None  # End of file
        b = byte_byte[0]
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return value


def _read_leveldb_records(stream, file_path="<stream>"):
    """Yields record payloads from a LevelDB log file stream (used by gcloud datastore export)."""
    current_record = bytearray()
    while True:
        pos = stream.tell()
        offset_in_block = pos % BLOCK_SIZE
        remaining_in_block = BLOCK_SIZE - offset_in_block

        if remaining_in_block < HEADER_SIZE:
            # Trailing padding in 32KB block (fewer than 7 bytes remaining)
            stream.read(remaining_in_block)
            continue

        header = stream.read(HEADER_SIZE)
        if not header or len(header) < HEADER_SIZE:
            break

        _crc, length, rtype = struct.unpack("<IHB", header)

        # Type 0 with 0 length indicates padding to the end of the 32KB block
        if rtype == 0 and length == 0:
            stream.read(remaining_in_block - HEADER_SIZE)
            continue

        data = stream.read(length)
        if len(data) < length:
            print(f"Warning: Unexpected EOF in record data in {file_path}", file=sys.stderr)
            break

        if rtype == 1:  # FULL record
            yield bytes(data)
        elif rtype == 2:  # FIRST fragment
            current_record = bytearray(data)
        elif rtype == 3:  # MIDDLE fragment
            current_record.extend(data)
        elif rtype == 4:  # LAST fragment
            current_record.extend(data)
            yield bytes(current_record)
            current_record = bytearray()
        else:
            print(f"Warning: Unknown record type {rtype} at offset {pos} in {file_path}", file=sys.stderr)
            break


def _read_varint_records(stream, file_path="<stream>"):
    """Yields record payloads from a varint32-prefixed binary stream."""
    while True:
        record_len = read_varint32(stream)
        if record_len is None:
            break

        record_bytes = stream.read(record_len)
        if len(record_bytes) < record_len:
            print(f"Warning: Unexpected EOF in {file_path}", file=sys.stderr)
            break

        yield record_bytes


def read_records_from_file(file_path):
    """Yields binary record payloads from a data file, auto-detecting LevelDB or varint format."""
    with open(file_path, "rb") as f:
        header = f.read(HEADER_SIZE)
        if len(header) == HEADER_SIZE:
            _, length, rtype = struct.unpack("<IHB", header)
            if rtype in (1, 2) and length <= (BLOCK_SIZE - HEADER_SIZE):
                # Standard LevelDB log format
                f.seek(0)
                yield from _read_leveldb_records(f, file_path)
                return

        # Fallback to varint32 length-prefixed stream
        f.seek(0)
        yield from _read_varint_records(f, file_path)


def format_gae_key(key):
    """Formats an App Engine datastore.Key into a deterministic path string."""
    path = key.to_path()
    elements = [f"{path[i]}:{path[i+1]}" for i in range(0, len(path), 2)]
    key_str = "/".join(elements)
    if key.namespace():
        return f"[{key.namespace()}]{key_str}"
    return key_str


def format_python_value(val):
    """Formats native Python values into JSON-serializable types."""
    if val is None or isinstance(val, (int, float, bool, str)):
        return val
    if hasattr(val, "isoformat"):
        return val.isoformat()
    if isinstance(val, (list, tuple)):
        return [format_python_value(x) for x in val]
    if isinstance(val, dict):
        return {k: format_python_value(v) for k, v in val.items()}
    if hasattr(val, "to_path"):
        return format_gae_key(val)
    if hasattr(val, "email"):
        return val.email()
    if hasattr(val, "lat") and hasattr(val, "lon"):
        return {"lat": val.lat, "lon": val.lon}
    if isinstance(val, (bytes, bytearray)):
        try:
            return val.decode("utf-8")
        except UnicodeDecodeError:
            return f"<BLOB: {len(val)} bytes>"
    return str(val)


def extract_typed_v1_value(val_dict):
    """Extracts raw Python native types from Datastore v1 property value representations."""
    if "stringValue" in val_dict:
        return val_dict["stringValue"]
    if "integerValue" in val_dict:
        return int(val_dict["integerValue"])
    if "doubleValue" in val_dict:
        return float(val_dict["doubleValue"])
    if "booleanValue" in val_dict:
        return val_dict["booleanValue"]
    if "timestampValue" in val_dict:
        return val_dict["timestampValue"]
    if "arrayValue" in val_dict:
        return [extract_typed_v1_value(v) for v in val_dict["arrayValue"].get("values", [])]
    if "entityValue" in val_dict:
        raw_sub = val_dict["entityValue"].get("properties", {})
        return {k: extract_typed_v1_value(v) for k, v in raw_sub.items()}
    if "nullValue" in val_dict:
        return None
    if "blobValue" in val_dict:
        return f"<BLOB: {len(val_dict['blobValue'])} bytes>"
    return str(val_dict)


def format_v1_entity_for_diff(entity_dict):
    """Normalizes key and property formats to produce deterministic, clean JSON for v1 Entity."""
    key = entity_dict.get("key", {})
    path_elements = key.get("path", [])

    key_str = "/".join(
        f"{elem.get('kind')}:{elem.get('id') or elem.get('name')}"
        for elem in path_elements
    )
    namespace = key.get("partitionId", {}).get("namespaceId")
    if namespace:
        key_str = f"[{namespace}]{key_str}"

    properties = {}
    raw_props = entity_dict.get("properties", {})
    for prop_name, prop_val in sorted(raw_props.items()):
        properties[prop_name] = extract_typed_v1_value(prop_val)

    return {
        "__key__": key_str,
        "properties": properties,
    }


def parse_entity_record(record_bytes):
    """Parses a single entity protobuf record.

    Supports GAE EntityProto (v3) as well as Cloud Datastore v1 Entity.
    """
    if HAS_APPENGINE:
        try:
            entity_v3 = entity_bytes_pb2.EntityProto()
            entity_v3.ParseFromString(record_bytes)
            if entity_v3.key.path.element:
                e = datastore.Entity.FromPb(entity_v3)
                key_str = format_gae_key(e.key())
                kind = e.kind()
                properties = {k: format_python_value(v) for k, v in sorted(e.items())}
                return kind, {"__key__": key_str, "properties": properties}
        except Exception:
            pass

    if HAS_DATASTORE_V1:
        try:
            entity_v1 = Entity()
            entity_v1._pb.ParseFromString(record_bytes)
            entity_dict = MessageToDict(entity_v1._pb)
            if entity_dict.get("key", {}).get("path"):
                key_path = entity_dict["key"]["path"]
                kind = key_path[-1].get("kind", "UnknownKind")
                formatted = format_v1_entity_for_diff(entity_dict)
                return kind, formatted
        except Exception:
            pass

    return None, None


def parse_data_file(file_path):
    """Parses a single export data file containing serialized entity records."""
    entities = []
    for record_bytes in read_records_from_file(file_path):
        kind, formatted = parse_entity_record(record_bytes)
        if kind and formatted:
            entities.append((kind, formatted))
        else:
            print(f"Warning: Could not decode record ({len(record_bytes)} bytes) in {file_path}", file=sys.stderr)
    return entities


def process_export_directory(export_target, output_dir):
    """Processes all export files and splits them into JSON dumps per Kind."""
    if not HAS_APPENGINE and not HAS_DATASTORE_V1:
        print(
            "Error: Neither 'appengine-python-standard' nor 'google-cloud-datastore' is available.\n"
            "Please run using your project virtual environment (e.g. ./.venv/bin/python).",
            file=sys.stderr,
        )
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    if os.path.isfile(export_target):
        data_files = [export_target]
    else:
        # Find all data files in export folder
        data_files = glob.glob(os.path.join(export_target, "**", "output-*"), recursive=True)
        if not data_files:
            # Fallback to direct .dada files if named differently
            data_files = glob.glob(os.path.join(export_target, "**", "*.dada*"), recursive=True)

    print(f"Found {len(data_files)} data record file(s) in '{export_target}'. Processing...")

    entities_by_kind = {}

    for file_path in data_files:
        parsed_entries = parse_data_file(file_path)
        for kind, formatted in parsed_entries:
            if kind not in entities_by_kind:
                entities_by_kind[kind] = []
            entities_by_kind[kind].append(formatted)

    # Write out separate JSON file for each Kind, sorted by entity Key
    for kind, entities in sorted(entities_by_kind.items()):
        # Sort entities by key string to ensure deterministic JSON ordering across diffs
        entities.sort(key=lambda x: x["__key__"])

        output_file = os.path.join(output_dir, f"{kind}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(entities, f, indent=2, ensure_ascii=False)

        print(f"Exported {len(entities)} '{kind}' entities to '{output_file}'")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python inspect-datastore.py <EXPORT_DIRECTORY_OR_FILE> <OUTPUT_JSON_DIRECTORY>")
        sys.exit(1)

    export_path = sys.argv[1]
    output_path = sys.argv[2]

    process_export_directory(export_path, output_path)

#!/usr/bin/env python3
"""scaffold_from_schema.py — derive a Pact consumer/provider test from a contract source.

Pact is code-first: a schema never *is* a classic pact. This tool reads a contract
source and emits a STARTING-POINT test (request shape + response matchers) plus notes
on which fields to review. It is intentionally dependency-free (stdlib only) so it runs
anywhere; for formats it cannot fully parse it emits a structured TODO scaffold.

Supported --type values and how each maps to Pact (see references/schema-driven.md):
  openapi|swagger  REST/JSON over HTTP  -> consumer HTTP test (or use bi-directional)
  jsonschema       JSON payload/event   -> matchers for HTTP or message pact
  xsd              XML / SOAP           -> HTTP + XML matchers (design source)
  wsdl             SOAP description     -> one HTTP interaction per operation + XML
  protobuf         gRPC / binary RPC    -> V4 + pact-protobuf-plugin (references .proto)
  avro             Kafka schema         -> V4 + pact-avro-plugin (message pact)
  asyncapi         event-driven         -> message pact (design source)
  graphql          GraphQL SDL          -> HTTP POST with query/variables matchers
  pact             existing pact file   -> summarize / stub provider verification

Usage:
  python scaffold_from_schema.py --type openapi --input api.yaml \
      --operation "GET /orders/{id}" --lang java --role consumer --out OrderClientPactTest.java

Always REVIEW the output: tighten/loosen guessed regexes, set real provider-state names,
and confirm which fields are genuinely fixed vs. matched by type.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SUPPORTED_TYPES = [
    "openapi", "swagger", "jsonschema", "xsd", "wsdl",
    "protobuf", "avro", "asyncapi", "graphql", "pact",
]
SUPPORTED_LANGS = ["java", "js", "dotnet", "go", "python"]


# --------------------------------------------------------------------------- #
# Input loading
# --------------------------------------------------------------------------- #
def load_structured(path: Path) -> dict:
    """Load JSON, or YAML if PyYAML is available; else raise with guidance."""
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return json.loads(text)
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        raise SystemExit(
            "FAIL: input looks like YAML but PyYAML is not installed. "
            "Install it (`pip install pyyaml`) or convert the spec to JSON."
        )


# --------------------------------------------------------------------------- #
# Matcher derivation (JSON Schema / OpenAPI schema object -> example value tree)
# --------------------------------------------------------------------------- #
FORMAT_REGEX = {
    "uuid": r"[0-9a-fA-F-]{36}",
    "email": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    "date": r"\d{4}-\d{2}-\d{2}",
    "date-time": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*",
}


def schema_to_matchers(schema: dict, defs: dict | None = None, depth: int = 0) -> dict:
    """Return a {field: {"kind": ..., "example": ..., "regex": ...}} description tree."""
    defs = defs or {}
    if not isinstance(schema, dict):
        return {"kind": "any", "example": None}

    if "$ref" in schema:
        ref = schema["$ref"].split("/")[-1]
        schema = defs.get(ref, {})

    t = schema.get("type")
    if "enum" in schema:
        vals = schema["enum"]
        return {"kind": "regex", "regex": "|".join(map(re.escape, map(str, vals))),
                "example": vals[0]}
    if t == "object" or "properties" in schema:
        props = schema.get("properties", {})
        return {"kind": "object",
                "fields": {k: schema_to_matchers(v, defs, depth + 1) for k, v in props.items()}}
    if t == "array":
        return {"kind": "array", "items": schema_to_matchers(schema.get("items", {}), defs, depth + 1)}
    if t == "string":
        fmt = schema.get("format")
        pat = schema.get("pattern") or FORMAT_REGEX.get(fmt or "")
        if pat:
            return {"kind": "regex", "regex": pat, "example": schema.get("example", "string")}
        return {"kind": "string", "example": schema.get("example", "string")}
    if t in ("integer", "number"):
        return {"kind": "number", "example": schema.get("example", 1 if t == "integer" else 1.0)}
    if t == "boolean":
        return {"kind": "boolean", "example": schema.get("example", True)}
    return {"kind": "any", "example": schema.get("example")}


# --------------------------------------------------------------------------- #
# Rendering matchers per language
# --------------------------------------------------------------------------- #
def render_body(node: dict, lang: str, indent: int = 0) -> str:
    pad = "  " * (indent + 1)
    if node["kind"] == "object":
        lines = []
        for name, child in node["fields"].items():
            lines.append(pad + render_field(name, child, lang, indent + 1))
        return "{\n" + "\n".join(lines) + "\n" + ("  " * indent) + "}"
    return render_field("value", node, lang, indent)


def render_field(name: str, node: dict, lang: str, indent: int) -> str:
    k = node["kind"]
    if lang == "java":
        if k == "number":
            return f'o.numberType("{name}", {node["example"]});'
        if k == "regex":
            return f'o.stringMatcher("{name}", "{node["regex"]}", "{node.get("example", "")}");'
        if k == "string":
            return f'o.stringType("{name}", "{node["example"]}");'
        if k == "boolean":
            return f'o.booleanType("{name}", {str(node["example"]).lower()});'
        if k == "array":
            return f'o.eachLike("{name}", item -> {{ /* TODO matchers */ }});'
        if k == "object":
            return f'o.object("{name}", obj -> {{ /* TODO nested */ }});'
        return f'// TODO {name}'
    # JS / others: emit a MatchersV3-style JSON comment block
    if k == "number":
        return f'"{name}": integer({node["example"]}),'
    if k == "regex":
        return f'"{name}": regex("{node["regex"]}", "{node.get("example", "")}"),'
    if k == "string":
        return f'"{name}": string("{node["example"]}"),'
    if k == "boolean":
        return f'"{name}": boolean({str(node["example"]).lower()}),'
    if k == "array":
        return f'"{name}": eachLike({{ /* TODO */ }}),'
    if k == "object":
        return f'"{name}": like({{ /* TODO */ }}),'
    return f'// TODO {name}'


# --------------------------------------------------------------------------- #
# Per-type handlers -> (title, body_node_or_None, notes[])
# --------------------------------------------------------------------------- #
def handle_openapi(spec: dict, operation: str | None) -> tuple[str, dict | None, list[str]]:
    defs = {**spec.get("components", {}).get("schemas", {}), **spec.get("definitions", {})}
    if not operation:
        ops = [f"{m.upper()} {p}" for p, item in spec.get("paths", {}).items()
               for m in item if m in ("get", "post", "put", "patch", "delete")]
        raise SystemExit("FAIL: --operation required. Available:\n  " + "\n  ".join(ops))
    method, path = operation.split(" ", 1)
    op = spec.get("paths", {}).get(path, {}).get(method.lower())
    if not op:
        raise SystemExit(f"FAIL: operation '{operation}' not found in spec.")
    notes = []
    body = None
    responses = op.get("responses", {})
    ok = responses.get("200") or responses.get("201") or next(iter(responses.values()), {})
    content = (ok or {}).get("content", {}).get("application/json", {})
    if content.get("schema"):
        body = schema_to_matchers(content["schema"], defs)
    else:
        notes.append("No application/json response schema found; add response matchers manually.")
    notes.append("Set the provider state in given(...) to match your data setup.")
    notes.append("Review every regex matcher — widen or tighten as needed.")
    return f"{method} {path}", body, notes


def handle_graphql(_text: str) -> tuple[str, dict | None, list[str]]:
    notes = [
        "GraphQL has no special Pact mode: model as HTTP POST to the GraphQL endpoint.",
        'Request body: { "query": "<operation>", "variables": {...} } — match query (regex/like) and variables.',
        "Response: match data/errors shape with matchers derived from the SDL types.",
        "Use spec V4.",
    ]
    return "POST /graphql", None, notes


def handle_plugin(kind: str, schema_path: str) -> tuple[str, dict | None, list[str]]:
    plugin = "protobuf" if kind == "protobuf" else "avro"
    notes = [
        f"{kind} requires Pact spec V4 + the pact-{plugin}-plugin.",
        f"Install once: pact-plugin-cli install {plugin}",
        f"Reference the schema file ({schema_path}) in the interaction; the plugin matches the binary payload.",
        "Avro interactions are message pacts (Kafka); Protobuf/gRPC are sync-message/HTTP2.",
    ]
    return f"{kind} interaction (plugin)", None, notes


def handle_xml(kind: str) -> tuple[str, dict | None, list[str]]:
    notes = [
        f"{kind.upper()} maps to an HTTP interaction with an XML body — use XML matchers, not JSON.",
        "Content-Type: text/xml (SOAP 1.1) or application/soap+xml (SOAP 1.2); set SOAPAction for SOAP.",
        "Build the body with PactXmlBuilder (JVM) / XML matcher helpers; keep namespaces + required elements exact.",
        "WSDL: scaffold one interaction per <wsdl:operation>; message types usually reference XSD.",
    ]
    return f"{kind.upper()} SOAP/XML interaction", None, notes


def handle_asyncapi(spec: dict) -> tuple[str, dict | None, list[str]]:
    notes = [
        "AsyncAPI is a design source for MESSAGE pacts (test the domain port, not the transport).",
        "Read the channel's message payload schema and derive matchers from it.",
        "Use spec V4 for message pacts.",
    ]
    return "async message", None, notes


def handle_pact(spec: dict) -> tuple[str, dict | None, list[str]]:
    consumer = spec.get("consumer", {}).get("name", "?")
    provider = spec.get("provider", {}).get("name", "?")
    inter = spec.get("interactions", []) or spec.get("messages", [])
    notes = [f"Existing pact: {consumer} -> {provider}, {len(inter)} interaction(s).",
             "Do not regenerate — verify this pact against the provider or publish it to the broker.",
             "Provider states referenced: " +
             ", ".join(sorted({i.get("providerState") or i.get("provider_state") or ps.get("name")
                               for i in inter for ps in (i.get("providerStates") or [{}])
                               if (i.get("providerState") or i.get("provider_state") or ps.get("name"))})) or "(none)"]
    return f"verify {consumer}->{provider}", None, notes


# --------------------------------------------------------------------------- #
# Output assembly
# --------------------------------------------------------------------------- #
def render_output(args, title, body, notes) -> str:
    header = [
        "// === Pact scaffold (REVIEW BEFORE USE) ===",
        f"// type={args.type} role={args.role} lang={args.lang}",
        f"// source={args.input}",
        f"// target interaction: {title}",
        "//",
        "// NOTES:",
    ]
    header += [f"//  - {n}" for n in notes]
    header.append("")
    if body is not None:
        header.append("// Response body matchers (Java DSL shown; adapt to your language pack):")
        header.append("// .body(newJsonBody(o -> " + render_body(body, "java") + ").build())")
        header.append("")
        header.append("// JSON/MatchersV3 form:")
        header.append("// " + render_body(body, "js").replace("\n", "\n// "))
    else:
        header.append("// No JSON body matchers generated for this contract type — see NOTES above.")
    return "\n".join(header) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Scaffold a Pact test from a contract source.")
    p.add_argument("--type", required=True, choices=SUPPORTED_TYPES)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--lang", default="java", choices=SUPPORTED_LANGS)
    p.add_argument("--role", default="consumer", choices=["consumer", "provider"])
    p.add_argument("--operation", help='e.g. "GET /orders/{id}" (OpenAPI)')
    p.add_argument("--channel", help="AsyncAPI channel name")
    p.add_argument("--message", help="message/record name")
    p.add_argument("--out", type=Path, help="output file (default: stdout)")
    args = p.parse_args(argv)

    if not args.input.exists():
        print(f"FAIL: input not found: {args.input}", file=sys.stderr)
        return 2

    t = args.type
    if t in ("openapi", "swagger"):
        title, body, notes = handle_openapi(load_structured(args.input), args.operation)
    elif t == "jsonschema":
        node = schema_to_matchers(load_structured(args.input))
        title, body, notes = "json payload", node, ["Use for HTTP body or message pact.",
                                                     "Review every regex matcher."]
    elif t in ("xsd", "wsdl"):
        title, body, notes = handle_xml(t)
    elif t in ("protobuf", "avro"):
        title, body, notes = handle_plugin(t, str(args.input))
    elif t == "asyncapi":
        title, body, notes = handle_asyncapi(load_structured(args.input))
    elif t == "graphql":
        title, body, notes = handle_graphql(args.input.read_text(encoding="utf-8"))
    elif t == "pact":
        title, body, notes = handle_pact(load_structured(args.input))
    else:
        print(f"FAIL: unsupported type {t}", file=sys.stderr)
        return 2

    out = render_output(args, title, body, notes)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out, encoding="utf-8")
        print(f"Wrote scaffold to {args.out}")
        print("REVIEW the matchers and provider-state names before committing.")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

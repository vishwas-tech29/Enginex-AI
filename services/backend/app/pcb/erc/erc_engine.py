from dataclasses import dataclass

from app.pcb.layout import PCBLayoutDocument, build_nets, footprint_pads_by_id, pad_world_position

POWER_NET_NAMES = {"GND", "VCC", "VDD", "VSS", "3V3", "5V", "1V8", "GROUND"}
DRIVER_CATEGORIES = {"ic", "microcontroller", "connector"}


@dataclass
class ERCViolation:
    violation_id: str
    rule: str
    severity: str  # "error" | "warning"
    net_name: str
    message: str

    def to_dict(self) -> dict:
        return {
            "id": self.violation_id,
            "rule": self.rule,
            "severity": self.severity,
            "net": self.net_name,
            "message": self.message,
        }


def run_erc(
    doc: PCBLayoutDocument,
    components: list,
    footprints_by_id: dict[str, object],
    library_components_by_id: dict[str, object],
) -> list[ERCViolation]:
    nets = build_nets(components)
    violations: list[ERCViolation] = []
    violations += _check_unassigned_pads(components, footprints_by_id, nets)
    violations += _check_floating_nets(nets)
    violations += _check_undriven_signals(nets, components, library_components_by_id)
    violations += _check_short_circuits(doc, components, footprints_by_id)
    return violations


def _check_unassigned_pads(
    components: list, footprints_by_id: dict[str, object], nets: dict
) -> list[ERCViolation]:
    assigned = {(ref, pad_id) for net in nets.values() for ref, pad_id in net.pins}
    violations = []
    for component in components:
        footprint = footprints_by_id.get(str(component.footprint_id)) if component.footprint_id else None
        if not footprint:
            continue
        for pad_id in footprint_pads_by_id(footprint):
            if (component.reference_designator, pad_id) not in assigned:
                violations.append(
                    ERCViolation(
                        f"unassigned_{component.reference_designator}_{pad_id}",
                        "unassigned_pad",
                        "warning",
                        "",
                        f"Pad {component.reference_designator}:{pad_id} has no net assigned",
                    )
                )
    return violations


def _check_floating_nets(nets: dict) -> list[ERCViolation]:
    violations = []
    for name, net in nets.items():
        if len(net.pins) == 1:
            ref, pad_id = net.pins[0]
            violations.append(
                ERCViolation(
                    f"floating_{name}",
                    "floating_net",
                    "error",
                    name,
                    f"Net '{name}' has only one connection (at {ref}:{pad_id})",
                )
            )
    return violations


def _check_undriven_signals(
    nets: dict, components: list, library_components_by_id: dict[str, object]
) -> list[ERCViolation]:
    """Flags signal nets with no IC/connector/microcontroller pin attached.
    Only runs on nets where at least one pin's component is linked to the
    shared component library — without that we have no category data to
    judge "driven" by, and a false positive is worse than staying silent."""
    components_by_ref = {c.reference_designator: c for c in components}
    violations = []
    for name, net in nets.items():
        if name.upper() in POWER_NET_NAMES:
            continue
        categories = []
        for ref, _pad_id in net.pins:
            component = components_by_ref.get(ref)
            if not component or not component.library_entry_id:
                continue
            library_component = library_components_by_id.get(str(component.library_entry_id))
            if library_component:
                categories.append(library_component.category.lower())
        if not categories:
            continue
        if not any(category in DRIVER_CATEGORIES for category in categories):
            violations.append(
                ERCViolation(
                    f"undriven_{name}",
                    "undriven_signal",
                    "warning",
                    name,
                    f"Net '{name}' has no driver IC/connector/microcontroller pin connected",
                )
            )
    return violations


def _check_short_circuits(
    doc: PCBLayoutDocument, components: list, footprints_by_id: dict[str, object]
) -> list[ERCViolation]:
    """A trace whose endpoint sits inside a pad belonging to a net other
    than the trace's own declared net is a short between those nets."""
    pad_points: list[tuple] = []  # (Point, net, radius)
    for component in components:
        footprint = footprints_by_id.get(str(component.footprint_id)) if component.footprint_id else None
        if not footprint:
            continue
        net_map = (component.data or {}).get("net_map", {})
        for pad_id, pad in footprint_pads_by_id(footprint).items():
            net = net_map.get(pad_id)
            if not net:
                continue
            point = pad_world_position(component, pad)
            radius = max(float(pad.get("width", 0.5)), float(pad.get("height", 0.5))) / 2
            pad_points.append((point, net, radius))

    violations = []
    for trace in doc.traces.values():
        touching_nets = {trace.net}
        for point, net, radius in pad_points:
            if point.distance_to(trace.start) <= radius or point.distance_to(trace.end) <= radius:
                touching_nets.add(net)
        if len(touching_nets) > 1:
            violations.append(
                ERCViolation(
                    f"short_{trace.segment_id}",
                    "short_circuit",
                    "error",
                    trace.net,
                    f"Trace {trace.segment_id} (net '{trace.net}') touches pads on nets: "
                    f"{', '.join(sorted(touching_nets))}",
                )
            )
    return violations

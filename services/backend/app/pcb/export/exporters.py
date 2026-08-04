"""Manufacturing export: Gerber (RS-274X), NC drill, netlist, BOM, and a
real 3D board slab (reusing the CadQuery/OpenCascade kernel already backing
CAD's STEP/mesh export — see app.cad.export.exporters) instead of a
hand-written STEP text dump that no real CAD tool could actually open.
"""

import datetime

import cadquery as cq

from app.pcb.layers import LayerType
from app.pcb.layout import PCBLayoutDocument, build_nets, footprint_pads_by_id, pad_world_position

INCH_PER_MM = 1 / 25.4


class GerberExporter:
    """RS-274X, one file per layer. Apertures are allocated on demand (one
    D-code per distinct trace width / pad size actually used), which keeps
    the file both small and syntactically valid — unlike referencing a
    D-code that was never defined."""

    def export_copper_layer(
        self,
        components: list,
        footprints_by_id: dict[str, object],
        doc: PCBLayoutDocument,
        layer: LayerType,
    ) -> str:
        lines = ["%FSLAX25Y25*%", "%MOIN*%", "%LPD*%"]
        aperture_by_size: dict[float, int] = {}
        next_dcode = 10

        def aperture_for(diameter_mm: float) -> int:
            nonlocal next_dcode
            key = round(diameter_mm, 4)
            if key not in aperture_by_size:
                lines.append(f"%ADD{next_dcode}C,{diameter_mm * INCH_PER_MM:.4f}*%")
                aperture_by_size[key] = next_dcode
                next_dcode += 1
            return aperture_by_size[key]

        def to_units(mm: float) -> int:
            return int(round(mm * INCH_PER_MM * 100000))

        for component in components:
            footprint = footprints_by_id.get(str(component.footprint_id)) if component.footprint_id else None
            if not footprint:
                continue
            for pad in footprint_pads_by_id(footprint).values():
                if layer.value not in pad.get("layers", []):
                    continue
                point = pad_world_position(component, pad)
                size = max(float(pad.get("width", 0.5)), float(pad.get("height", 0.5)))
                dcode = aperture_for(size)
                lines.append(f"D{dcode}*")
                lines.append(f"X{to_units(point.x)}Y{to_units(point.y)}D03*")

        for trace in doc.traces.values():
            if trace.layer != layer:
                continue
            dcode = aperture_for(trace.width)
            lines.append(f"D{dcode}*")
            lines.append(f"X{to_units(trace.start.x)}Y{to_units(trace.start.y)}D02*")
            lines.append(f"X{to_units(trace.end.x)}Y{to_units(trace.end.y)}D01*")

        lines.append("M02*")
        return "\n".join(lines)

    def export_solder_mask(
        self, components: list, footprints_by_id: dict[str, object], doc: PCBLayoutDocument, side: str = "top"
    ) -> str:
        layer = LayerType.SOLDER_MASK_TOP if side == "top" else LayerType.SOLDER_MASK_BOTTOM
        return self.export_copper_layer(components, footprints_by_id, doc, layer)


class NCDrillExporter:
    """Excellon-style NC drill file covering plated through-hole pads and vias."""

    def export(self, components: list, footprints_by_id: dict[str, object], doc: PCBLayoutDocument) -> str:
        hits: list[tuple[float, float, float]] = []  # (x_mm, y_mm, drill_mm)

        for component in components:
            footprint = footprints_by_id.get(str(component.footprint_id)) if component.footprint_id else None
            if not footprint:
                continue
            for pad in footprint_pads_by_id(footprint).values():
                drill = pad.get("drill")
                if not drill:
                    continue
                point = pad_world_position(component, pad)
                hits.append((point.x, point.y, float(drill)))

        for via in doc.vias.values():
            hits.append((via.position.x, via.position.y, via.drill_diameter))

        drill_sizes = sorted({round(h[2], 4) for h in hits})
        tool_by_size = {size: i + 1 for i, size in enumerate(drill_sizes)}

        lines = ["M48", "INCH,TZ,00.0000,00.0000"]
        for size in drill_sizes:
            lines.append(f"T{tool_by_size[size]}C{size * INCH_PER_MM:.4f}")
        lines.append("%")

        current_tool = None
        for x_mm, y_mm, drill_mm in hits:
            tool = tool_by_size[round(drill_mm, 4)]
            if tool != current_tool:
                lines.append(f"T{tool}")
                current_tool = tool
            lines.append(f"X{int(round(x_mm * INCH_PER_MM * 10000))}Y{int(round(y_mm * INCH_PER_MM * 10000))}")

        lines.extend(["M30", "%"])
        return "\n".join(lines)


class NetlistExporter:
    def export(self, board_name: str, components: list) -> str:
        nets = build_nets(components)
        lines = [
            "(export (version D)",
            " (design",
            f'  (source "{board_name}")',
            f'  (date "{datetime.datetime.now(datetime.timezone.utc).isoformat()}")',
            '  (tool "Enginex AI PCB")',
            " )",
            " (nets",
        ]
        for i, net in enumerate(nets.values(), 1):
            lines.append(f'  ({i} "{net.name}"')
            for component_ref, pad_id in net.pins:
                lines.append(f"   (node {component_ref} {pad_id})")
            lines.append("  )")
        lines.extend([" )", ")"])
        return "\n".join(lines)


class BOMExporter:
    def export(self, components: list, library_components_by_id: dict[str, object]) -> str:
        groups: dict[tuple[str, str], list[str]] = {}
        for component in components:
            value = str((component.data or {}).get("value", ""))
            library_component = (
                library_components_by_id.get(str(component.library_entry_id))
                if component.library_entry_id
                else None
            )
            mpn = library_component.part_number if library_component else ""
            groups.setdefault((value, mpn), []).append(component.reference_designator)

        lines = ["Reference,Value,Quantity,Manufacturer Part Number"]
        for (value, mpn), refs in sorted(groups.items()):
            refs_field = ";".join(sorted(refs))
            lines.append(f'"{refs_field}",{value},{len(refs)},{mpn}')
        return "\n".join(lines)


def build_board_shape(width_mm: float, height_mm: float, thickness_mm: float = 1.6) -> cq.Workplane:
    """A real extruded solid for the bare board outline — real enough
    geometry for CAD.export_step/export_stl/get_mesh to work on directly,
    reusing the same OCCT kernel as the mechanical CAD engine rather than
    hand-writing STEP entities."""
    return cq.Workplane("XY").rect(width_mm, height_mm).extrude(thickness_mm)

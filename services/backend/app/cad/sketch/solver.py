from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import least_squares

from app.cad.sketch.constraints import SketchConstraint, residuals
from app.cad.sketch.entities import SketchDocument

RESIDUAL_TOLERANCE = 1e-6


@dataclass
class SolveResult:
    status: str  # "solved" | "under_constrained" | "over_constrained" | "empty" | "error"
    is_fully_constrained: bool
    residual_norm: float
    dof_remaining: int
    conflicting_constraints: list[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "is_fully_constrained": self.is_fully_constrained,
            "residual_norm": self.residual_norm,
            "dof_remaining": self.dof_remaining,
            "conflicting_constraints": self.conflicting_constraints,
            "message": self.message,
        }


class _VarMap:
    """Bidirectional mapping between sketch free variables and a flat vector
    scipy's solver can operate on."""

    def __init__(self, doc: SketchDocument):
        self.doc = doc
        self.slots: list[tuple[str, str, str]] = []  # (kind, entity_id, field)
        for pid, p in doc.points.items():
            if not p.fixed:
                self.slots.append(("point_x", pid, "x"))
                self.slots.append(("point_y", pid, "y"))
        for cid in doc.circles:
            self.slots.append(("circle_r", cid, "radius"))
        for aid in doc.arcs:
            self.slots.append(("arc_r", aid, "radius"))
            self.slots.append(("arc_start", aid, "start_angle"))
            self.slots.append(("arc_end", aid, "end_angle"))

    @property
    def size(self) -> int:
        return len(self.slots)

    def pack(self) -> np.ndarray:
        values = []
        for kind, eid, _ in self.slots:
            if kind == "point_x":
                values.append(self.doc.points[eid].x)
            elif kind == "point_y":
                values.append(self.doc.points[eid].y)
            elif kind == "circle_r":
                values.append(self.doc.circles[eid].radius)
            elif kind == "arc_r":
                values.append(self.doc.arcs[eid].radius)
            elif kind == "arc_start":
                values.append(self.doc.arcs[eid].start_angle)
            elif kind == "arc_end":
                values.append(self.doc.arcs[eid].end_angle)
        return np.array(values, dtype=float)

    def unpack(self, vector: np.ndarray) -> None:
        for value, (kind, eid, _) in zip(vector, self.slots):
            if kind == "point_x":
                self.doc.points[eid].x = float(value)
            elif kind == "point_y":
                self.doc.points[eid].y = float(value)
            elif kind == "circle_r":
                self.doc.circles[eid].radius = float(value)
            elif kind == "arc_r":
                self.doc.arcs[eid].radius = float(value)
            elif kind == "arc_start":
                self.doc.arcs[eid].start_angle = float(value)
            elif kind == "arc_end":
                self.doc.arcs[eid].end_angle = float(value)


class SketchSolver:
    """Solves a 2D sketch's geometric/dimensional constraints with
    scipy's least-squares (Gauss-Newton/Levenberg-Marquardt via `least_squares`):
    each constraint contributes one or more residual equations that should
    be ~0 when satisfied, and the solver adjusts every free point coordinate
    (plus circle/arc radii and arc angles) to minimize them simultaneously.

    Over/under-constrained detection is numerical, not symbolic: after
    solving, the Jacobian's rank tells us how many effective degrees of
    freedom remain (`dof_remaining = free_vars - rank`), and a
    non-converged residual with `#constraint equations >= #free vars`
    indicates a conflicting (over-constrained) system.
    """

    def __init__(self, doc: SketchDocument, constraints: list[SketchConstraint]):
        self.doc = doc
        self.constraints = constraints

    def _residual_vector(self, x: np.ndarray, varmap: _VarMap) -> np.ndarray:
        varmap.unpack(x)
        out: list[float] = []
        for c in self.constraints:
            out.extend(residuals(self.doc, c))
        return np.array(out, dtype=float)

    def solve(self) -> SolveResult:
        varmap = _VarMap(self.doc)
        num_vars = varmap.size
        num_equations = sum(len(residuals(self.doc, c)) for c in self.constraints)

        if num_vars == 0:
            return SolveResult("empty", True, 0.0, 0, message="Nothing to solve")

        x0 = varmap.pack()

        try:
            result = least_squares(
                self._residual_vector, x0, args=(varmap,), method="lm", max_nfev=2000
            )
        except Exception as exc:  # noqa: BLE001 — surface as a solve error, not a crash
            varmap.unpack(x0)  # restore original state
            return SolveResult("error", False, float("nan"), num_vars, message=str(exc))

        varmap.unpack(result.x)
        residual_norm = float(np.linalg.norm(result.fun)) if result.fun.size else 0.0

        if residual_norm > 1e-3 and num_equations >= num_vars:
            return SolveResult(
                "over_constrained",
                False,
                residual_norm,
                0,
                conflicting_constraints=[c.id for c in self.constraints],
                message="Constraints are inconsistent — the solver could not satisfy them all.",
            )

        rank = int(np.linalg.matrix_rank(result.jac)) if result.jac.size else 0
        dof_remaining = max(num_vars - rank, 0)
        fully_constrained = dof_remaining == 0 and residual_norm <= RESIDUAL_TOLERANCE * max(num_equations, 1)

        return SolveResult(
            status="solved" if fully_constrained else "under_constrained",
            is_fully_constrained=fully_constrained,
            residual_norm=residual_norm,
            dof_remaining=dof_remaining,
        )

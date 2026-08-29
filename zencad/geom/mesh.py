"""Compact indexed-mesh extraction from ZenCad BRep shapes."""

from dataclasses import dataclass
import math

from OCP.BRep import BRep_Tool
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
from OCP.BRepLib import BRepLib_ToolTriangulatedShape
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepTools import BRepTools
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS


__all__ = ["MeshData", "to_mesh"]


@dataclass
class MeshData:
    """GPU-friendly indexed triangles with split normals and face provenance."""

    positions: list
    normals: list
    triangles: list
    triangle_face_ids: list
    dropped_triangles: int = 0

    @property
    def vertex_count(self):
        return len(self.positions)

    @property
    def triangle_count(self):
        return len(self.triangles)


def _distance_squared(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3))


def _triangle_area_squared(a, b, c):
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cross = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    return sum(component * component for component in cross)


def to_mesh(
    shape,
    linear_deflection=0.5,
    angular_deflection=0.6,
    crease_angle=math.radians(32),
    relative=False,
    parallel=True,
    weld_tolerance=None,
):
    """Return a deterministic compact mesh for a ZenCad shape.

    OCCT produces a separate triangulation for every BRep face.  This function
    transforms those triangulations to world space, computes normals from the
    source CAD surfaces, and welds coincident nodes only where their normals
    satisfy ``crease_angle``.  Sharp edges therefore remain split while smooth
    seams share vertices.
    """
    if not math.isfinite(linear_deflection) or linear_deflection <= 0:
        raise ValueError("linear_deflection must be finite and positive")
    if not math.isfinite(angular_deflection) or angular_deflection <= 0:
        raise ValueError("angular_deflection must be finite and positive")
    if not math.isfinite(crease_angle) or not 0 <= crease_angle <= math.pi:
        raise ValueError("crease_angle must be finite and between zero and pi")
    if weld_tolerance is None:
        weld_tolerance = max(1e-9, linear_deflection * 1e-6)
    if not math.isfinite(weld_tolerance) or weld_tolerance <= 0:
        raise ValueError("weld_tolerance must be finite and positive")

    source = shape.unlazy() if hasattr(shape, "unlazy") else shape

    # Work on a copy so a coarse request stays deterministic when the source
    # was previously triangulated more finely for display or STL export.
    copied = BRepBuilderAPI_Copy(source.Shape()).Shape()
    BRepTools.Clean_s(copied)
    mesher = BRepMesh_IncrementalMesh(
        copied,
        linear_deflection,
        relative,
        angular_deflection,
        parallel,
    )
    if not mesher.IsDone():
        raise RuntimeError("OCCT failed to triangulate the shape")

    cosine_crease = math.cos(crease_angle)
    tolerance_squared = weld_tolerance * weld_tolerance
    area_epsilon_squared = tolerance_squared * tolerance_squared

    positions = []
    reference_normals = []
    normal_sums = []
    buckets = {}
    triangles = []
    triangle_face_ids = []
    dropped_triangles = 0

    def vertex_index(position, normal):
        key = tuple(math.floor(component / weld_tolerance) for component in position)
        candidates = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    candidates.extend(
                        buckets.get((key[0] + dx, key[1] + dy, key[2] + dz), ())
                    )

        # Keep the choice deterministic when more than one existing vertex is
        # within tolerance, regardless of its spatial bucket.
        candidates.sort()
        for index in candidates:
            dot = sum(normal[i] * reference_normals[index][i] for i in range(3))
            if (
                dot >= cosine_crease
                and _distance_squared(position, positions[index]) <= tolerance_squared
            ):
                normal_sums[index] = tuple(
                    normal_sums[index][i] + normal[i] for i in range(3)
                )
                return index

        index = len(positions)
        positions.append(position)
        reference_normals.append(normal)
        normal_sums.append(normal)
        buckets.setdefault(key, []).append(index)
        return index

    explorer = TopExp_Explorer(copied, TopAbs_FACE)
    face_id = 0
    while explorer.More():
        face = TopoDS.Face(explorer.Current())
        location = TopLoc_Location()
        triangulation = BRep_Tool.Triangulation_s(face, location)
        if triangulation is None:
            explorer.Next()
            face_id += 1
            continue

        BRepLib_ToolTriangulatedShape.ComputeNormals_s(face, triangulation)
        transform = location.Transformation()
        reversed_face = face.Orientation() == TopAbs_REVERSED
        local_indices = []

        for node_index in range(1, triangulation.NbNodes() + 1):
            point = triangulation.Node(node_index).Transformed(transform)
            direction = triangulation.Normal(node_index).Transformed(transform)
            normal = (direction.X(), direction.Y(), direction.Z())
            if reversed_face:
                normal = tuple(-component for component in normal)
            position = (point.X(), point.Y(), point.Z())
            local_indices.append(vertex_index(position, normal))

        for triangle_index in range(1, triangulation.NbTriangles() + 1):
            a, b, c = triangulation.Triangle(triangle_index).Get()
            if reversed_face:
                a, b = b, a
            triangle = (
                local_indices[a - 1],
                local_indices[b - 1],
                local_indices[c - 1],
            )
            if len(set(triangle)) != 3 or _triangle_area_squared(
                positions[triangle[0]],
                positions[triangle[1]],
                positions[triangle[2]],
            ) <= area_epsilon_squared:
                dropped_triangles += 1
                continue
            triangles.append(triangle)
            triangle_face_ids.append(face_id)

        explorer.Next()
        face_id += 1

    normals = []
    for index, normal in enumerate(normal_sums):
        length = math.sqrt(sum(component * component for component in normal))
        if length <= 1e-15:
            normal = reference_normals[index]
            length = math.sqrt(sum(component * component for component in normal))
        normals.append(tuple(component / length for component in normal))

    return MeshData(
        positions=positions,
        normals=normals,
        triangles=triangles,
        triangle_face_ids=triangle_face_ids,
        dropped_triangles=dropped_triangles,
    )

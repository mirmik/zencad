#!/usr/bin/env python3
"""Minimal cadquery-ocp compatibility probe for the ZenCad migration."""

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

import OCP
from OCP.AIS import AIS_InteractiveContext, AIS_Shape  # noqa: F401
from OCP.Aspect import Aspect_DisplayConnection  # noqa: F401
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeSphere
from OCP.GProp import GProp_GProps
from OCP.Graphic3d import Graphic3d_GraphicDriver  # noqa: F401
from OCP.gp import gp_Pnt, gp_Trsf, gp_Vec
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS_Shape
from OCP.V3d import V3d_Viewer  # noqa: F401


def load_occ_compat():
    path = Path(__file__).parents[1] / "zencad" / "occ_compat.py"
    spec = importlib.util.spec_from_file_location("zencad_occ_compat", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    compat = load_occ_compat()
    box = BRepPrimAPI_MakeBox(10.0, 20.0, 30.0).Shape()
    sphere = BRepPrimAPI_MakeSphere(
        gp_Pnt(10.0, 10.0, 15.0), 8.0
    ).Shape()

    translation = gp_Trsf()
    translation.SetTranslation(gp_Vec(1.0, 2.0, 3.0))
    moved_box = BRepBuilderAPI_Transform(box, translation, True).Shape()

    fuse = BRepAlgoAPI_Fuse(moved_box, sphere)
    fuse.Build()
    assert fuse.IsDone()
    result = fuse.Shape()
    assert not result.IsNull()

    faces = []
    explorer = TopExp_Explorer(result, TopAbs_FACE)
    while explorer.More():
        faces.append(compat.as_face(explorer.Current()))
        explorer.Next()
    assert faces

    properties = GProp_GProps()
    compat.volume_properties(result, properties)
    assert properties.Mass() > 0

    with TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / "shape.brep"
        assert compat.write_brep(result, path)

        loaded = TopoDS_Shape()
        assert compat.read_brep(loaded, path)
        assert not loaded.IsNull()

    try:
        BRepPrimAPI_MakeBox(0.0, 2.0, 3.0).Shape()
    except Exception as exception:
        assert isinstance(exception, compat.Standard_DomainError)
    else:
        raise AssertionError("Expected Standard_DomainError")

    print(f"OCP {OCP.__version__}")
    print(f"faces: {len(faces)}")
    print(f"volume: {properties.Mass()}")
    print("cadquery-ocp compatibility spike: OK")


if __name__ == "__main__":
    main()

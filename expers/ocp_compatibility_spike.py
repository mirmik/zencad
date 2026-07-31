#!/usr/bin/env python3
"""Minimal cadquery-ocp compatibility probe for the ZenCad migration."""

from pathlib import Path
from tempfile import TemporaryDirectory

import OCP
from OCP.AIS import AIS_InteractiveContext, AIS_Shape  # noqa: F401
from OCP.Aspect import Aspect_DisplayConnection  # noqa: F401
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepGProp import BRepGProp
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeSphere
from OCP.BinTools import BinTools
from OCP.GProp import GProp_GProps
from OCP.Graphic3d import Graphic3d_GraphicDriver  # noqa: F401
from OCP.gp import gp_Pnt, gp_Trsf, gp_Vec
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.V3d import V3d_Viewer  # noqa: F401


def main():
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
        faces.append(TopoDS.Face(explorer.Current()))
        explorer.Next()
    assert faces

    properties = GProp_GProps()
    BRepGProp.VolumeProperties_s(result, properties)
    assert properties.Mass() > 0

    with TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / "shape.brep"
        assert BinTools.Write_s(result, str(path))

        loaded = TopoDS_Shape()
        assert BinTools.Read_s(loaded, str(path))
        assert not loaded.IsNull()

    try:
        BRepPrimAPI_MakeBox(0.0, 2.0, 3.0).Shape()
    except Exception as exception:
        assert type(exception).__name__ == "Standard_DomainError"
    else:
        raise AssertionError("Expected Standard_DomainError")

    print(f"OCP {OCP.__version__}")
    print(f"faces: {len(faces)}")
    print(f"volume: {properties.Mass()}")
    print("cadquery-ocp compatibility spike: OK")


if __name__ == "__main__":
    main()

# Topologically dependent transformations

There is a class of operations required as part of the model topology. In interactive CAD, we can, using the mouse pointer, point to such an element and point it as a guide. This method is not available in scripted CAD. One approach of ZenCad is that such an element is specified using the "closest point" method. When specifying an argument, a point is specified instead of a topology element. The selected element is the element, the distance to which from the specified point will be minimal.

Fillets, chamfers and drafts require selecting model topology. Use [geometric selectors](selectors.html) or pass edges and faces directly. Fillets and chamfers also accept reference points, selecting the nearest topology element.

---
## Fillet
Body rounding operation.
If the body is solid, the edges are modified. If flat - tops.
Fillets are specified by radius `r` and an array of nearest points`refs`. If `refs == None`, all elements of the topology are considered selected.

```python
fillet(model, radius, referencedPoints)
fillet(model, radius)
model.fillet(radius, referencedPoints)
model.fillet(radius)
```
![](../images/generic/fillet0.png) ![](../images/generic/fillet1.png) </br>
![](../images/generic/fillet2.png) ![](../images/generic/fillet3.png) </br>
![](../images/generic/fillet4.png) ![](../images/generic/fillet5.png)  

---
## Chamfer
Body chamfering operation. Unlike rounding, it is applied only to solid bodies.
The chamfer is specified by the distance `r` taken from the edge to the chamfer line and an array of the nearest points` refs`. If `refs == None`, all elements of the topology are considered selected.


```python
chamfer(model, radius, referencedPoints)
```
![](../images/generic/chamfer0.png) ![](../images/generic/chamfer1.png) </br>
![](../images/generic/chamfer2.png) ![](../images/generic/chamfer3.png)

---
## Face draft

`draft` inclines selected faces around a neutral plane, commonly so a molded
part can be released from its tooling. A positive angle removes material along
the pull direction; a negative angle adds it. The neutral plane remains fixed.

The pull direction defaults to `+Z`, with an origin plane perpendicular to it.
`neutral` also accepts a planar face or an `(origin, normal)` pair. Selected
faces must belong to the source body and be planar, cylindrical, or conical.

```python
body = box(20)
side_faces = body.faces().filter_by_position(Axis.Z, 10)

narrower = draft(body, side_faces, deg(5))
wider = draft(body, side_faces, deg(-5))
midplane = draft(
    body,
    side_faces,
    deg(5),
    neutral=((0, 0, 10), (0, 0, 1)),
)
```

---
## Thicksolid
The operation of creating a thin-walled volumetric body.
Defined by the prototype model `shp` and an array of points closest to the removed faces` refs`.
The wall thickness `t` is also specified. If the wall thickness is positive, the walls grow outward. If negative - inward.

```python
thicksolid(model, t=thickness, refs=referencedPoints)
```

![](../images/generic/thicksolid0.png) ![](../images/generic/thicksolid1.png)

## Result type and references

`fillet()` and `chamfer()` return `Shape`; inspect their contents using `faces()` and `solids()`. The result handle remains `Shape` even when it contains one solid.

Pass a list of `point3(...)` or `Vertex` values to select nearby elements, or a list of `Edge` objects from the original body to select edges explicitly. Do not mix edges and points. Plain numeric tuples inside the reference list are not supported; use `point3`. `None` selects all elements, while an empty list raises `ValueError`. Edges from another model are rejected. For a planar face fillet, select vertices or points.

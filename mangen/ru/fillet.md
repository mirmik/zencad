:ru
# Топологически зависимые преобразования

Скругление, фаска и уклон требуют выбора элементов топологии модели. Их можно выбирать по геометрическим свойствам через [селекторы](selectors.html) или передавать сами рёбра и грани. Для скруглений и фасок поддерживаются также ближайшие точки: выбирается элемент с минимальным расстоянием до точки.
:en
# Topologically dependent transformations

Fillets, chamfers and drafts require selecting model topology. Use [geometric selectors](selectors.html) or pass edges and faces directly. Fillets and chamfers also accept reference points, selecting the nearest topology element.
::

---
:ru
## Fillet
Операция скругления тела. 
Если тело объёмное - модификации подвергаются ребра. Если плоское - вершины.
Скругления задаются радиусом `r` и масивом ближайших точек `refs`. Если `refs == None`, выбранными считаются все элементы топологии. 
:en
## Fillet
Body rounding operation.
If the body is solid, the edges are modified. If flat - tops.
Fillets are specified by radius `r` and an array of nearest points`refs`. If `refs == None`, all elements of the topology are considered selected. 
::

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
:ru
## Chamfer
Операция взятия фаски тела. В отличие от скругления применяется только к объёмным телам.
Фаска задаётся расстоянием `r`, взятым от ребра до линии фаски и масивом ближайших точек `refs`. Если `refs == None`, выбранными считаются все элементы топологии. 

TODO: несиметричная фаска. 
:en
## Chamfer
Body chamfering operation. Unlike rounding, it is applied only to solid bodies.
The chamfer is specified by the distance `r` taken from the edge to the chamfer line and an array of the nearest points` refs`. If `refs == None`, all elements of the topology are considered selected.

TODO: asymmetrical chamfer. 
::

```python
chamfer(model, radius, referencedPoints)
```
![](../images/generic/chamfer0.png) ![](../images/generic/chamfer1.png) </br>
![](../images/generic/chamfer2.png) ![](../images/generic/chamfer3.png)

---
:ru
## Уклон граней (Draft)

`draft` наклоняет выбранные грани относительно нейтральной плоскости. Это
нужно, например, чтобы деталь извлекалась из пресс-формы. Положительный угол
снимает материал по направлению вытяжки, отрицательный — добавляет. Нейтральная
плоскость остаётся неподвижной.

По умолчанию направление равно `+Z`, а нейтральная плоскость проходит через
начало координат перпендикулярно направлению. `neutral` также принимает плоскую
грань или пару `(origin, normal)`. Выбранные грани должны принадлежать исходному
телу и быть плоскими, цилиндрическими или коническими.
:en
## Face draft

`draft` inclines selected faces around a neutral plane, commonly so a molded
part can be released from its tooling. A positive angle removes material along
the pull direction; a negative angle adds it. The neutral plane remains fixed.

The pull direction defaults to `+Z`, with an origin plane perpendicular to it.
`neutral` also accepts a planar face or an `(origin, normal)` pair. Selected
faces must belong to the source body and be planar, cylindrical, or conical.
::

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
:ru
## Thicksolid
Операция создания тонкостенного объёмного тела.
Задаётся прототипной моделью `shp` и массивом точек, ближайших к удаляемым граням `refs`.
Также задаётся толщина стенок `t`. Если толщина стенок положительная, стенки наращиваются наружу. Если отрицательная - внутрь.
:en
## Thicksolid
The operation of creating a thin-walled volumetric body.
Defined by the prototype model `shp` and an array of points closest to the removed faces` refs`.
The wall thickness `t` is also specified. If the wall thickness is positive, the walls grow outward. If negative - inward. 
::

```python
thicksolid(model, t=thickness, refs=referencedPoints)
```

![](../images/generic/thicksolid0.png) ![](../images/generic/thicksolid1.png)

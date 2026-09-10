# Planar primitives
This section covers planar primitives. They are usually combined with 3D operations to build solids with complex geometry.

---
## Rectangle
A rectangle is defined by two side lengths. Omit the second length to build a square. The _center_ option places its geometric center at the origin. With _wire_, the result is a rectangular wire instead of a filled face.

Signature:
```python
rectangle(x, y, center=False, wire=False)
rectangle(a, center=False, wire=False)
square(a, center=False, wire=False) #alternate
```
![](../images/generic/rectangle0.png) ![](../images/generic/rectangle1.png) </br>
![](../images/generic/rectangle2.png) ![](../images/generic/rectangle3.png)

---
## Circle and disk
A circle is defined by its radius _r_. The optional _angle_ parameter creates a sector or an arc.
With _wire_, the result is a circular wire instead of a filled disk.

Signature:
```python
circle(r=radius, wire=False)
circle(r=radius, angle=angle, wire=False)
circle(r=radius, angle=(start, stop), wire=False)
```
![](../images/generic/circle0.png) ![](../images/generic/circle1.png) </br>
![](../images/generic/circle2.png) ![](../images/generic/circle3.png)

---
## Ellipse
An ellipse is defined by two radii, with _r1_ greater than _r2_. To build a sector, pass an angle or a pair of angles as the optional _angle_ parameter.
With _wire_, the result is a wire instead of a filled face.

Signature:
```python
ellipse(r1=major, r2=minor, wire=False)
ellipse(r1=major, r2=minor, angle=angle, wire=False)
ellipse(r1=major, r2=minor, angle=(start, stop), wire=False)
```
![](../images/generic/ellipse0.png) ![](../images/generic/ellipse1.png) </br>
![](../images/generic/ellipse2.png) ![](../images/generic/ellipse3.png)

---
## Polygon
A polygon is defined by its vertices. With _wire_, the result is a wire instead of a filled face, equivalent to a closed polysegment.
_pnts_ is an array of vertex coordinates.

Signature:
```python
polygon(points=pnts, wire=False)
```
![](../images/generic/polygon0.png) ![](../images/generic/polygon1.png)

---
## Regular polygon
A regular polygon is defined by its radius and number of vertices.
With _wire_, the result is a wire instead of a filled face.

Signature:
```python
ngon(r=radius, n=vertexCount, wire=False)
```
![](../images/generic/ngon0.png) ![](../images/generic/ngon1.png) </br>
![](../images/generic/ngon2.png) ![](../images/generic/ngon3.png) </br>
![](../images/generic/ngon4.png) ![](../images/generic/ngon5.png)

---
## Text
Returns a `Compound` of character faces from the string `text`, font name `fontname` and font size `size`. The font is selected from those registered in the system. Use `register_font` to register additional fonts. The `composite_curve` option reduces the number of constituent objects by increasing their complexity.

Signature:
```python
textshape(text, fontname, size, composite_curve=False)
```
![](../images/generic/textshape0.png) ![](../images/generic/textshape1.png)

---
## Infinite plane
An infinite plane is a special geometric object used in operations on other objects.
It cannot be displayed directly.

Signature:
```python
infplane()
```

Example (conic sections):
```python
cone(r1=5, r2=0, h=10, center=True) ^ infplane()
cone(r1=5, r2=0, h=10, center=True).rotX(deg(45)) ^ infplane()
cone(r1=5, r2=0, h=10, center=True) ^ infplane().rotX(deg(45))
cone(r1=5, r2=0, h=10, center=True) ^ infplane().rotX(deg(90)).right(3)
```
![](../images/generic/infplane01.png) ![](../images/generic/infplane0.png) </br>
![](../images/generic/infplane1.png) ![](../images/generic/infplane2.png)

----------------------------------
## Filling a wire
This operation turns a closed planar _wire_ into a face.

Signature:
```python
fill(wire)
wire.fill() #alternate
```

Example:
```python
wire = sew([
	segment((0,0,0), (0,10,0)), 
	circle_arc((0,10,0),(10,15,0),(20,10,0)), 
	segment((20,0,0), (20,10,0)),
	segment((20,0,0), (0,0,0))
])
fill(wire)
```

|Before|After|
|--|--|
|![](../images/generic/fill0.png)|![](../images/generic/fill1.png)|

----------------------------------
## Interpolating a surface through a grid of points
Builds a B-spline surface by interpolating a two-dimensional array of points, supplied as a nested list.
`degmin` and `degmax` set the minimum and maximum degree of the interpolation polynomial.

Signature:
```python
interpolate2(pnts, degmin=3, degmax=7)
```

Example:
```python
POINTS = points2([
		[(0,0,0), (10,0,7), (20,0,5)],
		[(0,5,0), (10,5,7.5), (20,5,7)],
		[(0,10,2), (10,10,8), (20,10,5)],
		[(0,15,1.3), (10,15,8.5), (20,15,6)],
	])

m = interpolate2(POINTS)
disp(m)
disp(POINTS, color=color.red)
```

![](../images/generic/interpolate20.png)

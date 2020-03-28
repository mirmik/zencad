# Solid shapes.
This section provides basic CSG geometry primitives.

---
## Box.  
Box shape. It is specified with three sizes _x_, _y_, _z_. When specifying a single size _a_, a cube _(a, a, a)_ is generated. Setting the boolean option _center_ combines the geometric center of the body with the origin.

Signature:
```python
box(x, y, z, center=True/False)
box(size=(x,y,z), center=True/False)
box(size=a, center=True/False) 
```

Examples:
```python
box(10, 20, 30, center=False)
box(size=(10,20,30), center=False) # alternate
box(10, center=True)
```
![box0.png](../images/generic/box0.png)
![box1.png](../images/generic/box1.png)

---
## Sphere.
Sphere shape. _r_ is radius. It is possible to build a sector of the sphere using the optional parameters _yaw_, _pitch_.

Signature:
```python
sphere(r=radius, yaw=yaw, pitch=(minPitch, maxPitch))
```

Examples:
```python
sphere(10)
sphere(10, yaw=math.pi*2/3)
sphere(10, pitch=(deg(20), deg(60)))
sphere(10, yaw=deg(120), pitch=(deg(20), deg(60)))
```
![](../images/generic/sphere0.png)
![](../images/generic/sphere1.png)  
![](../images/generic/sphere2.png)
![](../images/generic/sphere3.png)  

---
## Cylinder.
Cylinder shape. Set with radius and height. It is possible to build a cylinder sector using the optional parameter _yaw_. Setting the _center_ option aligns the geometric center of the body with the origin.

Signature:
```python
cylinder(r=radius, h=height, yaw=yaw, center=True/False)
```

Examples:
```python
cylinder(r=10, h=20)
cylinder(r=10, h=20, yaw=deg(45))
cylinder(r=10, h=20, center=True)
cylinder(r=10, h=20, yaw=deg(45), center=True)
```

![](../images/generic/cylinder0.png)
![](../images/generic/cylinder1.png)  
![](../images/generic/cylinder2.png)
![](../images/generic/cylinder3.png)

---
## Cone.
Cone shape. Set with the lower radius _r1_, upper radius _r2_ and height. It is possible to build a cone sector using the optional parameter _yaw_. Setting the _center_ option aligns the geometric center of the body with the origin. Radii _r1_ and _r2_ can be zero, which corresponds to a pointed cone.

Signature:
```python
cone(r1=botRadius, r2=topRadius, h=height, yaw=yaw, center=True/False)
```

Examples:
```python
cone(r1=20, r2=10, h=20)
cone(r1=20, r2=10, h=20, yaw=deg(45))
cone(r1=0, r2=20, h=20)
cone(r1=20, r2=0, h=20, center=True)
```

![](../images/generic/cone0.png)
![](../images/generic/cone1.png)  
![](../images/generic/cone2.png)
![](../images/generic/cone3.png)  

---
## Torus. 
Torus shape. Set with the indication of the central radius _r1_ and the local radius _r2_. It is possible to build torus sectors using the optional parameters _yaw_, _pitch_.

In the case where the angle interval _pitch_ does not contain an inner region, a corresponding cylindrical insert is formed in the center. If the angle interval _pitch_ does not contain an outer region, the corresponding part of the torus is limited by a plane.

Signature:
```python
torus(r1=centralRadius, r2=localRadius, yaw=yaw, pitch=(minPitch, maxPitch))
```

Examples:
```python
torus(r1=20, r2=5)
torus(r1=20, r2=5, yaw=deg(120))
torus(r1=20, r2=5, pitch=(deg(-20), deg(120)))
torus(r1=20, r2=5, pitch=(deg(-20), deg(120)), yaw=deg(120))
torus(r1=20, r2=5, pitch=(deg(-140), deg(140)), yaw=deg(120))
torus(r1=20, r2=5, pitch=(deg(-20), deg(190)), yaw=deg(120))
```

![](../images/generic/torus0.png)
![](../images/generic/torus1.png)  
![](../images/generic/torus2.png)
![](../images/generic/torus3.png)  
![](../images/generic/torus4.png)
![](../images/generic/torus5.png)  

---
## Halfspace.
Special volumetric body representing the lower half-space. Like other volumetric bodies, it supports transformations and using them can represent any possible half-space. Unlike ordinary bodies, it cannot be displayed directly. Used with difference and intersection operations.

Signatures:
```python
halfspace()
```

Examples:
```python
sphere(r=10) - halfspace().rotateX(deg(150))
sphere(r=10) ^ halfspace().rotateX(deg(150))
```
![](../images/generic/halfspace0.png)
![](../images/generic/halfspace1.png)  

--------------------
## Platonic solids

Library based on https://github.com/qalle2/plato.scad

|Regular polyhedron|Number of vertices|Number of edges|Number of faces|Number of edges at the face|Number of edges adjacent to the vertex|Type of spatial symmetry|
|---|---|---|---|---|---|---|
|Tetrahedron|4|6|4|3|3|Td|
|Hexahedron|8|12|6|4|3|Oh|
|Oktohedron|6|12|8|3|4|Oh|
|Dodecahedron|20|30|12|5|3|Ih|
|Icosahedron|12|30|20|3|5|Ih|

The library allows you to specify the dimensions of the bodies through the radius of the circumscribed circle _r_ or through the length of the rib _a_.

Signatures:
```python
zencad.tetrahedron(r=1, a=None, shell=False)
zencad.hexahedron(r=1, a=None, shell=False)
zencad.octahedron(r=1, a=None, shell=False)
zencad.dodecahedron(r=1, a=None, shell=False)
zencad.icosahedron(r=1, a=None, shell=False)

# Альтернативный синтаксис
zencad.platonic(nfaces, r=1, a=None, shell=False)
```

Example:
```python
# Через радиус:
tetrahedron(10)
hexahedron(10)
octahedron(r=10)
dodecahedron(r=10)
icosahedron(10)

# Через длину ребра:
icosahedron(a=10)

# Альтернативный синтакис:
zencad.platonic(4, 10)
zencad.platonic(6, 10)
zencad.platonic(8, 10)
zencad.platonic(12, 10)
zencad.platonic(20, 10)
```

![](../images/generic/platonic0.png)
![](../images/generic/platonic1.png)  
![](../images/generic/platonic2.png)
![](../images/generic/platonic3.png)  
![](../images/generic/platonic4.png)

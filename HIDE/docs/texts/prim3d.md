---
layout : default
---

# 3d Примитивы

## Box  
```python
box(x, y, z, center = True/False);
box(size = (x,y,z), center = True/False);
box(size = x, center = True/False);
```

Example:
```python
zencad.box(size = [20, 20, 10], center = True)
```
![box.png](../images/box.png)

## Sphere  
```python
sphere(r = radius)
```

Example:
```python
zencad.sphere(r = 10)
```
![sphere.png](../images/sphere.png)

## Cylinder  
```python
cylinder(r = radius, h = height, center = True/False);
```

Example:
```python
zencad.cylinder(r = 10, h = 20)
zencad.cylinder(r = 10, h = 20, angle=50)
```

![cylinder.png](../images/cylinder.png)![cylinder_sector.png](../images/cylinder_sector.png)

## Cone  
```python
cone(r1 = botRadius, r2 = topRadius, h = height, center = True/False);
```

Example:
```python
zencad.cone(r1 = 20, r2 = 10, h = 20, center = True)
```
![cone.png](../images/cone.png)

## Torus  
```python
torus(r1 = centralRadius, r2 = localRadius);
```

Example:
```python
zencad.torus(r1 = 10, r2 = 3);
```
![torus.png](../images/torus.png)
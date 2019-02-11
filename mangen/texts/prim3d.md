# Объёмные тела.
В этом разделе приводятся базовые примитивы CSG геометрии.

---
## Box  
Объёмное тело - параллелипипед. Задаётся с указанием трёх размеров. При указании одного размера `a` генерируется куб `(a,a,a)`. Установка опции center совмещает геометрический центр тела с началом координат.

Варианты использования.
```python
box(x, y, z, center=True/False);
box(size=(x,y,z), center=True/False);
box(size=x, center=True/False);
```
![box.png](images/generic/box.png)

---
## Sphere  
Объёмное тело - сфера. Задаётся с указанием радиуса. Возможно построение сектора сферы с использованием параметров yaw, pitch.
```python
sphere(r=radius)
sphere(r=radius, yaw=yaw)
sphere(r=radius, pitch=(minPitch, maxPitch))
sphere(r=radius, yaw=yaw, pitch=(minPitch, maxPitch))
```
![](images/generic/sphere0.png)
![](images/generic/sphere1.png)  
![](images/generic/sphere2.png)
![](images/generic/sphere3.png)  

---
## Cylinder  
Объёмное тело - цилиндр. Задаётся с указанием радиуса и высоты. Возможно построение сектора цилиндра с использованием параметра yaw. Установка опции center совмещает геометрический центр тела с началом координат.

```python
cylinder(r=radius, h=height, center = True/False)
cylinder(r=radius, h=height, yaw=yaw, center = True/False)
```

![](images/generic/cylinder0.png)
![](images/generic/cylinder1.png)  

---
## Cone  
Объёмное тело - конус. Задаётся с указанием нижнего радиуса, верхнего радиуса и высоты. Возможно построение сектора цилиндра с использованием параметра yaw. Установка опции center совмещает геометрический центр тела с началом координат.
```python
cone(r1=botRadius, r2=topRadius, h=height, center=True/False);
cone(r1=botRadius, r2=topRadius, h=height, yaw=yaw, center=True/False);
cone(r1=0, r2=topRadius, h=height, center=True/False);
cone(r1=botRadius, r2=0, h=height, center=True/False);
```

![](images/generic/cone0.png)
![](images/generic/cone1.png)  
![](images/generic/cone2.png)
![](images/generic/cone3.png)  

---
## Torus 
Объёмное тело - тор. Задаётся с указанием нижнего радиуса, верхнего радиуса и высоты. Возможно построение сектора цилиндра с использованием параметра yaw. 
```python
torus(r1=centralRadius, r2=localRadius);
torus(r1=centralRadius, r2=localRadius, yaw=yaw);
torus(r1=centralRadius, r2=localRadius, pitch=(minPitch, maxPitch));
torus(r1=centralRadius, r2=localRadius, yaw=yaw, pitch=(minPitch, maxPitch));
```
![](images/generic/torus0.png)
![](images/generic/torus1.png)  
![](images/generic/torus2.png)
![](images/generic/torus3.png)  
![](images/generic/torus4.png)
![](images/generic/torus5.png)  

---
## Halfspace
Специальное объёмное тело, представляющее собой нижнее полупространство. Так же как и остальные объёмные тела, поддерживает трансформации и с использованием их может представлять любое возможное полупространство. В отличии от обычных тел не может быть отображено непосредственно. Используется вместе с операциями разности и пересечения.
```python
sphere(r=10) - halfspace().rotateX(deg(150))
sphere(r=10) ^ halfspace().rotateX(deg(150))
```
![](images/generic/halfspace0.png)
![](images/generic/halfspace1.png)  

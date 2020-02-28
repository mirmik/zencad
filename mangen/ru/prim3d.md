# Объёмные тела.
В этом разделе приводятся базовые примитивы CSG геометрии.

---
## Параллелепипед.  
Объёмное тело - параллелипипед. Задаётся с указанием трёх размеров _x_, _y_, _z_. При указании одного размера _a_ генерируется куб _(a,a,a)_. Установка булевой опции _center_ совмещает геометрический центр тела с началом координат.

Сигнатуры:
```python
box(x, y, z, center=True/False)
box(size=(x,y,z), center=True/False)
box(size=a, center=True/False) 
```

Примеры:
```python
box(10, 20, 30, center=False)
box(size=(10,20,30), center=False) # alternate
box(10, center=True)
```
![box0.png](../images/generic/box0.png)
![box1.png](../images/generic/box1.png)

---
## Сфера.
Объёмное тело - сфера. Задаётся с указанием радиуса. Возможно построение сектора сферы с использованием необязательных параметров yaw, pitch.

Сигнатура:
```python
sphere(r=radius, yaw=yaw, pitch=(minPitch, maxPitch))
```

Примеры:
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
## Цилиндр.
Объёмное тело - цилиндр. Задаётся с указанием радиуса и высоты. Возможно построение сектора цилиндра с использованием необязательного параметра _yaw_. Установка опции _center_ совмещает геометрический центр тела с началом координат.

Сигнатура:
```python
cylinder(r=radius, h=height, yaw=yaw, center=True/False)
```

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
## Конус.
Объёмное тело - конус. Задаётся с указанием нижнего радиуса _r1_, верхнего радиуса _r2_ и высоты. Возможно построение сектора конуса с использованием необязательного параметра _yaw_. Установка опции _center_ совмещает геометрический центр тела с началом координат. Радиусы _r1_ и _r2_ могут равняться нулю, что соответствует остроконечному конусу.

Сигнатура:
```python
cone(r1=botRadius, r2=topRadius, h=height, yaw=yaw, center=True/False)
```

Примеры:
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
## Тор. 
Объёмное тело - тор. Задаётся с указанием центрального радиуса _r1_ и локального радиуса _r2_. Возможно построение секторов тора с использованием необязательных параметров _yaw_, _pitch_. 

В случае, если интервал угла _pitch_ не содержит внутренней области, в центре образуется соответствующая цилиндрическая вставка. Если интервал угла _pitch_ не содержит внешней области, соответствующая часть тора ограничивается плоскостью.

Сигнатура:
```python
torus(r1=centralRadius, r2=localRadius, yaw=yaw, pitch=(minPitch, maxPitch))
```

Примеры:
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
## Полупространство.
Специальное объёмное тело, представляющее собой нижнее полупространство. Так же как и остальные объёмные тела, поддерживает трансформации и с использованием их может представлять любое возможное полупространство. В отличии от обычных тел не может быть отображено непосредственно. Используется вместе с операциями разности и пересечения.
```python
sphere(r=10) - halfspace().rotateX(deg(150))
sphere(r=10) ^ halfspace().rotateX(deg(150))
```
![](../images/generic/halfspace0.png)
![](../images/generic/halfspace1.png)  

--- 
## Полигедрон
Объёмное тело, состоящее из полских граней, заданное точками вершин _pnts_ и массивом кортежей индексов точек, задающих грани.

Сигнатура:
```python
polyhedron(pnts, faces, shell=False)
```
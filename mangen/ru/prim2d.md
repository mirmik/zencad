# Плоские примитивы.
В этом разделе приводятся плоские примитивы. Обычно они используются совместно с 3д операциями для построения тел со сложной геометрией.

---
## Прямоугольник
Плоский примитив - прямоугольник. Задаётся двумя сторонами. Допустимо не указывать вторую сторону, что будет соответствовать построению квадрата. Установка опции _center_ совмещает геометрический центр тела с началом координат. При установке опции _wire_ вместо залитой грани будет сгенерирован цикл прямоугольника.

Сигнатура:
```python
rectangle(x, y, center=True/False, wire=True/False)
rectangle(a, center=True/False, wire=True/False)
square(a, center=True/False, wire=True/False) #alternate
```
![](../images/generic/rectangle0.png)
![](../images/generic/rectangle1.png)  
![](../images/generic/rectangle2.png)
![](../images/generic/rectangle3.png)  

---
## Окружность/Круг
Окружность задаётся радиусом _r_. Установка необязательной опции _angle_ позволяет сгенерировать сектор круга / дугу окружности.
При установке опции _wire_ вместо залитой грани круга будет сгенерирована каркасная окружность.

Сигнатура:
```python
circle(r=radius, wire=True/False)
circle(r=radius, angle=angle, wire=True/False)
circle(r=radius, angle=(start, stop), wire=True/False)
```
![](../images/generic/circle0.png)
![](../images/generic/circle1.png)  
![](../images/generic/circle2.png)
![](../images/generic/circle3.png)  

---
## Элипс
Плоский примитив - эллипс. Задаётся двумя радиусами, причем _r1_ должен быть больше _r2_. Также можно построить сектор, указав угол или пару углов как необязательный параметр _angle_.
При установке опции _wire_ вместо залитой грани будет сгенерирован каркас.

Сигнатура:
```python
ellipse(r1=major, r2=minor, wire=True/False)
ellipse(r1=major, r2=minor, angle=angle, wire=True/False)
ellipse(r1=major, r2=minor, angle=(start, stop), wire=True/False)
```
![](../images/generic/ellipse0.png)
![](../images/generic/ellipse1.png)  
![](../images/generic/ellipse2.png)
![](../images/generic/ellipse3.png)  

---
## Полигон
Плоский примитив - полигон. Строится по точкам вершин.
При установке опции _wire_ вместо залитой грани будет сгенерирован каркас (что аналогично закрытому полисегменту.).
_pnts_ - массив точек вершин.

Сигнатура:
```python
polygon(pnts=pnts, wire=True/False)
```
![](../images/generic/polygon0.png)
![](../images/generic/polygon1.png)  

---
## Правильный многоугольник
Плоский примитив - правильный многоугольник. Задаются радиус и количество вершин.
При установке опции _wire_ вместо залитой грани будет сгенерирован каркас.

Сигнатура:
```python
ngon(r=radius, n=vertexCount, wire=True/False)
```
![](../images/generic/ngon0.png)
![](../images/generic/ngon1.png)  
![](../images/generic/ngon2.png)
![](../images/generic/ngon3.png)  
![](../images/generic/ngon4.png)
![](../images/generic/ngon5.png)  

---
## Текст
Плоский примитив - текст. Создаёт грань на основе строки и шрифта. Шрифт указывается в виде пути на файл формата ttf (FreeType).

Сигнатура:
```python
textshape(text=textString, fontpath=pathToFont, size=fontSize)
```
![](../images/generic/textshape0.png)
![](../images/generic/textshape1.png)  

---
## Бесконечная плоскость
Бесконечная плоскость - специальный геометрический объект, который может использоваться в некоторых операцих над другими объектами.
Бесконечная плоскость не может быть отображена непосредственно.

Сигнатура:
```python
infplane()
```

Пример (Построение конических сечений):
```python
cone(r1=5, r2=0, h=10, center=True) ^ infplane()
cone(r1=5, r2=0, h=10, center=True).rotX(deg(45)) ^ infplane()
cone(r1=5, r2=0, h=10, center=True) ^ infplane().rotX(deg(45))
cone(r1=5, r2=0, h=10, center=True) ^ infplane().rotX(deg(90)).right(3)
```
![](../images/generic/infplane01.png)
![](../images/generic/infplane0.png)  
![](../images/generic/infplane1.png)
![](../images/generic/infplane2.png)  

----------------------------------
## Заполнение контура
Данная операция применяется к плоской замкнутой линии _wire_ и превращает ее в грань.

Сигнатура:
```python
fill(wire)
wire.fill() #alternate
```

Пример:
```python
wire = sew([
	segment((0,0,0), (0,10,0)), 
	circle_arc((0,10,0),(10,15,0),(20,10,0)), 
	segment((20,0,0), (20,10,0)),
	segment((20,0,0), (0,0,0))
])
fill(wire)
```

|До|После|
|--|--|
|![](../images/generic/fill0.png)|![](../images/generic/fill1.png)|


----------------------------------
## Интерполяция поверхности по массиву точек
Строит bspline поверхность интерполируя 2д массив точек. Масив задаётся двумерным списком.

Сигнатура:
```python
interpolate2(pnts)
```

Пример:
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
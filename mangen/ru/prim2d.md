# Плоские примитивы
В этом разделе приводятся плоские примитивы. Обычно они используются совместно с 3д операциями для построения тел со сложной геометрией.

---
## Rectangle
Плоский примитив - прямоугольник. Задаётся двумя сторонами. Если задать только одну сторону, будет построен квадрат. Установка опции `center` совмещает геометрический центр тела с началом координат. При установке опции `wire` вместо залитой грани будет сгенерирован каркас.

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
## Circle
Плоский примитив - окружность/круг. Задаётся радиусом. Также можно построить сектор, указав угол или пару углов.
При установке опции `wire` вместо залитой грани будет сгенерирован каркас.

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
## Ellipse
Плоский примитив - эллипс. Задаётся двумя радиусами, причем `r1` должен быть больше `r2`. Также можно построить сектор, указав угол или пару углов.
При установке опции `wire` вместо залитой грани будет сгенерирован каркас.

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
## Polygon
Плоский примитив - полигон. Строится по точкам вершин.
При установке опции `wire` вместо залитой грани будет сгенерирован каркас.
`pnts` - массив точек.

```python
polygon(pnts=pnts, wire=True/False)
polygon(pnts=[(0,0), (0,10), (10,0)], wire=True/False)
```
![](../images/generic/polygon0.png)
![](../images/generic/polygon1.png)  

---
## Ngon
Плоский примитив - правильный многоугольник. Задаются радиус и количество вершин.
При установке опции `wire` вместо залитой грани будет сгенерирован каркас.

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
## Textshape
Плоский примитив - текст. Создаёт грань на основе строки и шрифта. Шрифт указывается в виде пути на файл формата ttf (FreeType).

```python
textshape(text=textString, fontpath=pathToFont, size=fontSize)
```
![](../images/generic/textshape0.png)
![](../images/generic/textshape1.png)  


# Преобразования

Парадигма zencad предполагает, что большая часть объектов появляется в точке начала координат, после чего перемещается к месту своего назначения с помощью механизма преобразований. 

---
## Трансляция
Паралельный перенос тела на вектор (x,y,z).
```python
#basic:
model.translate(x,y,z)
model.transform(translate(x,y,z)) #alternate
translate(x,y,z)(model) #alternate

#additional:
model.left(a)	#translate(-a,0,0)
model.right(a)	#translate(a,0,0)
model.back(a)	#translate(0,-a,0)
model.forw(a)	#translate(0,a,0)
model.up(a)		#translate(0,0,-a)
model.down(a)	#translate(0,0,a)
```

---
## Поворот
Поворот тела вокруг оси axis, проходящей через начало координат на угол angle.
```python
#basic:
#model.rotate(angle=angle, axis=(x,y,z))
#model.transform(rotate(angle=angle, axis=(x,y,z)) #alternate
#rotate(angle=angle, axis=(x,y,z))(model) #alternate
TODO

#additional:
model.rotateX(angle) 	#rotate(angle, axis=(1,0,0)
model.rotateY(angle) 	#rotate(angle, axis=(0,1,0)
model.rotateZ(angle) 	#rotate(angle, axis=(0,0,1)
```

---
## Масштабирование
Изменение размера тела на коэффициент a. Может выполняться в направлении заданной оси или изотропно.
```python
#basic:
model.scale(a)

#additional:
model.scaleX(a)
model.scaleY(a)
model.scaleZ(a)
```

---
## Отражение
Операция отражения геометрии относительно заданного объекта (ось или плоскость).
```python
#basic:
TODO

#additional:
model.mirrorX()
model.mirrorY()
model.mirrorZ()
model.mirrorXY()
model.mirrorYZ()
model.mirrorXZ()
```

---
## Преобразование общего вида
TODO
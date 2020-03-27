# Триангуляция и меш

Функции для работы с полигональным представлением.

---
## Триангуляция
Построение полигональной сетки в формате (_nodes_, _triangles_), где _pnts_ - массив точек, а _triangles_ - массив 3-кортежей, индексов точек.
Параметр _deflection_ отвечает за разрешение разбиения. 

Сигнатура:
```python
nodes, triangles = triangulate(shp, deflection)
```

Пример:
```python
m=sphere(10)
nodes, triangles = triangulate(m, 0.1)

print("count_of_nodes:", len(nodes))
print("count_of_triangles:", len(triangles))

print("first_five_nodes:", nodes[:5])
print("first_five_triangles:", triangles[:5])

#count_of_nodes: 699
#count_of_triangles: 1362
#first_five_nodes: [point3(0.000000,-0.000000,10.000000), point3(0.000000,-0.000000,10.000000), point3(0.000000,-0.000000,-10.000000), point3(1.950903,-0.000000,-9.807853), point3(3.826834,-0.000000,-9.238795)]
#first_five_triangles: [[237, 227, 200], [486, 482, 470], [237, 200, 211], [487, 472, 477], [238, 201, 212]]
```

--- 
## Полигедрон
Объёмное тело, состоящее из полских граней, заданное точками вершин _pnts_ и массивом кортежей индексов точек, задающих грани.

Сигнатура:
```python
polyhedron(pnts, faces, shell=False)
```

Пример:
```python
m=sphere(10)
nodes, triangles = triangulate(m, 0.1)
disp(polyhedron(nodes, triangles))
```
![](../images/generic/polyhedron0.png)


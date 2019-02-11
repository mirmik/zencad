# Ссылочная геометрия

## Linear extrude
Операция линейной экструзии. Самый часто используемый метод придания объёма плоскому объекту.
Задаётся плоским объектом `face` и вектором `vec` вдоль которого будет выполнено растяжение. Если вместо вектора указать одну координату, модель будет вытянута в положительном направлении оси Z.
При указании опции center, после выполнения операции модель будет транслирована в направлении обратном vec на его половинную длину.

```python
linear_extrude(shp=face, vec=(x,y,z), center=True/False)
linear_extrude(shp=face, vec=z, center=True/False) #equal: vec=(0,0,z)
model.extrude(vec=(x,y,z), center=True/False)
model.extrude(vec=z, center=True/False)
```
![](images/generic/extrude0.png)
![](images/generic/extrude1.png)  
![](images/generic/extrude2.png)
![](images/generic/extrude3.png)  

---
## Loft
Операция натягивает 3д поверхность на масив каркасных линий `wires`.  
TODO: Добавить больше параметров в алгоритм сглаживания.

```python
loft(wires)
```
![](images/generic/loft0.png)
![](images/generic/loft1.png)  
![](images/generic/loft2.png)
![](images/generic/loft3.png)  
![](images/generic/loft4.png)
![](images/generic/loft5.png)  

---
## Sweep
Операция выдавливания тела `shp` по траектории. В текущей реализации профиль задаётся замкнутым контуром. Путь `traj` задаётся линией. При установке опции frenet меняется алгоритм расчета поворота сечения от поворота траектории. Эту опцию рекомендуется устанавливать для спирального свипа (см. [https://en.wikipedia.org/wiki/Frenet-Serret_formulas](https://en.wikipedia.org/wiki/Frenet%E2%80%93Serret_formulas)).  
```python
sweep(shp=profile, traj=trajectory, frenet=True/False)
```
![](images/generic/sweep0.png)
![](images/generic/sweep1.png)  
![](images/generic/sweep2.png)
![](images/generic/sweep3.png)  
![](images/generic/sweep4.png)

---
## Revol
Операция создания тела вращения. Задаётся с указанием вращаемого тела. При необходимости создания сектора задаётся угол.
```python
revol(shp=model, yaw=angle)
revol(shp=model)
```
![](images/generic/revol0.png)
![](images/generic/revol1.png)  
![](images/generic/revol2.png)
![](images/generic/revol3.png)  

# Рефлексия
Сложные геометрические объекты состоят из более простых. Данная группа функций и методов позволяет расскладывать сложные объекты на образующие их компоненты.

---------------------------
# Массивы базовых объектов
С помощью следующих методов можно извлечь простые объекты, лежащие в основе сложных: 

shape.vertices()  
shape.solids()  
shape.faces()  
shape.edges()  
shape.wires()  
shape.shells()  
shape.compounds()  
shape.compsolids()  

---------------------------------------------------
# Взятие базового объекта по методу ближаёшей точки
Иногда требуется извлечь из сложного объекта конкретный базовый объект. 
В этом случае можно использовать метод базовой точки.  

Следующие функции реализуют метод ближаёшей точке и возвращают ближайший к _pnt_ базовый объект соответствующего типа, принадлежащий сложному объекту _shp_.

near\_edge(shp, pnt)  
near\_face(shp, pnt)  
near\_vertex(shp, pnt)  
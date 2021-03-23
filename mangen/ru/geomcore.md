:ru
# Введение в BREP представление геометрических моделей.
:en
# Introduction to BREP representation of geometric models. 
::


:ru
Библиотека ZenCad основана на функциональных возможностях и объектной структуре геометрического ядра OpenCascade, использующего для работы с геометрическими моделями BREP (boundary representation/граничное представление).

Для более полного понимания работы библиотеки и использования продвинутых функций требуется хотя бы поверхностное понимание BREP и топологической структуры геометрических объектов в используемом геометрическом ядре.
:en
The ZenCad library is based on the functionality and object structure of the OpenCascade geometric kernel, which uses boundary representation (BREP) for working with geometric models.

For a more complete understanding of the library and the use of advanced functions, at least a superficial understanding of the BREP and the topological structure of geometric objects in the geometric kernel used is required. 
::

------------------------------------------------------
:ru
## BREP представление.

Граничное представление (ан. Boundary representation) есть способ представления тел через описание их границ.

Объект в граничном представлении задаётся топологически (с помощью набора ссылок на ограничивающие его объекты) и геометрически (с помощью порождающего его форму геометрического правила). Ограничивающие объекты в свою очередь задаются исходя из тех же соображений.

Так, например, куб является объёмным телом, порождённым внутренним пространством оболочки, образованной 6-ю гранями. Каждая грань геометрически задана уравнением плоскости и ограничена 4-мя объектами рёбер. Каждое ребро геометрически задано уравнением прямой и ограничено двумя вершинами.

В разных библиотеках, использующих BREP представление, разделение на классы объектов может выполняться с определённой спецификой, но общая идея будет неизменной. ZenCad использует систему классов ядра OpenCascade.
:en
## Boundary representation.

Boundary representation is a way of representing bodies by describing their boundaries.

An object in Boundary Representation is defined topologically (using a set of references to its bounding objects) and geometrically (using a geometric rule that shapes its shape). Bounding objects, in turn, are set based on the same considerations.

So, for example, a cube is a volumetric body formed by the inner space of a shell formed by 6 faces. Each face is geometrically defined by a plane equation and is bounded by 4 edge objects. Each edge is geometrically defined by the equation of a straight line and is bounded by two vertices.

In different libraries using the BREP representation, the division of objects into classes can be done with certain specifics, but the general idea will be the same. ZenCad uses the OpenCascade core class system. 
::


------------------------------------------------------
## Классы геометрических объектов.
|ZenCad|OpenCascade|Составной|Мерность|Описание|
|----|---|----|
|Shape|TopoDS\_Shape|неопр.|неопр.|Абстрактный геометрический объект|
|Vertex*|TopoDS\_Vertex|нет|0|Вершина|
|Edge|TopoDS\_Edge|нет|1|Ребро|
|Wire|TopoDS\_Wire|да|1|Сложное ребро|
|Face|TopoDS\_Face|нет|2|Грань|
|Shell|TopoDS\_Shell|да|2|Оболочка|
|Solid|TopoDS\_Solid|нет|3|Твёрдое тело|
|CompSolid|TopoDS\_CompSolid|да|3|Множество твёрдых тел|
|Compound|TopoDS\_Compound|да|неопр.|Составной объект|

>! * В zencad практически всегда вместо Vertex используется эквивалентный объект точки point3. 

------------------------------------------------------
:ru
## Более подробно о ядре.
Ядро OpenCascade довольно обширно, имеет бесчисленное количество инструментов и потому врядли возможно сколь-нибудь передать его суть в рамках этой маленькой справки.

За подробной информацией о геометрическом ядре OpenCascade следует обратиться к документации:  
:en
## Learn more about the kernel.
The OpenCascade core is quite extensive, has countless tools, and therefore it is hardly possible to convey its essence in any way within the framework of this little help.

For detailed information on the OpenCascade geometric kernel, refer to the documentation: 
::
[Technology Overview](https://www.opencascade.com/doc/occt-7.3.0/overview/html/index.html)  
[Reference Manual](https://www.opencascade.com/doc/occt-7.3.0/refman/html/index.html)
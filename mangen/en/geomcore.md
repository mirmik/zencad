# Introduction to BREP representation of geometric models. 


The ZenCad library is based on the functionality and object structure of the OpenCascade geometric kernel, which uses boundary representation (BREP) for working with geometric models.

For a more complete understanding of the library and the use of advanced functions, at least a superficial understanding of the BREP and the topological structure of geometric objects in the geometric kernel used is required. 

------------------------------------------------------
## Boundary representation.

Boundary representation is a way of representing bodies by describing their boundaries.

An object in Boundary Representation is defined topologically (using a set of references to its bounding objects) and geometrically (using a geometric rule that shapes its shape). Bounding objects, in turn, are set based on the same considerations.

So, for example, a cube is a volumetric body formed by the inner space of a shell formed by 6 faces. Each face is geometrically defined by a plane equation and is bounded by 4 edge objects. Each edge is geometrically defined by the equation of a straight line and is bounded by two vertices.

In different libraries using the BREP representation, the division of objects into classes can be done with certain specifics, but the general idea will be the same. ZenCad uses the OpenCascade core class system. 


------------------------------------------------------
## Классы геометрических объектов.
|ZenCad|OpenCascade|Составной|Мерность|Описание|
|----|---|----|----|----|
|Shape|TopoDS\_Shape|неопр.|неопр.|Абстрактный геометрический объект|
|Vertex|TopoDS\_Vertex|нет|0|Вершина|
|Edge|TopoDS\_Edge|нет|1|Ребро|
|Wire|TopoDS\_Wire|да|1|Сложное ребро|
|Face|TopoDS\_Face|нет|2|Грань|
|Shell|TopoDS\_Shell|да|2|Оболочка|
|Solid|TopoDS\_Solid|нет|3|Твёрдое тело|
|CompSolid|TopoDS\_CompSolid|да|3|Множество твёрдых тел|
|Compound|TopoDS\_Compound|да|неопр.|Составной объект|

`Vertex` is a topological vertex; `Point3` holds coordinates. `shape.vertices()` returns a vertex collection; `vertex.point()` obtains a point.

------------------------------------------------------
## Learn more about the kernel.
The OpenCascade core is quite extensive, has countless tools, and therefore it is hardly possible to convey its essence in any way within the framework of this little help.

For detailed information on the OpenCascade geometric kernel, refer to the documentation: 
[Technology Overview](https://www.opencascade.com/doc/occt-7.3.0/overview/html/index.html)  
[Reference Manual](https://www.opencascade.com/doc/occt-7.3.0/refman/html/index.html)

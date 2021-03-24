:ru
# Экспорт/Импорт

Операции экспорта/импорта отличаются от большинства операций библиотеки zencad тем, что производятся не только над объектами в памяти программы, но и над файлами. Для работы с файлами библиотека кэширования evalcache использует специальный механизм. Благодаря ему операции импорта учитывают изменения содержимого файлов, а операции экспорта не выполняются без необходимости.
:en
# Export Import

Export / import operations differ from most operations of the zencad library in that they are performed not only on objects in the program memory, but also on files. The evalcache caching library uses a special mechanism to work with files. It allows imports to take into account changes to the content of files, and exports are not performed unnecessarily. 
::

---
:ru
## STL
Создать файл мешсети формата STL, находящийся по пути `path`, из твердотельной модели `model`. 
Параметр `delta` определяет степень детализации. Чем меньше `delta`, тем меньше размер полигонов.
:en
## STL
Create an STL mesh file located in the path from the solid model model.
The `delta` parameter determines the granularity. The smaller the delta, the smaller the size of the polygons. 
::
```python3
to_stl(model, path, delta)
```

:ru
Импортирование МАЛОПОЛИГОНАЛЬНЫХ stl и прочих форматов mesh сетей возможно с применением сторонних библиотек, таких как trimesh. (см. examples/Integration/trimesh)
:en
Importing SMALL stl and other mesh mesh formats is possible using third-party libraries such as trimesh. (see examples / Integration / trimesh) 
::

---
:ru
## BREP
Создать файл brep представления формата BREP, находящийся по пути `path`, из твердотельной модели `model`. 
:en
Create a brep file of the BREP format located in the path `path` from the solid model` model`. 
::
```python3
to_brep(model, path)
```

:ru
Считать файл brep представления формата BREP, находящийся по пути `path`. Вернуть полученную модель.
:en
Read the brep file of the BREP format located in the path `path`. Return the resulting model. 
::
```python3
m = from_brep(path)
```

---
## SVG
:ru
("0.34.0: На текущий момент поддержка ограничена. Поддерживаются не все типы кривых.")

Создать/считать svg файл из плоского тела `model`, находящийся по пути `path`. 
:en
("0.34.0: Currently limited support. Not all curve types are supported.")

Create / read svg file from flat body `model`, located on path` path`. 
::

```python3
to_svg(model, path)
model = from_svg(path)
```

:ru
Создать/считать строку svg представления плоского тела `model`. 
:en
Create / read svg string of flat body representation `model`. 
::

```python3
svg = to_svg_string(model)
model = from_svg_string(svg)
```


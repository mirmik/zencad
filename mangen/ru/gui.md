:ru
# Графический интерфейс, основные моменты.
:en
# Graphical interface, highlights. 
::

![gui.png](../images/gui.png)

---
:ru
## Вызов
Окно графического интерфейса может быть вызвано следующими способами:

* Вызов `zencad.show()` в интерпретаторе python.  
* Выполнение `python3 -m pip zencad` в среде терминала. (usage: `python3 -m pip zencad [filepath]`)  
* Вызов утилиты командной строки `zencad` (usage: `zencad [filepath]`)
:en
## Call
The GUI window can be invoked in the following ways:

* Calling `zencad.show ()` in the python interpreter.
* Executing `python3 -m pip zencad` in a terminal environment. (usage: `python3 -m pip zencad [filepath]`)
* Call the command line utility `zencad` (usage:` zencad [filepath] `) 
::  

---
:ru
## Обновление модели по обновлению файла источника
Визуализатор отслеживает изменения файла, источника геометрии. По обновлению источника, программа автоматически начинает перевыполнение скрипта. Следует учесть, что реализация этой функциональности выполняется путём изменения работы функции `zencad.show()` (То есть, есть разница в запуске скрипта из терминала, или из программы визуализатора).  
:en
## Updating the model by updating the source file
The renderer keeps track of changes in the file, the source of the geometry. When the source is updated, the program automatically starts re-executing the script. It should be noted that this functionality is implemented by changing the operation of the `zencad.show ()` function (That is, there is a difference in running the script from the terminal, or from the visualizer program). 
::

---
:ru
## Встроенный текстовый редактор
Визуализатор имеет встроенный виджет текстового редактора, который может быть использован для быстрого редактирования или проведения экспериментов. Отображение редактора `View/'Hide editor'`
:en
## Built-in text editor
The visualizer has a built-in text editor widget that can be used for quick editing or experimentation. Show editor `View/'Hide editor'`
::

---
:ru
## Встроенная консоль
ZenCad также ретранслирует вывод терминала на встроенную консоль. Отображение консоли `View/'Hide console'`.
Это может использоваться в случае, когда вывод основного терминала недоступен.
:en
## Built-in console
ZenCad also relays the terminal output to the embedded console. Show console `View/'Hide console'`.
This can be used when the main terminal output is not available. 
::

---
:ru
## Маркеры, определение координат
Для установки маркеров следует используются клавиши `Q(F1)`, `W(F2)`. После установки координаты маркера выводятся в соответствующем поле. Если установлены оба маркера, дистанция между ними отображается в поле Distance.
:en
## Markers, determination of coordinates
To set markers, use the keys `Q (F1)`, `W (F2)`. After setting, the coordinates of the marker are displayed in the corresponding field. If both markers are set, the distance between them is displayed in the Distance field. 
::

---
:ru
## 3D навигация
Вращение: MouseLeftClick/Alt + MouseMove  
Смещение: MouseRightClick/Shift + MouseMove  
Масштабирование: PgUp/PgDown/MouseWheel  

Визуализатор поддерживает два режима ориентации. Ортогональную ориентацию (ось Z всегда направлена вверх) и режим свободного вращения. Переключение между ними - `Navigation/'Axionometric view'`, `Navigation/'Free rotation view'`
:en
## 3D navigation
Rotation: MouseLeftClick / Alt + MouseMove
Offset: MouseRightClick / Shift + MouseMove
Scaling: PgUp / PgDown / MouseWheel

The renderer supports two orientation modes. Orthogonal orientation (Z axis is always upward) and free rotation mode. Switch between them - `Navigation/'Axionometric view'`, `Navigation / 'Free rotation view'`. 
::
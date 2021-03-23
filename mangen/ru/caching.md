:ru
# Кэширование и ленивые объекты.

Особенностью скриптового cad является необходимость перезапуска скрипта генерации геометрии при каждом обновлении модели. С ростом размера модели это приводит к значительному росту времени, требующегося на расчёт и отрисовку геометрии. С целью решения этой проблемы вычислительно ёмкие операции ZenCad закешированы и ленифицированы силами библиотеки [evalcache](https://github.com/mirmik/evalcache). 

Вместо непосредственного расчета, evalcache строит дерево построения модели на основе хэшключей генерируемых объектов. Библиотека сохраняет в кэше на жестком диске все произведенные вычисления и в случае, если объект уже был расчитан ранее, достаёт его из кэша. evalcache отслеживает изменения параметров в дереве модели и на лету обновляет переставшие быть актуальными объекты вычисления.
:en
# Caching and lazy objects.

A feature of the scripted cad is the need to restart the geometry generation script every time the model is updated. As the size of the model grows, this leads to a significant increase in the time required for calculating and drawing geometry. To solve this problem, computationally intensive ZenCad operations are cached and lenified by the [evalcache] library (https://github.com/mirmik/evalcache).

Instead of calculating directly, evalcache builds a model building tree based on the hash keys of the generated objects. The library saves all performed calculations in the cache on the hard disk and, if the object has already been calculated earlier, retrieves it from the cache. evalcache monitors changes in parameters in the model tree and updates computation objects that have ceased to be up-to-date on the fly. 
::

:ru
### Отладка в условиях работы с ленивыми вычислениями.
Так как evalcache выполняет вычисления только в момент, когда объект в действительности запрошен, а не тогда, когда он объявлен, могут возникать проблемы с пониманием точки возникновения возможной ошибки. Также могут возникать проблемы из-за неявного раскрытия ленивых объектов на некоторых операциях.

Для отладки и понимания точки возникновения ошибки можно применять следующие опции:
:en
### Debugging with lazy evaluation.
Since evalcache only performs computations when the object is actually requested, and not when it is declared, it can be difficult to understand where a possible error occurs. Problems can also arise due to the implicit expansion of lazy objects on some operations.

The following options can be used to debug and understand where the error occurred: 
::

```python
zencad.lazy.diag=True # Активировать вывод информации об операциях библиотеки кеширования.
zencad.lazy.fastdo=True # Выполнять запрос объекта в момент его создания.
zencad.lazy.encache=False # Запретить сохранение в кэш.
zencad.lazy.decache=False # Запретить загрузку из кэша.

zencad.lazy.onbool=False # Запретить автоматическое раскрытие на булевых операциях
zencad.lazy.onstr=False # Запретить автоматическое раскрытие при преобразовании к строке.

zencad.lazy.onplace=True # Раскрывать объект в момент его создания (не рекомендуется, может нарушать логику).
```

:ru
Дополнительные опции можно найти в документации к коду библиотеки evalcache.

----
### Где лежит кэш?
По умолчанию кеш располагается по локальному адресу `~/.zencadcache`, где _~_ - домашний директорий пользователя.
:en
Additional options can be found in the documentation for the evalcache library code.

----
### Where is the cache?
By default, the cache is located at the local address `~/.zencadcache`, where _~_ is the user's home directory. 
::
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

Для отладки и понимания точки возникновения ошибки можно в шапке скрипта включить
немедленные вычисления. Публичные типы объектов при этом не меняются:
:en
### Debugging with lazy evaluation.
Since evalcache only performs computations when the object is actually requested, and not when it is declared, it can be difficult to understand where a possible error occurs. Problems can also arise due to the implicit expansion of lazy objects on some operations.

Set immediate evaluation in the script header to report failures at the
operation that declared them. Public object types do not change:
::

```python
zencad.configure(cache_enabled=False)
zencad.set_evaluation_mode("immediate")
model = zencad.box(20) - zencad.cylinder(3, 20)
```

:ru
Для headless-проверки тот же режим включается командой
`zencad inspect model.py --eager --no-cache --json`. Режим устанавливается для всего
скрипта и действует до явного изменения. Старый глобальный интерфейс
`zencad.lazy.onplace` в ZenCad 2 удалён.
:en
For a headless check, use
`zencad inspect model.py --eager --no-cache --json`. The mode applies to the whole
script and persists until explicitly changed. The old global `zencad.lazy.onplace`
interface was removed in ZenCad 2.
::

----
### Где лежит кэш?
По умолчанию все процессы ZenCad текущего пользователя используют один общий
каталог tempfile.gettempdir()/zencad-cache-<uid>. ZenCad не удаляет его при
завершении, но операционная система может очистить временный каталог.

Путь и состояние кэша можно изменить в окне настроек ZenCad. Переменная
окружения ZENCAD_CACHE_DIR переопределяет сохранённый путь, а
ZENCAD_CACHE_DISABLE=1 полностью отключает чтение и запись дискового кэша.
Ленивые вычисления при этом остаются включёнными.

В пользовательском скрипте конфигурацию можно изменить до создания геометрии:

    zencad.configure(cache_dir="/path/to/cache")
    zencad.configure(cache_enabled=False)
:en
Additional options can be found in the documentation for the evalcache library code.

----
### Where is the cache?
By default, every ZenCad process of the current user shares
tempfile.gettempdir()/zencad-cache-<uid>. ZenCad does not remove it at process
exit, although the operating system may clean its temporary area.

The ZenCad settings dialog can change the directory and enabled state.
ZENCAD_CACHE_DIR overrides the saved directory, while
ZENCAD_CACHE_DISABLE=1 disables both disk-cache reads and writes. Lazy
evaluation remains enabled.

A user script can configure caching before creating geometry:

    zencad.configure(cache_dir="/path/to/cache")
    zencad.configure(cache_enabled=False)
::

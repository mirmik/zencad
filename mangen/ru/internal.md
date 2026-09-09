:ru
# Внутренняя кухня ZenCad

## Геометрическое ядро и вычисления

ZenCad использует OpenCascade через пакет `cadquery-ocp-novtk` и его Python-модули `OCP`. Геометрические типы и операции ZenCad находятся в `zencad.geom`; адаптеры к ядру — в `zencad._native`.

Объекты геометрии и значения сохраняют зависимости между операциями. Вычислитель EvalCache выполняет их в режиме `deferred` или `immediate` и управляет повторным использованием результатов. `Context` владеет вычислителем; обычному скрипту достаточно модульных функций и методов объектов. `.value()` получает вычисленное значение, `.native()` у формы — объект OCP. Подробнее: [«Вычисления и кэш»](caching.html), [«Значения, точки и преобразования»](prim0d.html).

## Главное окно и исполнитель скрипта

При запуске `zencad model.py` или `python -m zencad model.py` главный процесс владеет интерфейсом Qt, viewer OpenCascade и контекстом OpenGL. В этом же процессе находятся камера, выделение, маркеры и объекты отображения AIS.

`RunnerSupervisor` запускает исполнителя модели отдельным процессом через `multiprocessing` с методом `spawn`. Исполнитель строит геометрию и собирает сцену, но не создаёт окна Qt или OpenGL. Между процессами передаются данные сцены: сериализованная BREP-геометрия или меши, размещения, цвета, имена и видимость объектов. Окно viewer принадлежит главному процессу и сохраняется при пересчётах модели.

Связь организована через каналы `multiprocessing.Pipe` и версионированный протокол. По нему передаются снимки сцены, прогресс вычислений, вывод скрипта и ошибки; в обратном направлении — управляющие события и пользовательский ввод. `stdout` и `stderr` скрипта перехватываются исполнителем и доставляются интерфейсу как сообщения.

## Пересчёт и обновление сцены

Каждый запуск получает номер поколения. Исполнитель накапливает описание объектов в `SceneDraft`; при публикации получается снимок `SceneSnapshot`. `ScenePresenter` в GUI проверяет и декодирует его, затем заменяет содержимое viewer. Применяется только результат актуального поколения: запоздавшее сообщение от предыдущего запуска не заменит текущую модель.

Во время расчёта, отмены или ошибки остаётся видимой последняя успешно построенная сцена. Камера при обновлении по умолчанию сохраняется. Исполнителя можно остановить и запустить заново, не пересоздавая главное окно и viewer.

## Что делает show()

Поведение зависит от способа запуска:

- В скрипте, запущенном редактором или командами `inspect`/`check`, `display()` добавляет данные в `SceneDraft`, а `show()` публикует снимок сцены. Для статической сцены исполнение затем продолжается без запуска оконного цикла.
- При прямом запуске `python model.py` вызов `show()` открывает самостоятельный viewer в том же процессе и запускает цикл событий Qt. Полный редактор при этом не создаётся. Этот режим также доступен через `zencad --display model.py`.
- `zencad --no-show model.py` выполняет скрипт с отключённым показом. Для получения отчёта о геометрии используются отдельные команды [inspect и check](headless.html).

## Анимация и ввод

В редакторе анимированный исполнитель остаётся активным после публикации сцены. Callback получает время, ввод через `state.input` и управление камерой через `state.camera`. Изменения размещения, цвета и видимости передаются как обновления сцены; действия камеры — отдельными сообщениями. Обработка Qt и отображение выполняются в GUI-процессе.

Геометрию для такой анимации создают до начального `show()`. Callback не получает прямой доступ к виджету viewer и не заменяет геометрию после публикации. Контракт и примеры описаны в разделе [«Анимация»](animate.html).

Описание протокола, владения объектами и жизненного цикла: [Runtime architecture](../development/runtime-architecture.md).
:en
# ZenCad internals

## Geometry kernel and evaluation

ZenCad uses OpenCascade through `cadquery-ocp-novtk` and its `OCP` Python modules. ZenCad geometry types and operations live in `zencad.geom`; kernel adapters live in `zencad._native`.

Geometry objects and values retain dependencies between operations. The EvalCache evaluator executes them in `deferred` or `immediate` mode and manages result reuse. A `Context` owns an evaluator; ordinary scripts use module functions and object methods. `.value()` obtains a computed value, while a shape's `.native()` obtains an OCP object. See [Evaluation and caching](caching.html) and [Values, points and transforms](prim0d.html).

## Main window and script runner

When started with `zencad model.py` or `python -m zencad model.py`, the main process owns Qt, the OpenCascade viewer and the OpenGL context. Camera, selection, markers and AIS presentation objects also belong to this process.

`RunnerSupervisor` starts a separate model process using the `multiprocessing` `spawn` method. The runner constructs geometry and collects the scene without creating Qt or OpenGL windows. Scene data crosses the process boundary: serialized BREP geometry or meshes, placements, colors, names and visibility. The viewer window belongs to the main process and persists across model evaluations.

Communication uses `multiprocessing.Pipe` connections and a versioned protocol. Messages carry scene snapshots, evaluation progress, script output and errors; control events and user input travel in the opposite direction. The runner captures script stdout and stderr and delivers them to the interface as messages.

## Evaluation and scene updates

Each run receives a generation number. The runner collects object descriptions in a `SceneDraft` and publishes a `SceneSnapshot`. The GUI's `ScenePresenter` validates and decodes the snapshot before replacing the viewer contents. Only the current generation can be applied: a late message from a previous run cannot replace the current model.

The last successful scene remains visible during evaluation, cancellation or failure. Camera state is preserved by default. A runner can be stopped and replaced without recreating the main window or viewer.

## What show() does

Its behavior depends on how the script is launched:

- In scripts launched by the editor or `inspect`/`check`, `display()` adds data to a `SceneDraft`, and `show()` publishes a snapshot. Static scripts then continue without entering a GUI event loop.
- In a direct `python model.py` run, `show()` opens a standalone viewer in the same process and starts the Qt event loop. It does not create the full editor. This mode is also available through `zencad --display model.py`.
- `zencad --no-show model.py` executes a script with display disabled. Use [inspect and check](headless.html) to obtain geometry reports.

## Animation and input

In the editor, an animated runner stays active after publishing the scene. Its callback receives timing, input through `state.input` and camera controls through `state.camera`. Placement, color and visibility changes are sent as scene updates; camera actions use separate messages. Qt event handling and presentation run in the GUI process.

Construct geometry for managed animations before the initial `show()`. The callback has no direct viewer-widget access and cannot replace geometry after publication. See [Animation](animate.html) for the contract and examples.

See [Runtime architecture](../development/runtime-architecture.md) for protocol details, object ownership and lifecycle.
::

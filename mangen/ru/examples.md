:ru
# Примеры

Примеры поставляются в каталоге `zencad/examples`. Откройте модель через меню примеров в GUI или запустите файл из checkout репозитория:

```sh
python3 -m zencad zencad/examples/4.Assemble/robot-arm.py
```

- `4.Assemble/robot-arm.py` — рука из поворотных звеньев следует за шариком; используются Якобиан и обратная кинематика.
- `4.Assemble/robot.py` — анимация иерархической сборки с поворотами головы и рук.
- `4.Assemble/EulerAngles.py` — композиция поворотов.
- `3.Animation/camera.py` — управление камерой из анимации.
- `Models/nut.py` — построение резьбовой геометрии через спираль и развёртку профиля. Функции модели определены в самом примере; это не отдельная библиотека стандартных резьбовых соединений.

Для проверки модели без окна:

```sh
python3 -m zencad --no-show zencad/examples/4.Assemble/robot-arm.py
```

Этот режим проверяет построение начальной сцены; callback анимации выполняется при обычном запуске. Устройство анимации описано в разделе [Анимация](animate.html), работа с цепями — в разделе [Кинематика](kinematic.html).
:en
# Examples

Examples are included in `zencad/examples`. Open a model from the GUI examples menu or run its file from a repository checkout:

```sh
python3 -m zencad zencad/examples/4.Assemble/robot-arm.py
```

- `4.Assemble/robot-arm.py` — a rotary-joint arm follows a ball using a Jacobian and inverse kinematics.
- `4.Assemble/robot.py` — an animated hierarchical assembly with rotating head and arms.
- `4.Assemble/EulerAngles.py` — composition of rotations.
- `3.Animation/camera.py` — camera control from an animation.
- `Models/nut.py` — threaded geometry built with a helix and a swept profile. The model functions are defined in the example itself; this is not a separate standard fastener library.

To check a model without opening a window:

```sh
python3 -m zencad --no-show zencad/examples/4.Assemble/robot-arm.py
```

This mode checks the initial scene construction; the animation callback runs during normal execution. See [Animation](animate.html) for animation behavior and [Kinematics](kinematic.html) for chains.
::

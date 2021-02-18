from zencad.scene import Scene

UNBOUND_MODE = False  # Устанавливается из zencad.gui.display_unbounded
# сигнализирует об активации подчинённого режима работы

__default_scene = Scene()  # Сцена, с которой работают команды
# disp и show по умолчанию


def display(shp, color=None, deep=True, scene=None):
    if scene is None:
        scene = __default_scene

    return __default_scene.add(shp, color)


def disp(*args, **kwargs):
    return display(*args, **kwargs)


def show(scene=None, display_only=False):
    if scene is None:
        scene = __default_scene

    if UNBOUND_MODE:
        # Включён UNBOUND_MODE возвращаем управление модулю,
        # который создаст виджет и прилинкует его к главному окну
        import zencad.gui.display_unbounded
        zencad.gui.display_unbounded.unbound_worker_bottom_half(
            scene=scene)

    elif display_only:
        # Простой режим. Просто отображаем виджет без
        # главной оболочки.
        import zencad.gui.display_only
        zencad.gui.display_only.init_display_only_mode()
        zencad.gui.display_only.DISPLAY.attach_scene(scene)
        zencad.gui.display_only.exec_display_only_mode()

    else:
        import zencad.gui.main_unbounded
        zencad.gui.main_unbounded._show(scene=scene)

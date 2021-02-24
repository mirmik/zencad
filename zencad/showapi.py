from zencad.scene import Scene
from zenframe.unbound import (
    is_unbound_mode, 
    unbound_worker_bottom_half,
    unbound_frame_summon
)
        
#UNBOUND_MODE = False  # Устанавливается из zencad.gui.display_unbounded
# сигнализирует об активации подчинённого режима работы

__default_scene = Scene()  # Сцена, с которой работают команды
# disp и show по умолчанию


def display(shp, color=None, deep=True, scene=None):
    if scene is None:
        scene = __default_scene

    return __default_scene.add(shp, color)


def disp(*args, **kwargs):
    return display(*args, **kwargs)

def widget_creator(communicator, scene):
    from zencad.gui.display import DisplayWidget
    display = DisplayWidget(
        communicator=communicator,
        init_size=(640, 480))
    display.attach_scene(scene)

    # todo: почему не внутри?
    communicator.bind_handler(display.external_communication_command)
    return display

def show(scene=None, display_only=False):
    if scene is None:
        scene = __default_scene

    if is_unbound_mode():
        # Включён UNBOUND_MODE возвращаем управление модулю,
        # который создаст виджет и прилинкует его к главному окну
        unbound_worker_bottom_half(scene=scene)

    elif display_only:
        # Простой режим. Просто отображаем виджет без
        # главной оболочки.
        import zencad.gui.display_only
        zencad.gui.display_only.init_display_only_mode()
        zencad.gui.display_only.DISPLAY.attach_scene(scene)
        zencad.gui.display_only.exec_display_only_mode()

    else:
        # Запускаем оболочку как подчинённый процесс 
        import zencad.gui.main_unbounded
        unbound_frame_summon(widget_creator, "zencad", scene=scene)

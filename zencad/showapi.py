from zencad.scene import Scene

NOSHOW = False

# UNBOUND_MODE = False  # Устанавливается из zencad.gui.display_unbounded
# сигнализирует об активации подчинённого режима работы

__default_scene = Scene()  # Сцена, с которой работают команды
# disp и show по умолчанию


def display(shp, color=None, deep=True, scene=None):
    if scene is None:
        scene = __default_scene

    if (isinstance(shp, list)):
        ret = []
        for i in shp:
            ret.append(display(i, color, deep, scene))
        return ret

    return scene.add(shp, color)


def disp(*args, **kwargs):
    return display(*args, **kwargs)


def highlight(shp, color=(1, 0, 0, 0.5), deep=True, scene=None):
    display(shp, color, deep, scene)
    return shp


def hl(*args, **kwargs): return highlight(*args, **kwargs)


ANIMATE_THREAD = None


def widget_creator(communicator, scene, animate, preanimate, close_handle, animate_step=0.01):
    import zencad.animate
    import zenframe.finisher

    global ANIMATE_THREAD
    from zencad.gui.display import DisplayWidget
    display = DisplayWidget(
        communicator=communicator)
    display.attach_scene(scene)

    # todo: почему не внутри?
    communicator.bind_handler(display.external_communication_command)

    if close_handle:
        zenframe.finisher.register_destructor(None, close_handle)

    if animate:
        animate_thread = zencad.animate.AnimateThread(
            widget=display,
            updater_function=animate,
            animate_step=animate_step)

        if preanimate:
            preanimate(display, animate_thread)

        animate_thread.start()
        ANIMATE_THREAD = animate_thread

    return display


def show(scene=None, animate=None, preanimate=None, close_handle=None, animate_step=0.01, display_only=False):
    from zenframe.unbound import (
        is_unbound_mode,
        unbound_worker_bottom_half,
        unbound_frame_summon
    )
    from zenframe.configuration import Configuration

    if scene is None:
        scene = __default_scene

    if Configuration.NOSHOW:
        return

    if is_unbound_mode():
        # Включён UNBOUND_MODE возвращаем управление модулю,
        # который создаст виджет и прилинкует его к главному окну
        unbound_worker_bottom_half(scene=scene, animate=animate, preanimate=preanimate,
                                   close_handle=close_handle, animate_step=animate_step)

    elif display_only:
        # Простой режим. Просто отображаем виджет без
        # главной оболочки.
        import zencad.gui.display_only
        zencad.gui.display_only.init_display_only_mode()
        zencad.gui.display_only.DISPLAY.attach_scene(scene)
        zencad.gui.display_only.exec_display_only_mode()

    else:
        # Запускаем оболочку как подчинённый процесс
        unbound_frame_summon(widget_creator, "zencad",
                             scene=scene, animate=animate, preanimate=preanimate, close_handle=close_handle, animate_step=animate_step)

from contextlib import contextmanager

from zencad.scene import Scene
from zencad.scene_draft import SceneDraft

NOSHOW = False
DISPLAY = None
ANIMATE_THREAD = None

# UNBOUND_MODE = False  # Устанавливается из zencad.gui.display_unbounded
# сигнализирует об активации подчинённого режима работы

__default_scene = Scene()  # Сцена, с которой работают команды
# disp и show по умолчанию


def display(shp, color=None, deep=True, scene=None):
    from zencad.settings import Settings

    if scene is None:
        scene = __default_scene

    # Managed runners receive settings as data and must not initialize Qt just
    # because a script called display().
    if not isinstance(scene, SceneDraft):
        Settings.restore()

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


def hl(*args, **kwargs):
    return highlight(*args, **kwargs)


def widget_creator(communicator, scene, animate, preanimate, close_handle, animate_step=0.01):
    import zencad.animate
    import zenframe.finisher

    global DISPLAY
    global ANIMATE_THREAD
    from zencad.gui.display import DisplayWidget
    DISPLAY = DisplayWidget(
        communicator=communicator)
    DISPLAY.attach_scene(scene)

    # todo: почему не внутри?
    communicator.bind_handler(DISPLAY.external_communication_command)

    if close_handle:
        zenframe.finisher.register_destructor(None, close_handle)

    if animate:
        animate_thread = zencad.animate.AnimateThread(
            widget=DISPLAY,
            updater_function=animate,
            animate_step=animate_step)

        if preanimate:
            preanimate(DISPLAY, animate_thread)

        animate_thread.start()
        ANIMATE_THREAD = animate_thread

    return DISPLAY


def show(scene=None, animate=None, preanimate=None, close_handle=None, animate_step=0.01, display_only=False):
    if scene is None:
        scene = __default_scene

    if isinstance(scene, SceneDraft):
        if preanimate is not None:
            raise ValueError(
                "Managed scenes do not support preanimate or direct GUI access"
            )
        if animate is None and close_handle is not None:
            raise ValueError(
                "Managed static scenes do not support close_handle"
            )
        snapshot = scene.publish()
        scene.ready(animated=animate is not None)
        if animate is not None:
            scene.run_animation(
                animate,
                animate_step=animate_step,
                close_handle=close_handle,
            )
        return snapshot

    from zenframe.unbound import (
        is_unbound_mode,
        unbound_worker_bottom_half,
        unbound_frame_summon
    )
    from zenframe.configuration import Configuration

    if Configuration.NOSHOW:
        return

    if is_unbound_mode():
        # Включён UNBOUND_MODE возвращаем управление модулю,
        # который создаст виджет и прилинкует его к главному окну
        unbound_worker_bottom_half(scene=scene, animate=animate, preanimate=preanimate,
                                   close_handle=close_handle, animate_step=animate_step)

    elif display_only or Configuration.WIDGET_ONLY:
        # Простой режим. Просто отображаем виджет без
        # главной оболочки.
        import zencad.gui.display_only
        zencad.gui.display_only.init_display_only_mode()
        DISPLAY.attach_scene(scene)
        zencad.gui.display_only.exec_display_only_mode()

    else:
        # Запускаем оболочку как подчинённый процесс
        unbound_frame_summon(widget_creator, "zencad",
                             scene=scene, animate=animate, preanimate=preanimate, close_handle=close_handle, animate_step=animate_step)


@contextmanager
def managed_scene(
    generation,
    publisher=None,
    camera_policy="preserve",
    patch_publisher=None,
    ready_publisher=None,
    cancel_event=None,
    input_drain=None,
):
    """Temporarily route the public display/show API into a data-only draft."""
    global __default_scene

    previous = __default_scene
    draft = SceneDraft(
        generation=generation,
        publisher=publisher,
        camera_policy=camera_policy,
        patch_publisher=patch_publisher,
        ready_publisher=ready_publisher,
        cancel_event=cancel_event,
        input_drain=input_drain,
    )
    __default_scene = draft
    try:
        yield draft
    finally:
        __default_scene = previous

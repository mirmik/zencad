import zencad.geom.trans as trans
import zencad.geom.general_transformation as general_transformation


class Transformable:
    def move(self, *args): return trans.move(*args)(self)
    def moveX(self, *args): return trans.moveX(*args)(self)
    def moveY(self, *args): return trans.moveY(*args)(self)
    def moveZ(self, *args): return trans.moveZ(*args)(self)
    def mov(self, *args): return trans.move(*args)(self)
    def movX(self, *args): return trans.moveX(*args)(self)
    def movY(self, *args): return trans.moveY(*args)(self)
    def movZ(self, *args): return trans.moveZ(*args)(self)

    def translate(self, *args): return trans.translate(*args)(self)
    def translateX(self, *args): return trans.translateX(*args)(self)
    def translateY(self, *args): return trans.translateY(*args)(self)
    def translateZ(self, *args): return trans.translateZ(*args)(self)

    def rotate(self, *args): return trans.rotate(*args)(self)
    def rotateX(self, *args): return trans.rotateX(*args)(self)
    def rotateY(self, *args): return trans.rotateY(*args)(self)
    def rotateZ(self, *args): return trans.rotateZ(*args)(self)
    def rot(self, *args): return trans.rotate(*args)(self)
    def rotX(self, *args): return trans.rotateX(*args)(self)
    def rotY(self, *args): return trans.rotateY(*args)(self)
    def rotZ(self, *args): return trans.rotateZ(*args)(self)

    def scale(self, *args): return trans.scale(*args)(self)
    def scaleX(self, *args): return general_transformation.scaleX(*args)(self)
    def scaleY(self, *args): return general_transformation.scaleY(*args)(self)
    def scaleZ(self, *args): return general_transformation.scaleZ(*args)(self)
    def scaleXYZ(
        self, *args): return general_transformation.scaleXYZ(*args)(self)

    def up(self, *args): return trans.up(*args)(self)
    def down(self, *args): return trans.down(*args)(self)
    def right(self, *args): return trans.right(*args)(self)
    def left(self, *args): return trans.left(*args)(self)
    def forw(self, *args): return trans.forw(*args)(self)
    def back(self, *args): return trans.back(*args)(self)

    def mirror(self, *args): return trans.mirror(*args)(self)
    def mirrorX(self, *args): return trans.mirrorX(*args)(self)
    def mirrorY(self, *args): return trans.mirrorY(*args)(self)
    def mirrorZ(self, *args): return trans.mirrorZ(*args)(self)
    def mirrorXY(self, *args): return trans.mirrorXY(*args)(self)
    def mirrorXZ(self, *args): return trans.mirrorXZ(*args)(self)
    def mirrorYZ(self, *args): return trans.mirrorYZ(*args)(self)

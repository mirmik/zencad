import zencad.assemble
import zencad.libs.screw
from zencad._native.exttrans import nulltrans
import numpy
import time

from abc import ABC, abstractmethod

from zencad.assemble import kinematic_unit


class kinematic_chain:
    """Объект-алгоритм управления участком кинематической чепи от точки
    выхода, до точки входа.

    Порядок следования обратный, потому что звено может иметь одного родителя,
    но много потомков. Цепочка собирается от выходного звена к родителю.

    distant - конечное звено.
    proxymal - начальное звено. 
            Если не указано, алгоритм проходит до абсолютной СК"""

    def __init__(self, distant, proxymal=None):
        self.distant = distant
        self.chain = self.collect_chain(distant, proxymal)
        self.simplified_chain = self.simplify_chain(self.chain)
        self.kinematic_pairs = self.collect_kinematic_pairs()

    def collect_kinematic_pairs(self):
        par = []
        for l in self.chain:
            if isinstance(l, kinematic_unit):
                par.append(l)
        return par

    #indexer 
    def __getitem__(self, key):
        return self.kinematic_pairs[key]

    def apply_step(self, x):
        # Validate before changing any joint, including unsupported multi-DOF chains.
        if any(k.dim() != 1 for k in self.kinematic_pairs):
            raise NotImplementedError("apply_step supports only one-coordinate joints")
        if len(x) != len(self.kinematic_pairs):
            raise ValueError("Expected one coordinate change per kinematic pair")
        for k, delta in zip(self.kinematic_pairs, x):
            k.set_coord(k.coord + delta)

    def apply(self, speeds, delta):
        self.apply_step([speed * delta for speed in speeds])

    @staticmethod
    def collect_chain(distant, proxymal=None):
        chain = []
        link = distant

        while link is not proxymal:
            if link is None:
                raise ValueError("proxymal must be an ancestor of distant")
            chain.append(link)
            link = link.parent

        if proxymal is not None:
            chain.append(proxymal)

        return chain

    @staticmethod
    def simplify_chain(chain):
        ret = []
        tmp = None

        for l in chain:
            if isinstance(l, kinematic_unit):
                if tmp is not None:
                    ret.append(tmp)
                    tmp = None
                ret.append(l)
            else:
                if tmp is None:
                    tmp = l.location
                else:
                    tmp = l.location * tmp

        if tmp is not None:
            ret.append(tmp)

        return ret

    def getchain(self):
        return self.chain

    @staticmethod
    def found_first_kinematic_unit_in_parent_tree(body):
        if isinstance(body, kinematic_unit):
            raise ValueError("body cannot be kinematic unit")
    
        link = body
        while link is not None:
            if isinstance(link, kinematic_unit):
                return link
            link = link.parent
        return None

    def sensivity2(self, body, local, basis=None):
        """
        body - звено, с которым связана отслеживаемая система координат
        local - локальная система координат внутри body
        basis - система координат, в которой возвращаются чувствительности
        """

        ancestors = set()
        ancestor = body
        while ancestor is not None:
            ancestors.add(ancestor)
            ancestor = ancestor.parent

        senses = []
        outtrans = body.global_location * local

        for link in self.kinematic_pairs:
            # Получаем собственные чувствительности текущего звена в его собственной системе координат
            lsenses = link.senses()

            if link.output not in ancestors:
                for _ in lsenses:
                    senses.append(zencad.libs.screw.screw())
                continue
 
            # Получаем трансформацию выхода текущей пары
            linktrans = link.output.global_location

            # Получаем трансформацию цели в системе текущего звена
            trsf = linktrans.inverse() * outtrans

            # Получаем радиус-вектор в системе текущего звена
            radius = trsf.translation()

            for sens in reversed(lsenses):
                # Получаем линейную и угловую составляющие чувствительности
                # в системе текущего звена
                scr = sens.kinematic_carry(radius)

                # Трансформируем их в систему цели и добавляем в список
                senses.append((
                    scr.inverse_transform_by(trsf)
                ))
            
        # Перегоняем в систему basis, если она задана
        if basis is not None:
            btrsf = basis.global_location
            trsf = btrsf.inverse() * outtrans
            senses = [s.transform_by(trsf) for s in senses]

        return senses

    def sensitivity_jacobian2(self, body, local, basis=None):
        """Вернуть матрицу Якоби выхода по координатам в виде numpy массива 6xN"""

        sens = self.sensivity2(body, local, basis)
        jacobian = numpy.zeros((6, len(sens)))

        for i in range(len(sens)):
            wsens = sens[i].ang.to_array()
            vsens = sens[i].lin.to_array()

            jacobian[0:3, i] = wsens
            jacobian[3:6, i] = vsens

        return jacobian

    def translation_sensitivity_jacobian2(self, body, local, basis=None):
        """Вернуть матрицу Якоби трансляции выхода по координатам в виде numpy массива 3xN"""

        sens = self.sensivity2(body, local, basis)
        jacobian = numpy.zeros((3, len(sens)))

        for i in range(len(sens)):
            vsens = sens[i].lin.to_array()
            jacobian[0:3, i] = vsens

        return jacobian


    def sensivity(self, basis=None):
        """Вернуть массив тензоров производных положения выходного
        звена по вектору координат в виде [(w_i, v_i) ...]"""

        return self.sensivity2(self.distant, nulltrans(), basis)

    def sensivity_jacobian(self, basis=None):
        """Вернуть матрицу Якоби выхода по координатам в виде numpy массива 6xN"""

        sens = self.sensivity(basis)
        jacobian = numpy.zeros((6, len(sens)))

        for i in range(len(sens)):
            wsens = sens[i].ang.to_array()
            vsens = sens[i].lin.to_array()

            jacobian[0:3, i] = wsens
            jacobian[3:6, i] = vsens

        return jacobian

    def translation_sensivity_jacobian(self, basis=None):
        """Вернуть матрицу Якоби трансляции выхода по координатам в виде numpy массива 3xN"""

        sens = self.sensivity(basis)
        jacobian = numpy.zeros((3, len(sens)))

        for i in range(len(sens)):
            vsens = sens[i].lin.to_array()
            jacobian[0:3, i] = vsens

        return jacobian

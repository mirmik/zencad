import zencad.assemble
import zencad.libs.screw
import numpy
import time

from abc import ABC, abstractmethod

from zencad.assemble import kinematic_unit


class kinematic_chain:
    """Объект-алгоритм управления участком кинематической чепи от точки
    выхода, до точки входа.

    Порядок следования обратный, потому что звено может иметь одного родителя,
    но много потомков. Цепочка собирается по родителю.

    finallink - конечное звено.
    startlink - начальное звено. 
            Если не указано, алгоритм проходит до абсолютной СК"""

    def __init__(self, finallink, startlink=None):
        self.chain = self.collect_chain(finallink, startlink)
        self.simplified_chain = self.simplify_chain(self.chain)
        self.kinematic_pairs = self.collect_kinematic_pairs()

    def collect_kinematic_pairs(self):
        par = []
        for l in self.chain:
            if isinstance(l, kinematic_unit):
                par.append(l)
        return par

    # def collect_coords(self):
    #	arr = []
    #	for l in self.parametered_links:
    #		arr.append(l.coord)
    #	return arr

    def apply(self, speeds, delta):
        for i in range(len(speeds)):
            k = self.kinematic_pairs[len(self.kinematic_pairs) - i - 1]
            k.set_coord(k.coord + speeds[i] * delta)

    @staticmethod
    def collect_chain(finallink, startlink=None):
        chain = []
        link = finallink

        while link is not startlink:
            chain.append(link)
            link = link.parent

        if startlink is not None:
            chain.append(startlink)

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
                    tmp = tmp * l.location

        if tmp is not None:
            ret.append(tmp)

        return ret

    def getchain(self):
        return self.chain

    def sensivity(self, basis=None):
        """Вернуть массив тензоров производных положения выходного
        звена по вектору координат в виде [(w_i, v_i) ...]"""

        trsf = _nulltrans()
        senses = []

        outtrans = self.chain[0].global_location

        """Два разных алгоритма получения масива тензоров чувствительности.
		Первый - проход по цепи с аккумулированием тензора трансформации.
		Второй - по глобальным объектам трансформации

		Возможно следует использовать второй и сразу же перегонять в btrsf вместо outtrans"""

        if False:
            for link in self.simplified_chain:
                if isinstance(link, Transformation):
                    trsf = link * trsf

                else:
                    lsenses = link.senses()
                    radius = trsf.translation()

                    for sens in reversed(lsenses):

                        wsens = sens[0]
                        vsens = wsens.cross(radius) + sens[1]

                        itrsf = trsf.inverse()

                        senses.append((
                            itrsf(wsens),
                            itrsf(vsens)
                        ))

                    trsf = link.location * trsf

        else:
            for link in self.kinematic_pairs:
                lsenses = link.senses()

                linktrans = link.output.global_location
                trsf = linktrans.inverse() * outtrans

                radius = trsf.translation()

                for sens in reversed(lsenses):

                    wsens = sens[0]
                    vsens = wsens.cross(radius) + sens[1]

                    itrsf = trsf.inverse()

                    senses.append((
                        itrsf(wsens),
                        itrsf(vsens)
                    ))

        """Для удобства интерпретации удобно перегнать выход в интуитивный базис."""
        if basis is not None:
            btrsf = basis.global_location
            #trsf =  btrsf * outtrans.inverse()
            # trsf =  outtrans * btrsf.inverse() #ok
            trsf = btrsf.inverse() * outtrans  # ok
            #trsf =  outtrans.inverse() * btrsf
            #trsf =  trsf.inverse()

            senses = [(trsf(w), trsf(v)) for w, v in senses]

        senses = [zencad.libs.screw.screw(ang=s[0], lin=s[1]) for s in senses]

        return list(reversed(senses))

    def decompose(self, vec, use_base_frame=False):
        sens = self.sensivity(self.chain[-1] if use_base_frame else None)
        #sens = self.sensivity(None)
        sens = [s.to_array() for s in sens]
        target = vec.to_array()
        return zencad.malgo.svd_backpack(target, sens)[0]

    def decompose_linear(self, vec, use_base_frame=False, maxsig=2, maxnorm=1,
                         priority=None):
        a = time.time()
        sens = self.sensivity(self.chain[-1] if use_base_frame else None)
        b = time.time()
        #sens = self.sensivity(None)
        sens = [s.lin for s in sens]
        target = vec

        if priority:
            for i in range(len(sens)):
                sens[i] = sens[i] * priority[i]

        # for i in range(len(sens)):
        #	print(abs(sens[i].dot(target)))
            # if abs(sens[i].dot(target)) > 10:
            #	sens[i] = (0,0,0)
        # print(sens)
        sigs = zencad.malgo.svd_backpack(target, sens)[0]
        c = time.time()

        if priority:
            for i in range(len(sens)):
                sigs[i] = sigs[i] * priority[i]
        # print(sigs)
        # print(sigs)

        #norm = numpy.linalg.norm(sigs)
        # if norm > maxnorm:
        #	sigs = sigs / norm * maxnorm
        # print(sigs)
        # if norm > maxnorm:
        #	sigs = sigs / norm * maxnorm

        #ssigs = list(sigs)
        # print(ssigs)
        # for i in range(len(sigs)):
        #	if abs(ssigs[i]) > maxsig:
        #		ssigs[i] = 0

        #print(b-a, c-b)

        return sigs

    def kunit(self, num):
        return self.kinematic_pairs[-num-1]

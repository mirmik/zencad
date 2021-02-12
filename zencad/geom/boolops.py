from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCC.Core.TopoDS import TopoDS_Shape

from zencad.shape import shape_generator, Shape
from zencad.lazy import lazy
from zencad.geom.boolops_base import occ_pair_union, occ_pair_difference, occ_pair_intersect

@lazy.lazy(cls=shape_generator)
def union(lst):
	if len(lst) == 1: 
		return Shape(lst[0])

	nrsize = 0
	rsize = len(lst) // 2 + len(lst) % 2

	narr = [ TopoDS_Shape() for i in range(rsize) ]

	for i in range(len(lst) // 2):
		narr[i] = occ_pair_union(lst[i].Shape(), lst[len(lst) - i - 1].Shape())

	if len(lst) % 2:
		narr[rsize - 1] = lst[len(lst) // 2].Shape()

	while rsize != 1:
		nrsize = rsize // 2 + rsize % 2

		for i in range(rsize // 2):
			narr[i] = occ_pair_union(narr[i], narr[rsize - i - 1]);

		if rsize % 2:
			narr[nrsize - 1] = narr[rsize // 2]

		rsize = nrsize

	return Shape(narr[0])

@lazy.lazy(cls=shape_generator)
def difference(lst):
	pass

@lazy.lazy(cls=shape_generator)
def intersect(lst):
	pass
#servoce::shape servoce::make_difference(const std::lsttor<const servoce::shape*>& lst)
#{
#	TopoDS_Shape ret = lst[0]->Shape();
#
#	for (unsigned int i = 1; i < lst.size(); ++i)
#	{
#		ret = __make_difference(ret, lst[i]->Shape());
#	}
#
#	return ret;
#}
#
#servoce::shape servoce::make_intersect(const std::lsttor<const servoce::shape*>& lst)
#{
#	TopoDS_Shape ret = lst[0]->Shape();
#
#	for (unsigned int i = 1; i < lst.size(); ++i)
#	{
#		ret = __make_intersect(ret, lst[i]->Shape());
#	}
#
#	return ret;
#}
#
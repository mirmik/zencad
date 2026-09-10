#!/usr/bin/env python3
"""Execute symbolic reference calls using concrete, independent fixtures."""
import ast
import math
import re

from main import ROOT as MANGEN, localized

# Each symbolic block is run statement-by-statement with fresh geometry. This
# preserves the intended meaning of alternative spellings (especially builders).
CASES = {
    'assemble': {0:'ShapeInteractiveObject', 1:'NoneType', 3:'NoneType', 4:'NoneType', 5:'NoneType'},
    'bool': {0: 'Shape', 2: 'Shape', 4: 'Shape', 6: 'Shape'},
    'fillet': {0: 'Shape', 1: 'Shape', 3: 'Solid'},
    'ops3d': {0: 'Shape', 2: 'Face', 4: 'Solid'},
    'other': {0: 'Solid'},
    'prim1d': {0: 'Edge', 1: 'Wire', 2: 'Edge', 3: 'Edge', 4: 'Wire',
               5: 'Edge', 6: 'Edge', 7: 'Wire', 9: 'Wire',
               12: 'WireBuilder', 14: 'WireBuilder', 16: 'WireBuilder',
               17: 'WireBuilder', 18: 'WireBuilder'},
    'prim2d': {0: 'Face', 1: 'Face', 2: 'Face', 3: 'Face', 4: 'Face',
               5: 'Compound', 8: 'Face', 10: 'Face'},
    'prim3d': {0: 'Solid', 2: 'Solid', 4: 'Solid', 6: 'Solid', 8: 'Solid', 11: 'Solid'},
    'reflect': {0: 'bool', 2: 'ShapeList', 3: ('Edge', 'Face', 'Vertex'), 4: 'Solid'},
    'surfalgo': {0: 'Vector3'},
    'sweep': {0: 'Shape', 3: 'Solid', 5: 'Shape', 7: 'Solid'},
    'trans0': {0: 'Solid', 1: 'Transform', 2: 'Solid', 3: 'Transform',
               4: 'Solid', 5: ('Transform','AffineTransform','AffineTransform','AffineTransform','AffineTransform'),
               6: 'Solid', 7: 'Transform', 9: 'Transform', 12: 'Transform',
               13: 'Transform', 15: ('list','Shape'), 17: 'MultiTransform',
               19: 'MultiTransform', 21: 'MultiTransform'},
}


def fixtures(page, index):
    import zencad as z
    from zencad.geom.wire_builder import WireBuilder
    from zencad.geom.exttrans import MultiTransform
    from zencad.assemble import unit
    from zencad.scene import Scene
    ns = dict(vars(z), zencad=z, math=math, WireBuilder=WireBuilder,
              MultiTransform=MultiTransform, bool=bool, list=list)
    shape = z.box(10)
    ns.update(u=unit(parts=[shape]), child=unit(), obj=shape, scene=Scene(), location=z.translate(2,3,4),
              shp=shape, shape=shape, model=shape, proto=shape,
              shp0=shape, shp1=z.box(10).right(5), array=[shape,z.box(10).right(5)],
              radius=1, thickness=-1, referencedPoints=[z.point3(0,0,0)],
              x=2, y=3, z=4, a=2, r=1, h=6, height=6, step=2,
              angle=.5, yaw=math.pi, minPitch=-.5, maxPitch=.5,
              botRadius=3, topRadius=1, centralRadius=5, localRadius=1,
              major=4, minor=2, start=0, stop=math.pi, vertexCount=6,
              nfaces=12, n=4, distance=1, vec=(0,0,5),
              pnt=z.point3(0,0,0), pnt1=(0,0,0),pnt2=(4,0,0),
              p1=(0,0,0),p2=(2,1,0),p3=(4,0,0),
              pnts=[(0,0,0),(10,0,0),(10,10,0),(20,10,0)],
              weights=[1,2,2,1],knots=[0,1],muls=[4,4],degree=3,
              text='ZenCad',fontname='Mandarinc',size=5,
              face=z.square(10), surface=z.square(10).surface(),
              wire=z.rectangle(10,10,wire=True),
              wires=[z.segment((0,0,0),(10,0,0)),z.segment((10,0,0),(10,10,0))],
              profiles=[z.circle(2,wire=True),z.circle(3,wire=True).up(10)],
              spine=z.segment((0,0,0),(0,0,10)),
              profile=z.square(2).rotateX(math.pi/2).right(5),
              trsf=z.translate(2,3,4)*z.rotateZ(.7), f=(0,0,1), t=(1,0,0),
              transes=[z.translate(20,0,0),z.translate(-20,0,0)],
              wb=z.wire_builder(start=(-5,-5,0)).segment((-2,-2,0)), b=(5,0,0))
    if page=='fillet' and index==3:
        ns['referencedPoints']=[z.point3(5,5,10)]
    if page=='ops3d' and index==2:
        ns.update(a=z.circle(2,wire=True),b=z.circle(3,wire=True).up(10))
    if page=='bool' and index==6:
        ns.update(a=shape,b=z.infplane().up(5))
    if page=='prim1d' and index==16:
        ns.update(a=(0,2,0),b=(2,0,0))
    if page=='prim2d' and index==3:
        ns['pnts']=[(0,0,0),(10,0,0),(10,10,0),(0,10,0)]
    if page=='sweep' and index==7:
        ns.update(profile=z.square(2,center=True),r=5)
    if page=='prim2d' and index==10:
        ns['pnts']=z.points2([[(0,0,0),(0,5,1),(0,10,0)],
                              [(5,0,1),(5,5,2),(5,10,1)],
                              [(10,0,0),(10,5,1),(10,10,0)]])
    return ns


def check_symbolic_calls():
    import zencad as z
    z.register_font(str(MANGEN.parent/'zencad/examples/fonts/mandarinc.ttf'))
    count=0
    failures=[]
    for language in ('ru','en'):
        for page,cases in CASES.items():
            source=localized((MANGEN/'ru'/f'{page}.md').read_text(),language)
            blocks=re.findall(r'```python\n(.*?)```',source,re.S)
            for index,types in cases.items():
                statements=ast.parse(blocks[index]).body
                for number,statement in enumerate(statements):
                    label=f'{page}:{language}:{index}:{number}'
                    try:
                        ns=fixtures(page,index)
                        expression=statement.value
                        result=eval(compile(ast.Expression(expression),label,'eval'),ns)
                        expected=types if isinstance(types,str) else types[number]
                        assert type(result).__name__==expected, (type(result).__name__,expected)
                        if isinstance(result,z.Shape):
                            result.native()
                            assert not result.native().IsNull()
                            result.assert_valid()
                        elif isinstance(result,z.ShapeList):
                            kinds = {'vertices':'Vertex', 'solids':'Solid', 'faces':'Face',
                                     'edges':'Edge', 'wires':'Wire', 'shells':'Shell',
                                     'compounds':'Compound', 'compsolids':'CompSolid'}
                            for item in result:
                                assert type(item).__name__ == kinds[expression.func.attr]
                                item.native()
                        elif isinstance(result,(z.Transform,z.AffineTransform)):
                            result.matrix()
                        elif isinstance(result,z.Vector3):
                            assert math.isclose(float(result.length()),1,abs_tol=1e-8)
                        elif expected=='WireBuilder':
                            if page == 'prim1d' and index == 12:
                                assert not result.edges
                            else:
                                result.doit().native()
                        elif isinstance(result,list):
                            for item in result:item.native()
                        if page == 'assemble':
                            if index == 0:
                                assert result in ns['u'].dispobjects
                            elif index == 1:
                                assert ns['child'].parent is ns['u']
                            elif index == 4:
                                assert tuple(ns['u'].global_location.translation()) == (2,3,4)
                            elif index == 5:
                                assert ns['scene'].interactives == ns['u'].dispobjects
                        count+=1
                    except Exception as error:
                        failures.append(f'{label}: {ast.unparse(statement)}: {type(error).__name__}: {error}')
    if failures:
        raise AssertionError('\n'.join(failures))
    print(f'PASS {count} concrete symbolic calls and result types',flush=True)


def check_boundaries():
    import zencad as z

    def rejects(error_type, call):
        try:
            call()
        except error_type:
            return
        raise AssertionError(f"Expected {error_type.__name__}")

    box = z.box(10)
    cut = box - box
    assert len(cut.solids()) == 0
    assert type(z.restore_shapetype(cut)) is z.Shape
    multiple = z.union([box, box.right(20)])
    assert type(z.restore_shapetype(multiple)) is z.Shape
    assert len(multiple.solids()) == 2
    rejects(ValueError, lambda: multiple.solids().only().native())
    rejects(ValueError, lambda: cut.solids().only().native())
    assert isinstance(box.solids().only(), z.Solid)
    assert math.isclose(float(box.scaleXYZ(2, 3, 4).mass()), 24000, abs_tol=1e-7)
    assert math.isclose(float(box.mirrorYZ().mass()), 1000, abs_tol=1e-7)

    for operation in (z.fillet, z.chamfer):
        for references in ([z.point3(0,0,0)], [box.vertices()[0]], [box.edges()[0]]):
            result = operation(box, 1, references)
            result.assert_valid()
            assert 0 < float(result.mass()) < 1000
        rejects(ValueError, lambda: operation(box, 1, []).native())
        rejects(ValueError, lambda: operation(box, 1, [z.box(20).edges()[0]]).native())
        rejects(TypeError, lambda: operation(box, 1, [(0,0,0)]).native())
    rounded = z.fillet(z.square(10), 1)
    assert type(rounded) is z.Shape and len(rounded.faces()) == 1
    rounded.assert_valid()

    edge = z.segment((0,0,0),(10,0,0))
    wire = z.sew([edge, z.segment((10,0,0),(10,10,0))])
    assert type(wire) is z.Wire and not wire.is_closed()
    rejects(ValueError, lambda: z.sew([]))
    rejects(TypeError, lambda: z.sew([edge, z.square(10)]))
    rejects(ValueError, lambda: z.fill(edge).native())
    shell = z.sew(list(box.faces()))
    assert type(shell) is z.Shell
    shell.assert_valid()

    profiles = [z.circle(2,wire=True),z.circle(3,wire=True).up(10)]
    for shell_mode, kind in ((False,z.Solid),(True,z.Shell)):
        loft = z.loft(profiles,shell=shell_mode)
        assert type(loft) is kind
        loft.assert_valid()
    spine=z.segment((0,0,0),(0,0,10))
    for solid,kind in ((False,z.Shell),(True,z.Solid)):
        pipe=z.pipe_shell(profiles,spine,solid=solid)
        assert type(pipe) is kind
        pipe.assert_valid()
    for result in (z.loft([edge,edge.up(10)],shell=True),
                   z.pipe_shell([edge],spine,solid=False)):
        assert type(result) is z.Shell
        result.assert_valid()

    curve=z.bezier([(0,0,0),(0,10,0),(10,10,0),(10,0,0)]).curve()
    assert isinstance(curve.range(),z.Interval)
    assert tuple(float(v) for v in curve.d1(0).value()) == (0,30,0)
    assert all(isinstance(v,z.Point3) for v in curve.endpoints())
    for count in (0,1,-1,True):
        rejects(ValueError,lambda:curve.uniform(count))
    rejects(TypeError,lambda:curve.uniform(3,0))
    samples=curve.uniform(5)
    assert len(samples)==5 and all(isinstance(v,z.Scalar) for v in samples)
    assert math.isclose(float(samples[0]),0,abs_tol=1e-8)
    assert math.isclose(float(samples[-1]),1,abs_tol=1e-8)
    assert not math.isclose(float(samples[1]),.25,abs_tol=1e-3)
    assert len(curve.uniform_points(5))==5
    print('PASS boundary contracts: topology, references, sweeps, curves',flush=True)


def check_contracts():
    import zencad as z
    for context in (z.Context.immediate(cache=False), z.Context.deferred(cache=False)):
        with z.using_context(context):
            check_symbolic_calls()
            check_boundaries()


if __name__=='__main__':
    check_contracts()

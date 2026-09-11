#!/usr/bin/env python3
"""Check reference examples with their documented/shared model context.

Unlike the standalone tutorial snippets, reference blocks also contain symbolic
signatures. EXAMPLES identifies executable blocks (zero-based python-fence index).
Other blocks are syntax/API-call checked, not executed with invented geometry.
"""
import ast
import inspect
import math
from pathlib import Path
import re

from main import ROOT as MANGEN

EXAMPLES = {
    'helloworld': [0, 1, 2, 3, 4, 5], 'bbox': [0, 1],
    'prim0d': [2, 4, 5], 'trimesh': [0, 1, 3, 6, 8],
    'assemble': [2, 6], 'bool': [1, 3, 5, 7, 8, 9], 'crvalgo': [0, 1, 2],
    'fillet': [2], 'ops3d': [1, 3, 5],
    'prim1d': [7, 9, 11, 12, 14, 16, 20], 'prim2d': [6, 7, 9, 11],
    'prim3d': [1, 3, 5, 7, 9, 10, 12],
    'sweep': [1, 2, 4, 6, 8, 9], 'trans0': [8, 10, 11, 14, 16, 18, 20, 22, 23, 24],
    'surfalgo': [0, 1],
}


def check_reference():
    import zencad as z
    import zencad.showapi
    from zencad.assemble import unit

    zencad.showapi.NOSHOW = True
    evaluated = checked = 0

    def force(value):
        if isinstance(value, z.Shape):
            value.native()
        elif isinstance(value, (tuple, list)):
            for item in value:
                force(item)
        return value

    class MaterializeExpressions(ast.NodeTransformer):
        def visit_Expr(self, node):
            return ast.copy_location(ast.Expr(ast.Call(
                ast.Name('_force', ast.Load()), [node.value], [])), node)

    for language in ('ru', 'en'):
        for page in sorted((MANGEN / language).glob('*.md')):
            source = page.read_text(encoding='utf-8')
            # Symbolic signatures still must name valid methods and bind arguments.
            owners = dict(vars(z), z=z, zencad=z, math=math)
            shape = z.box(10)
            owners.update(shp=shape, shape=shape, model=shape, trsf=z.transform(),
                          wb=z.wire_builder(), curve=z.segment((0, 0, 0), (1, 0, 0)),
                          face=z.square(10), surface=z.square(10).surface(), u=unit())
            for index, block in enumerate(re.findall(r'```python(?:3)?\s*\n(.*?)```', source, re.S)):
                tree = ast.parse(block, filename=f'{page.stem}:{language}:syntax:{index}')
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    # Resolve only bare functions and attributes of known owners;
                    # evaluating a nested call here would construct arbitrary geometry.
                    parts = []
                    expr = node.func
                    while isinstance(expr, ast.Attribute):
                        parts.append(expr.attr)
                        expr = expr.value
                    if not isinstance(expr, ast.Name) or expr.id not in owners:
                        continue
                    # Locally assigned variables may shadow public factory names.
                    assigned = {n.id for n in ast.walk(tree)
                                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
                    if expr.id in assigned:
                        continue
                    function = owners[expr.id]
                    for part in reversed(parts):
                        function = getattr(function, part)
                    try:
                        signature = inspect.signature(function)
                    except (ValueError, TypeError):
                        continue
                    if any(isinstance(arg, ast.Starred) for arg in node.args) or any(
                            kw.arg is None for kw in node.keywords):
                        continue
                    try:
                        signature.bind(*[None for _ in node.args],
                                       **{kw.arg: None for kw in node.keywords})
                    except TypeError as error:
                        raise AssertionError(f"{page.stem}:{language}:{index}: {ast.unparse(node)}: {error}") from error
                    checked += 1
            selected = EXAMPLES.get(page.stem)
            if selected is None:
                continue
            blocks = re.findall(r'```python\n(.*?)```', source, re.S)
            namespace = dict(vars(z), zencad=z, math=math, _force=force,
                             FONTPATH=str(MANGEN.parent / 'zencad/examples/fonts/testfont.ttf'),
                             FONTNAME='Ubuntu Mono')
            for index in selected:
                tree = MaterializeExpressions().visit(ast.parse(blocks[index]))
                exec(compile(ast.fix_missing_locations(tree),
                             f'{page.stem}:{language}:{index}', 'exec'), namespace)
                for key, value in list(namespace.items()):
                    if not key.startswith('_'):
                        force(value)
                evaluated += 1
    print(f'PASS {evaluated} reference examples, {checked} API call signatures', flush=True)


if __name__ == '__main__':
    check_reference()

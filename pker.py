import ast

BUILTIN_MACROS = (
    'GLOBAL',
    'INST',
    'OBJ',
    'RETURN',
)


def extract_value(v):
    if isinstance(v, ast.Num):
        return v.n
    elif isinstance(v, ast.Str):
        return v.s
    elif isinstance(v, ast.List):
        lst = [extract_value(elt) for elt in v.elts]
        return lst
    elif isinstance(v, ast.Tuple):
        tpl = tuple([extract_value(elt) for elt in v.elts])
        return tpl
    elif isinstance(v, ast.Dict):
        dct = {
            extract_value(key): extract_value(value)
            for key in v.keys for value in v.values
        }
        return dct
    else:
        return v


def cons_basic_type(v):
    if isinstance(v, str):
        return cons_str(v)
    elif isinstance(v, (int, float)):
        return cons_num(v)
    elif isinstance(v, list):
        return cons_lst(v)
    elif isinstance(v, tuple):
        return cons_tpl(v)
    elif isinstance(v, dict):
        return cons_dct(v)
    else:
        return v


def cons_str(s):
    return "S'%s'\n" % s


def cons_num(n):
    if isinstance(n, int):
        return 'I%d\n' % n
    elif isinstance(n, float):
        return 'F%s\n' % n


def cons_lst(lst):
    buf = ['(']
    for cell in lst:
        buf.append(cons_basic_type(cell))
    buf.append('l')
    return ''.join(buf)


def cons_tpl(tpl):
    buf = ['(']
    for cell in tpl:
        buf.append(cons_basic_type(cell))
    buf.append('t')
    return ''.join(buf)


def cons_dct(dct):
    buf = ['(']
    for k, v in dct.items():
        if isinstance(k, str):
            buf.append(cons_str(k))
        elif isinstance(k, (int, float)):
            buf.append(cons_num(k))
        elif isinstance(k, tuple):
            buf.append(cons_tpl(k))

        buf.append(cons_basic_type(v))

    buf.append('d')
    return ''.join(buf)


def cons_item_assign(obj_name, item_k, item_v, lookup_memo):
    buf = [cons_defined_var(obj_name, lookup_memo)]

    buf.append(cons_basic_type(extract_value(item_k)))
    if isinstance(item_v, ast.Name):
        buf.append(cons_defined_var(item_v.id, lookup_memo))
    elif isinstance(item_v, ast.Call):
        buf.append(cons_invoke(item_v, lookup_memo))
    else:
        buf.append(cons_basic_type(extract_value(item_v)))
    buf.append('s')
    return ''.join(buf)


def cons_defined_var(varname, lookup_memo):
    return 'g%d\n' % lookup_memo(varname)


def cons_attr_assign(obj_name, attr_k, attr_v, lookup_memo):
    buf = [cons_defined_var(obj_name, lookup_memo)]
    buf.append('(}(')
    buf.append("S'%s'\n" % attr_k)

    if isinstance(attr_v, ast.Name):
        buf.append(cons_defined_var(attr_v.id, lookup_memo))
    elif isinstance(attr_v, ast.Call):
        buf.append(cons_invoke(attr_v, lookup_memo))
    else:
        buf.append(cons_basic_type(extract_value(attr_v)))
    buf.append('dtb')
    return ''.join(buf)


def cons_builtin_macros(macro_name, args, lookup_memo):
    buf = []
    if macro_name == 'GLOBAL':
        if len(args) != 2:
            raise Exception(
                'Macro `GLOBAL` takes 2 argumenmts but %d was given' %
                len(args))

        buf.append('c')
        for arg in args:
            if isinstance(arg, str):
                buf.append(arg + '\n')
            else:
                raise Exception('Macro `GLOBAL` takes `str` type arguments')

    elif macro_name == 'INST':
        if len(args) < 2:
            raise Exception('Macro `INST` takes at least 2 argumenmts')

        buf.append('(')
        for arg in args[2:]:
            buf.append(cons_basic_type(arg))
        buf.append('i')
        for arg in args[:2]:
            if isinstance(arg, str):
                buf.append(arg + '\n')
            else:
                raise Exception(
                    'Macro `INST` needs the first 2 arguments are `str` type')

    elif macro_name == 'OBJ':
        if len(args) < 1:
            raise Exception('Macro `OBJ` takes at least 1 argumenmt')

        buf.append('(')
        callable_obj = args[0]
        if isinstance(callable_obj, ast.Name):
            buf.append(cons_defined_var(callable_obj.id, lookup_memo))
        elif isinstance(callable_obj, ast.Call):
            buf.append(
                cons_builtin_macros(
                    callable_obj.func.id,
                    [extract_value(arg) for arg in callable_obj.args], None))

        for arg in args[1:]:
            buf.append(cons_basic_type(arg))
        buf.append('o')

    return ''.join(buf)


def cons_func(fn_name, args, lookup_memo):
    args = [
        cons_defined_var(arg.id, lookup_memo)
        if isinstance(arg, ast.Name) else cons_basic_type(arg) for arg in args
    ]

    args = [
        cons_func(arg.func.id, [extract_value(arg_t)
                                for arg_t in arg.args], lookup_memo)
        if isinstance(arg, ast.Call) else arg for arg in args
    ]

    buf = [cons_defined_var(fn_name, lookup_memo)]
    buf.append('(')
    [buf.append(arg) for arg in args]
    buf.append('tR')
    return ''.join(buf)


def cons_invoke(node, lookup_memo):
    fn_name = node.func.id
    args = [extract_value(arg) for arg in node.args]

    if fn_name in BUILTIN_MACROS:
        return cons_builtin_macros(fn_name, args, lookup_memo)
    else:
        return cons_func(fn_name, args, lookup_memo)


class Pickler(object):
    def __init__(self):
        self._context = {}
        self._memo_index = 0
        self._output = []

    def __setitem__(self, key, value):
        if isinstance(key, ast.Name):
            self._context[key.id] = self._memo_index

            if not isinstance(value, ast.Call):
                self.push(
                    cons_basic_type(extract_value(value)) + self.gen_memo())

            elif isinstance(value, ast.Call):
                self.push(
                    cons_invoke(value, self.lookup_memo) + self.gen_memo())

        elif isinstance(key, ast.Subscript):
            self.push(
                cons_item_assign(key.value.id, key.slice.value, value,
                                 self.lookup_memo))

        elif isinstance(key, ast.Attribute):
            self.push(
                cons_attr_assign(key.value.id, key.attr, value,
                                 self.lookup_memo))

        self._memo_index += 1

    def gen_memo(self):
        return 'p%d\n0' % self._memo_index

    def lookup_memo(self, varname):
        memo_index = self._context.get(varname)
        if memo_index is None:
            raise Exception('Variable `%s` is not defined' % varname)
        return memo_index

    def push(self, s):
        self._output.append(s)

    def output(self):
        return ''.join(self._output)

    def terminat(self, obj):
        if obj is not None:
            if isinstance(obj, ast.Name):
                self.push('g%d\n' % self.lookup_memo(obj.id))
            else:
                self.push(cons_basic_type(extract_value(obj)))
        self.push('.')

    def invoke(self, node):
        self.push(cons_invoke(node, self.lookup_memo))


class Parser(ast.NodeVisitor):
    def __init__(self):
        self._pickler = Pickler()

    def visit_Assign(self, node):
        target = node.targets[0]
        value = node.value
        self._pickler[target] = value

    def visit_Call(self, node):
        self._pickler.invoke(node)

    def visit_Return(self, node):
        self._pickler.terminat(node.value)


code = []
try:
    while True:
        code.append(input() + '\n')
except EOFError:
    pass
code = ''.join(code)

root = ast.parse(code)

p = Parser()
p.visit(root)
print(''.join(p._pickler.output()).encode())

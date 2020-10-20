import ast

BUILTIN_MACROS = (
    'GLOBAL',
    'INST',
    'OBJ',
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
    elif isinstance(v, ast.Call):
        return cons_invoke(v)
    elif isinstance(v, ast.Name):
        return cons_defined_var(v.id)
    else:
        return v


def cons_str(s):
    return "S'%s'\n" % s.replace('\\', '\\\\').replace("'", "\\'")


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
        buf.append(cons_basic_type(k))
        buf.append(cons_basic_type(v))

    buf.append('d')
    return ''.join(buf)


def cons_item_assign(obj_name, item_k, item_v):
    buf = [cons_defined_var(obj_name)]
    buf.append(cons_basic_type(extract_value(item_k)))
    buf.append(cons_basic_type(extract_value(item_v)))
    buf.append('s')
    return ''.join(buf)


def cons_defined_var(varname):
    return 'g%d\n' % lookup_memo(varname)


def cons_attr_assign(obj_name, attr_k, attr_v):
    buf = [cons_defined_var(obj_name)]
    buf.append('(}(')
    buf.append("S'%s'\n" % attr_k)
    buf.append(cons_basic_type(extract_value(attr_v)))
    buf.append('dtb')
    return ''.join(buf)


def cons_builtin_macros(macro_name, args):
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
            buf.append(cons_defined_var(callable_obj.id))
        elif isinstance(callable_obj, ast.Call):
            buf.append(
                cons_builtin_macros(
                    callable_obj.func.id,
                    [extract_value(arg) for arg in callable_obj.args]))

        for arg in args[1:]:
            buf.append(cons_basic_type(arg))
        buf.append('o')

    return ''.join(buf)


def cons_func(fn_name, args):
    buf = [cons_defined_var(fn_name)]
    buf.append(cons_args(args))
    return ''.join(buf)


def cons_args(args):
    args = [cons_basic_type(arg) for arg in args]
    buf = ['(']
    [buf.append(arg) for arg in args]
    buf.append('tR')
    return ''.join(buf)


def cons_invoke(node):
    args = [extract_value(arg) for arg in node.args]

    if isinstance(node.func, ast.Name):
        fn_name = node.func.id

        if fn_name in BUILTIN_MACROS:
            return cons_builtin_macros(fn_name, args)
        else:
            return cons_func(fn_name, args)

    elif isinstance(node.func, ast.Call):
        return cons_invoke(node.func) + cons_args(args)


class Pickler(object):
    def __init__(self):
        self._context = {}
        self._memo_index = 0
        self._output = []
        globals()['lookup_memo'] = self.lookup_memo

    def __setitem__(self, key, value):
        if isinstance(key, ast.Name):
            if key.id in BUILTIN_MACROS:
                raise Exception('Can\'t assign to built-in macros %s' % key.id)

            self._context[key.id] = self._memo_index
            self.push(cons_basic_type(extract_value(value)) + self.gen_memo())

        elif isinstance(key, ast.Subscript):
            self.push(cons_item_assign(key.value.id, key.slice.value, value))

        elif isinstance(key, ast.Attribute):
            self.push(cons_attr_assign(key.value.id, key.attr, value))

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

    def terminat(self, obj):
        if obj is not None:
            if isinstance(obj, ast.Name):
                self.push('g%d\n' % self.lookup_memo(obj.id))
            else:
                self.push(cons_basic_type(extract_value(obj)))
        self.push('.')

    def invoke(self, node):
        self.push(cons_invoke(node))


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

    def output(self):
        return ''.join(self._pickler._output)


def cons(c):
    root = ast.parse(c)
    p = Parser()
    p.visit(root)
    return p.output().encode()


if __name__ == '__main__':
    code = []
    try:
        while True:
            code.append(input() + '\n')
    except EOFError:
        pass
    code = ''.join(code)
    print(cons(code))


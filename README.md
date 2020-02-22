# pker

Tools for converting Python source code to Pickle opcode automatically, see `https://xz.aliyun.com/t/7012`

## Usage

Write code with normal Python syntax: 

```python
i = 0
s = 'id'
lst = [i]
tpl = (0,)
dct = {tpl: 0}
system = GLOBAL('os', 'system')
system(s)
return
```

```
$ python3 pker.py < x
b"I0\np0\n0S'id'\np1\n0(g0\nlp2\n0(I0\ntp3\n0(g3\nI0\ndp4\n0cos\nsystem\np5\n0g5\n(g1\ntR."
```

***

Nested complex expressions are ok

```python
getattr = GLOBAL('__builtin__', 'getattr')
get = getattr(GLOBAL('__builtin__', 'dict'), 'get')
__builtins__ = get(GLOBAL('__builtin__', 'globals')(), '__builtins__')

f = getattr(__builtins__, 'getattr')(__builtins__, 'getattr')(__builtins__, 'getattr')(__builtins__, 'getattr')(__builtins__, 'getattr')
sin = GLOBAL('math', 'sin')
k = {sin(sin(sin(sin(sin(1))))): {(1, 2): [0, f]}}
return k
```

```
$ python3 pker.py < x
b"c__builtin__\ngetattr\np0\n0g0\n(c__builtin__\ndict\nS'get'\ntRp1\n0g1\n(c__builtin__\nglobals\n(tRS'__builtins__'\ntRp2\n0g0\n(g2\nS'getattr'\ntR(g2\nS'getattr'\ntR(g2\nS'getattr'\ntR(g2\nS'getattr'\ntR(g2\nS'getattr'\ntRp3\n0cmath\nsin\np4\n0(g4\n(g4\n(g4\n(g4\n(g4\n(I1\ntRtRtRtRtR((I1\nI2\nt(I0\ng3\nlddp5\n0g5\n."

$ python3 pker.py < x | python3 ../test.py
{0.5871809965734309: {(1, 2): [0, <built-in function getattr>]}}
```

***

The differences from normal Python code are: 

+ there are 3 built-in macros

  ```
  GLOBAL('os', 'system')             =>  cos\nsystem\n
  INST('os', 'system', 'ls')         =>  (S'ls'\nios\nsystem\n
  OBJ(GLOBAL('os', 'system'), 'ls')  =>  (cos\nsystem\nS'ls'\no
  ```

+ `return` expression could be used outside of the function

  ```
  var = 1
  return var
  ```

  ```
  return           =>  .
  return var       =>  g_\n.
  return 1         =>  I1\n.
  ```


Examples are in pker/test

# pker

Tools for converting Python source code to Pickle opcode automatically

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
sin = GLOBAL('math', 'sin')
k = {sin(sin(sin(sin(sin(sin(1)))))): {(1, 2): [1, 2, 3]}}
return k
```

```
$ python3 pker.py < x
b'cmath\nsin\np0\n0(g0\n(g0\n(g0\n(g0\n(g0\n(g0\n(I1\ntRtRtRtRtRtR((I1\nI2\nt(I1\nI2\nI3\nlddp1\n0g1\n.'

$ python3 pker.py < x | python3 ../read.py
{0.5540163907556296: {(1, 2): [1, 2, 3]}}
```

***

The differences from normal Python code are: 

+ there are 3 builtin-macros

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

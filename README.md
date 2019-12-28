# pker

Tools for converting Python source code to Pickle opcode automatically

## Usage

Write code using Python syntax: 

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

The only difference is that there are 3 builtin-macros: 

```
GLOBAL('os', 'system')             =>  cos\nsystem\n
INST('os', 'system', 'ls')         =>  (S'ls'\nios\nsystem\n
OBJ(GLOBAL('os', 'system'), 'ls')  =>  (cos\nsystem\nS'ls'\no
```

Examples are in pker/test

# pker

Tools for converting Python source code to Pickle opcode automatically

## Usage

Write code using Python syntax, the only difference is that there are 3 builtin-macros: 

```
GLOBAL('os', 'system')             =>  cos\nsystem\n
INST('os', 'system', 'ls')         =>  (S'ls'\nios\nsystem\n
OBJ(GLOBAL('os', 'system'), 'ls')  =>  (cos\nsystem\nS'ls'\no
```

Example is in pker/test


## Brica

taken from https://github.com/ganeshredcobra/osc_breakout

a simple breakout game using osc as input

### requirements

pygame and python-liblo are required, they are packaged by main linux distributions

### usage

```
python brica.py
```

brica expects messages on port 1200, on the /head osc address and in the format

```
double,double
```

probably with the idea of getting data from an XY pad. Only the first value is used.

We can send it a custom package of the form

```
rx_d,ry_d
```

for example.

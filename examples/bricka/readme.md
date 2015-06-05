## Brica

taken from https://github.com/ganeshredcobra/osc_breakout

a simple breakout game using osc as input

### requirements

pygame and python-liblo are required, they are packaged by main linux distributions

### usage

```
python bricka.py
```

bricka expects messages on port 12000, on the /head osc address and in the format

```
double,double
```

probably with the idea of getting data from an XY pad. Only the first value is used.

We can send it a custom package of the form

```
rx_d,ry_d
```

for example.

### Note

Brica doesn't exit cleanly on escape, you need to use ctrl-c in the shell that started it (or xkill if you started it graphically)

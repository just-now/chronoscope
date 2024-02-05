![pytest/systest workflow](https://github.com/just-now/chronoscope/actions/workflows/python-package.yml/badge.svg)
![systest workflow](https://github.com/just-now/chronoscope/actions/workflows/makefile.yml/badge.svg)

# chronoscope
Chronoscope, a cross-platform matplotlib-based observability tool

## Chart
![alt text](https://github.com/just-now/chronoscope/blob/master/img/chart1.png)

## Definitions

```math
\mathcal{S} \subset \mathbb{N}.
```

```math
\mathcal{T} = \left\langle  \mathbb{T},\prec   \right\rangle.
```

```math
\mathcal{A}:\mathcal{S}\times\Sigma^{c}\times\Sigma^{c}.
```

```math
\mathcal{K}:\mathcal{S}\times\mathcal{S}\times\Sigma^{c}.
```

```math
\mathcal{R}:\mathcal{S}\times\mathcal{S}.
```

```math
relation \triangleq \left\langle origin: \mathcal{S}, dest: \mathcal{S} \right\rangle.
```

```math
tick \triangleq \left\langle sm: \mathcal{S}, time: \mathcal{T}, event: \Sigma^{c} \right\rangle.
```

```math
attr \triangleq \left\langle sm: \mathcal{S}, key: \Sigma^{c}, val: \Sigma^{c} \right\rangle.
```

## Notes

### Note 0.0
```math
iter_1: \mathcal{S} \to \left\{ \mathcal{S^{1}}, ... \mathcal{S^{p}} \right\},
```

```math
iter_1(sm) = \left\{ dest(related\_sm) | related\_sm \in \left\{ rel \in \mathcal{R} | origin(rel) = sm \right\}  \right\},
```

```math
p = \left| iter_1(sm) \right|.
```

### Note 0.1
```math
height: \mathcal{S} \to \mathbb{N},
```

```math
height(sm_i) = 1 + max(\left\{ height(sm_i) | sm_i \in iter_1(sm_i) \right\}),
```

```math
max(\varnothing) = 0.
```

### Note 0.2

```math
 iter: \mathcal{S} \to \left\{ \mathcal{S^{1}}, ... \mathcal{S^{r}} \right\},
```

```math
iter(sm_i) = \left\{ sm_i \right\} \cup \bigcup_{i=1}^{height(sm_i)-1}\left( \left\{ iter_1(sm_{i+1}) | iter_1(sm_{i+1}) \in iter_1(sm_i)\right\} \right),
```

```math
r = \sum_{i=0}^{height(sm_i)}\left| iter_1(sm_i) \right|.
```

### Note 1
```math
timeline: \mathcal{S} \to \left\{ \mathcal{K^{1}}, ... \mathcal{K^{q}} \right\},
```

```math
timeline(sm_i) = \left\{ tick \in \mathcal{K} | sm(tick)=sm_i \right\},
```

```math
q=\left| timeline(sm_i) \right|.
```

### Note 2
```math
chart: \mathcal{S} \to \left\{   \left\{ \mathcal{K^{1}}, ... \mathcal{K^{q}} \right\}^{1}, ... \left\{ \mathcal{K^{1}}, ... \mathcal{K^{q}} \right\}^{r}    \right\}
```

```math
chart(sm_i) = \left\{ timeline(sm) | sm \in iter(sm_i) \right\},
```

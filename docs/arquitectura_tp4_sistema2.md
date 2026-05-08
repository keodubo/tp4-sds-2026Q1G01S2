# Arquitectura TP4 - Sistema 2

Este documento define la arquitectura conceptual y el contrato de output para el
Sistema 2 del TP4. El objetivo es separar con claridad:

- el motor de simulacion por paso temporal fijo;
- el modelo fisico y las ecuaciones implementadas;
- los datos crudos que salen del motor;
- el analisis posterior que calcula observables.

No define implementacion concreta ni clases finales. Define responsabilidades y
fronteras para evitar mezclar simulacion con analisis.

## Decisiones cerradas del problema

- El recinto circular tiene diametro `L = 80 m`.
- El radio externo del recinto es `R = L / 2 = 40 m`.
- El obstaculo central fijo tiene radio `r0 = 1 m`.
- Las particulas tienen radio `rp = 1 m`, masa `m = 1 kg` y velocidad inicial
  de modulo `v0 = 1 m/s`.
- El sistema es puramente elastico conservativo: no hay disipacion ni friccion.
- La dinamica se resuelve con paso temporal fijo `dt`.
- La interaccion de contacto es elastica lineal:

```text
F_i = -k * xi * n_ij
xi = r_i + r_j - |x_i - x_j|, si xi > 0
```

donde `n_ij` es la normal unitaria definida por el contrato de contactos.

Para el recinto circular, los centros de las particulas deben permanecer en el
anillo fisicamente accesible:

```text
r0 + rp <= |x_i| <= R - rp
```

Con los valores del problema:

```text
2 m <= |x_i| <= 39 m
```

## Modulos del proyecto

Los nombres son logicos. Pueden mapearse a paquetes Java, modulos Python o la
estructura final elegida, pero la separacion de responsabilidades debe
mantenerse.

```text
common/
  config/
  math/
  output/

system2/
  model/
  state/
  contacts/
  forces/
  integrators/
  engine/
  output/

analysis-python/
  system2/
```

## Responsabilidades exactas

### `common/config`

Responsable de cargar y validar parametros compartidos.

Debe contener:

- parametros numericos de corrida;
- cantidad de particulas `N`;
- `L`, `R`, `r0`, `rp`, `m`, `k`, `v0`, `dt`;
- tiempo total o cantidad de pasos;
- semilla aleatoria;
- frecuencia de escritura;
- identificador de realizacion.

No debe contener:

- calculo de observables;
- reglas de contacto;
- logica de integracion.

### `common/math`

Responsable de primitivas matematicas simples.

Debe contener:

- vectores 2D;
- norma, distancia, producto escalar;
- operaciones auxiliares deterministas.

No debe contener conocimiento del Sistema 2, de particulas ni de observables.

### `system2/model`

Responsable de representar el modelo fisico.

Debe contener:

- geometria circular del sistema;
- definicion del obstaculo central;
- propiedades fisicas de particulas;
- parametros de la ley elastica;
- convenciones de unidades.

No debe:

- avanzar el tiempo;
- escribir archivos;
- calcular `Cfc(t)`, `J`, `Fu(t)` ni energia total.

### `system2/state`

Responsable de representar el estado dinamico instantaneo.

Debe contener:

- `step`;
- `t`;
- para cada particula: `id`, `x`, `y`, `vx`, `vy`.

Puede contener, si el integrador lo requiere:

- fuerza actual por particula;
- aceleracion actual por particula.

No debe contener:

- bandera `fresh/used`;
- acumuladores de contactos;
- histogramas;
- valores de energia;
- resultados de regresiones.

La condicion `fresh/used` pertenece al analisis, porque no afecta la dinamica
fisica.

### `system2/contacts`

Responsable de detectar contactos geometricos en un estado dado.

Debe detectar:

- contacto particula-particula;
- contacto particula-obstaculo;
- contacto particula-pared externa.

Debe devolver una lista de contactos activos con:

- tipo de contacto;
- ids involucrados;
- distancia geometrica;
- solapamiento `xi`;
- normal unitaria;
- convencion de signo documentada.

No debe:

- calcular observables;
- decidir si una particula es fresca o usada;
- acumular episodios de contacto;
- integrar fuerzas en el tiempo.

#### Convencion de normales

Para un contacto particula-particula `(i, j)`:

```text
n_ij = (x_j - x_i) / |x_j - x_i|
xi = r_i + r_j - |x_j - x_i|
F_on_i = -k * xi * n_ij
F_on_j = +k * xi * n_ij
```

Para un contacto particula-obstaculo `(i, obstacle)`:

```text
n_iO = (x_obstacle - x_i) / |x_obstacle - x_i|
xi = r_i + r0 - |x_obstacle - x_i|
F_on_i = -k * xi * n_iO
F_on_obstacle = +k * xi * n_iO
```

Como el obstaculo esta en el origen, esta fuerza repele a la particula hacia
afuera.

Para un contacto particula-pared externa `(i, wall)`:

```text
n_iW = x_i / |x_i|
xi = |x_i| + r_i - R
F_on_i = -k * xi * n_iW
F_on_wall = +k * xi * n_iW
```

Esta fuerza empuja a la particula hacia adentro del recinto.

### `system2/forces`

Responsable de aplicar la ley elastica a los contactos activos.

Debe producir:

- fuerza total sobre cada particula;
- fuerza individual por contacto;
- fuerza total instantanea sobre el obstaculo;
- fuerza total instantanea sobre la pared externa.

No debe:

- calcular energia total;
- calcular impulso acumulado;
- calcular promedios temporales;
- calcular `Fu(t)`;
- calcular `Cfc(t)`.

Las fuerzas instantaneas son output crudo valido porque salen directamente de la
ley fisica aplicada por el motor.

### `system2/integrators`

Responsable de avanzar el estado con paso fijo `dt`.

Debe exponer una interfaz conceptual:

```text
state(t), dt, force_evaluator -> state(t + dt)
```

Para este sistema conservativo, el integrador recomendado es uno compatible con
dinamica molecular conservativa, por ejemplo Velocity Verlet. Euler explicito
puede existir solo como referencia o prueba, no como integrador principal para
resultados finales.

No debe:

- escribir archivos;
- conocer formatos de output;
- calcular observables;
- modificar estado fresco/usado.

### `system2/engine`

Responsable de orquestar la corrida.

Debe:

- inicializar el sistema;
- ejecutar el loop temporal;
- pedir contactos para el estado actual;
- pedir fuerzas para esos contactos;
- llamar al integrador;
- enviar datos crudos al modulo de output;
- mantener reproducibilidad mediante semilla y metadata.

No debe:

- calcular energia total;
- calcular `Cfc(t)`;
- marcar particulas como usadas;
- calcular `J`;
- calcular perfiles radiales;
- generar graficos;
- hacer regresiones;
- decidir ventanas estadisticas.

El motor termina cuando produce archivos crudos completos y auditables.

### `system2/output`

Responsable de serializar datos crudos del motor.

Debe:

- escribir metadata;
- escribir estados;
- escribir contactos;
- escribir fuerzas instantaneas sobre cuerpos fijos;
- usar formatos de texto estables y documentados;
- incluir unidades o convenciones en metadata.

No debe:

- transformar datos en observables finales;
- suavizar series temporales;
- aplicar binning radial;
- calcular regresiones.

### `analysis-python/system2`

Responsable de postprocesar outputs crudos.

Debe calcular:

- energia total;
- `Cfc(t)`;
- pendiente `J` por realizacion;
- promedio y desvio estandar de `J` entre realizaciones;
- `Fu(t) = Nu(t) / N`, si se desea guardar;
- perfiles radiales;
- figuras, tablas y animaciones.

Puede decidir:

- ventanas de regresion;
- bins radiales;
- ventanas temporales para perfiles;
- criterios de descarte;
- comparaciones entre `dt`, `N` o realizaciones.

No debe:

- corregir trayectorias;
- re-simular fuerzas;
- convertirse en fuente de verdad de la dinamica.

## Contrato minimo de output crudo

Cada realizacion debe escribir sus archivos en un directorio propio:

```text
outputs/system2/<run_id>/
  metadata.json
  states.csv
  contacts.csv
  boundary_forces.csv
```

Los archivos `states.csv` y `contacts.csv` deben compartir `step` y `t`. Para
calcular correctamente `Cfc(t)`, los contactos con el obstaculo deben guardarse
cada `dt`; no alcanza con snapshots visuales submuestreados. Los estados y los
contactos completos pueden guardarse con strides configurables para mantener
archivos razonables, siempre que los pasos usados para energia tengan tanto
estado como contactos completos.

### `metadata.json`

Debe contener al menos:

```json
{
  "system": "system2",
  "run_id": "example",
  "realization": 0,
  "seed": 12345,
  "N": 100,
  "L": 80.0,
  "L_meaning": "diameter",
  "R": 40.0,
  "obstacle_radius": 1.0,
  "particle_radius": 1.0,
  "particle_mass": 1.0,
  "initial_speed": 1.0,
  "k": 1000.0,
  "dt": 0.0001,
  "steps": 100000,
  "integrator": "velocity_verlet",
  "state_stride": 5000,
  "contact_stride": 5000,
  "full_contact_stride": 5000,
  "obstacle_contact_stride": 1,
  "boundary_force_stride": 5000,
  "units": {
    "length": "m",
    "mass": "kg",
    "time": "s"
  },
  "normal_convention": "contacts file stores n_ij from body i to body j; force_on_i = -k * overlap * n_ij"
}
```

`k`, `dt`, `steps`, strides e identificadores son ejemplos; los valores finales
deben salir de la configuracion de corrida.

### `states.csv`

Una fila por particula y por paso escrito. El archivo debe incluir los pasos
divisibles por `state_stride` y tambien los divisibles por
`full_contact_stride`, para que la energia pueda calcularse en los pasos donde
se guardan contactos completos.

Columnas minimas:

```text
step,t,particle_id,x,y,vx,vy
```

Ejemplo:

```text
0,0.000000,17,12.345000,-4.200000,0.600000,0.800000
```

Este archivo permite reconstruir:

- trayectorias;
- velocidad de cada particula;
- energia cinetica;
- posiciones radiales;
- perfiles espaciales;
- animaciones.

No debe incluir:

- `used`;
- `fresh`;
- energia;
- bins radiales;
- valores de `Cfc`.

### `contacts.csv`

Una fila por contacto activo y por paso escrito. Para evitar archivos enormes,
los contactos de tipo `particle_obstacle` se escriben cada `dt`, mientras que
los contactos completos (`particle_particle`, `particle_obstacle` y
`particle_wall`) se escriben en los pasos divisibles por `full_contact_stride`.

Columnas minimas:

```text
step,t,contact_type,i,j,distance,overlap,nx,ny,fx_i,fy_i,fx_j,fy_j
```

Donde:

- `contact_type` pertenece a `{particle_particle, particle_obstacle, particle_wall}`;
- `i` es siempre una particula;
- `j` es otra particula, `obstacle` o `wall`;
- `nx,ny` es la normal desde `i` hacia `j`;
- `fx_i,fy_i` es la fuerza sobre `i`;
- `fx_j,fy_j` es la fuerza sobre `j`, incluyendo cuerpo fijo si corresponde.

Ejemplo:

```text
42,0.004200,particle_obstacle,17,obstacle,1.950000,0.050000,-1.000000,0.000000,500.000000,-0.000000,-500.000000,0.000000
```

Este archivo es la fuente de verdad para:

- energia potencial elastica;
- episodios de contacto con el obstaculo;
- fuerzas instantaneas de contacto;
- validacion de accion y reaccion.

Para `Cfc(t)`, usar todos los contactos `particle_obstacle`. Para energia,
usar solo los pasos divisibles por `full_contact_stride`, donde el archivo tiene
todos los tipos de contacto activos.

### `boundary_forces.csv`

Una fila por paso escrito, con cadencia configurable `boundary_force_stride`.

Columnas minimas:

```text
step,t,fx_obstacle,fy_obstacle,fx_wall,fy_wall,n_obstacle_contacts,n_wall_contacts
```

Este archivo es redundante con `contacts.csv`, pero util para auditoria y para
evitar sumar contactos en cada lectura de analisis. Sigue siendo output crudo:
es la suma instantanea de fuerzas generadas en el mismo paso, no un observable
promediado.

No debe incluir:

- impulso acumulado;
- fuerza suavizada;
- promedio temporal;
- normalizaciones estadisticas.

## Como el output permite calcular observables

### Energia total

El analisis calcula, para cada `step`:

```text
K(t) = sum_i 0.5 * m * |v_i(t)|^2
U(t) = sum_contacts 0.5 * k * overlap_contact(t)^2
E(t) = K(t) + U(t)
```

Datos usados:

- `states.csv` para velocidades;
- `contacts.csv` para solapamientos de contactos particula-particula,
  particula-obstaculo y particula-pared;
- `metadata.json` para `m` y `k`.

El motor no escribe `E(t)`. La conservacion aproximada de energia se evalua
afuera para validar `dt`.

### `Cfc(t)`

`Cfc(t)` es el numero acumulado de particulas frescas que contactan el
obstaculo central y pasan a usadas.

Como el contacto dura varios pasos, se cuenta solo el primer `dt` del episodio
de contacto.

El analisis reconstruye esto asi:

1. Inicializa todas las particulas como frescas.
2. Lee `contacts.csv` ordenado por `step`.
3. Para cada particula detecta si hay contacto `particle_obstacle` en el paso
   actual.
4. Un episodio empieza cuando:

```text
contact_now(i) == true
contact_previous_step(i) == false
```

5. Si la particula estaba fresca al inicio del episodio:

```text
Cfc = Cfc + 1
used(i) = true
```

6. Si la particula sigue en contacto durante varios `dt`, no se vuelve a
   contar.

Datos usados:

- `contacts.csv` con contactos de obstaculo guardados cada `dt`;
- `metadata.json` para `N`, `dt` y duracion de corrida.

La bandera `used` no pertenece al motor porque no modifica las fuerzas ni el
movimiento.

### `J`

Para cada realizacion, el analisis calcula `J` como la pendiente de la regresion
lineal de `Cfc(t)` contra `t`:

```text
Cfc(t) = J * t + b
```

Luego, entre realizaciones, calcula:

```text
mean_J = promedio de pendientes
std_J = desvio estandar de pendientes
```

Datos usados:

- `Cfc(t)` reconstruido desde `contacts.csv`;
- `metadata.json` para identificar realizaciones y parametros.

El motor no calcula pendientes, regresiones, promedios ni desvios.

### `Fu(t)`

Si se guarda, `Fu(t)` se define como:

```text
Fu(t) = Nu(t) / N
```

donde `Nu(t)` es la cantidad de particulas usadas hasta el tiempo `t`.

Este valor se obtiene en analisis con el mismo estado `used(i)` reconstruido
para `Cfc(t)`. Puede escribirse como output de analisis, por ejemplo:

```text
analysis-output/system2/<run_id>/used_fraction.csv
```

No debe formar parte del output crudo del motor.

### Perfiles radiales

El analisis calcula perfiles radiales desde posiciones y velocidades.

Datos usados:

- `states.csv`;
- `metadata.json` para centro, `R`, `r0`, `rp`, masa y tiempos;
- opcionalmente `contacts.csv` si se quiere perfil radial de contactos o
  presion de contacto.

El analisis decide:

- cantidad de bins;
- rango radial valido `[r0 + rp, R - rp]`;
- ventana temporal;
- si el perfil es de densidad, velocidad radial, velocidad tangencial,
  energia cinetica local o contactos.

El motor no calcula bins ni histogramas.

## Output de analisis recomendado

Estos archivos no son output crudo. Son derivados.

```text
analysis-output/system2/<experiment_id>/
  energy_by_run.csv
  cfc_by_run.csv
  j_by_run.csv
  j_summary.csv
  used_fraction_by_run.csv
  radial_profiles.csv
  figures/
```

Los nombres pueden cambiar, pero deben mantenerse separados de
`outputs/system2/<run_id>/`.

## Que pertenece al motor

Pertenece al motor:

- generar condiciones iniciales reproducibles;
- mantener estado dinamico;
- detectar contactos geometricos;
- calcular fuerzas elasticas instantaneas;
- integrar con paso fijo `dt`;
- escribir estado, contactos y fuerzas crudas;
- documentar parametros y convenciones.

## Que pertenece al analisis posterior

Pertenece al analisis:

- reconstruir particulas frescas/usadas;
- detectar inicios de episodios de contacto con obstaculo;
- calcular `Cfc(t)`;
- calcular `J` por regresion;
- promediar `J` entre realizaciones;
- calcular `Fu(t)`;
- calcular energia total;
- evaluar conservacion de energia;
- calcular perfiles radiales;
- generar figuras, tablas y animaciones.

## Decisiones explicitas para evitar problemas del TP3

### 1. La matematica debe mapear a modulos concretos

Cada ecuacion debe tener una ubicacion clara:

- geometria y radios en `model`;
- deteccion de `xi` y normales en `contacts`;
- ley `F = -k * xi * n` en `forces`;
- avance temporal en `integrators`;
- resultados estadisticos en `analysis`.

No debe haber formulas de observables escondidas en el loop del motor.

### 2. Los observables no forman parte del estado fisico

`fresh`, `used`, `Cfc`, `Fu`, histogramas y regresiones son conceptos de
analisis. No afectan la dinamica conservativa y por lo tanto no deben vivir en
el estado del motor.

### 3. El output crudo debe ser auditado sin rerun

El analisis debe poder explicar cada resultado leyendo archivos:

- posiciones y velocidades desde `states.csv`;
- contactos y solapamientos desde `contacts.csv`;
- parametros desde `metadata.json`;
- fuerzas sobre cuerpos fijos desde `boundary_forces.csv` o sumando contactos.

Si un resultado no se puede reconstruir desde esos archivos, el contrato de
output esta incompleto.

### 4. El analisis no debe redefinir la fisica del motor

El analisis no debe redetectar contactos como fuente primaria para energia
potencial o `Cfc(t)`. Debe usar los contactos que el motor efectivamente uso
para calcular fuerzas.

Puede recalcular para validacion, pero no como fuente de verdad.

### 5. Evitar herencia conceptual de TP3

El Sistema 2 de TP4 no es dinamica dirigida por eventos. No deben aparecer:

- tiempos futuros de colision;
- resoluciones instantaneas tipo hard-sphere;
- contadores de choque integrados al motor;
- logica de eventos como mecanismo principal de evolucion.

La evolucion es por fuerza elastica y paso temporal fijo.

### 6. Frecuencia de output compatible con los observables

Para `Cfc(t)`, guardar cada muchos pasos puede perder el primer `dt` del
episodio de contacto. Por eso, para corridas usadas en el calculo de `J`, los
contactos con obstaculo deben guardarse cada `dt`.

Si se usa submuestreo para animaciones, debe ser otro output y no reemplazar la
traza cruda usada para analisis.

### 7. Convenciones de signo documentadas

Toda fuerza guardada debe indicar sobre que cuerpo actua. En particular:

- `fx_i, fy_i` es fuerza sobre `i`;
- `fx_j, fy_j` es fuerza sobre `j`;
- para `j = obstacle`, esa fuerza es sobre el obstaculo fijo;
- para `j = wall`, esa fuerza es sobre la pared externa.

Esto evita ambiguedades al calcular fuerzas, impulsos o validaciones de accion y
reaccion.

### 8. Validacion cientifica separada

La conservacion aproximada de energia se usa para validar `dt`, pero se calcula
en analisis. El motor no debe pasar o fallar una corrida por energia salvo en
tests unitarios o herramientas de validacion separadas.

Validaciones recomendadas:

- dos particulas superpuestas producen fuerzas opuestas;
- particula contra obstaculo recibe fuerza hacia afuera;
- particula contra pared externa recibe fuerza hacia adentro;
- energia total aproximadamente constante al reducir `dt`;
- `Cfc(t)` no cuenta multiples veces un contacto persistente.

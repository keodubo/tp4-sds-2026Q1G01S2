# TP3 Reference Output Contract v1

**Fecha:** 2026-05-11  
**Objetivo:** dejar listo el barrido TP3 que se va a comparar contra las salidas TP4.

## Grilla Final

| Parametro | Valor |
|---|---|
| `N` | `100, 250, 500, 750, 1000` |
| Realizaciones | `5` por `N` |
| Seeds | `12345, 12346, 12347, 12348, 12349` |
| `tf` | `500 s` |
| `comparison_dt` | `1e-4` |
| `state_stride` | `5000` |
| `full_contact_stride` | `5000` |
| `boundary_force_stride` | `5000` |
| Cadencia equivalente | `comparison_dt * state_stride = 0.5 s` |

## Comandos

Generar las 25 configs y el manifest, sin correr simulaciones:

```bash
python3 scripts/run_tp3_reference_sweep.py
```

Correr el barrido TP3 completo:

```bash
python3 scripts/run_tp3_reference_sweep.py --execute
```

Smoke recomendado antes del barrido completo:

```bash
python3 scripts/run_tp3_reference_sweep.py \
  --experiment-id tp3-smoke \
  --particle-counts 100 \
  --seed-count 1 \
  --tf 5 \
  --execute
```

## Ubicacion Generada

```text
outputs/tp3-reference/tp3-final-grid/
```

Archivos principales:

```text
outputs/tp3-reference/tp3-final-grid/manifest.csv
outputs/tp3-reference/tp3-final-grid/configs/N_100/r_00.toml
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/snapshot.txt
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/metadata.json
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/center_contacts.csv
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/used_fraction.csv
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/radial_profile_samples.csv
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/radial_profiles.csv
```

`outputs/` esta ignorado por Git, asi que estas configs y salidas son locales y regenerables.

## Nota Importante

TP3 es dirigido por eventos. `comparison_dt` y los strides quedan registrados para alinear el barrido con TP4, pero no son un paso de integracion TP3. En la copia compacta actual, `snapshot_every` es una cadencia por cantidad de eventos; la exportacion CSV muestreada cada `0.5 s` queda para la siguiente fase si necesitamos comparacion punto a punto.

El runner actual ya exporta los observables necesarios para la comparacion manual:

- `center_contacts.csv`: serie `Cfc(t)` con los cambios `fresh -> used`.
- `used_fraction.csv`: fraccion de particulas usadas en cada snapshot registrado.
- `radial_profile_samples.csv`: muestras por capa radial para particulas frescas entrantes.
- `radial_profiles.csv`: perfil radial agregado por corrida.

Lo que no hace todavia es escribir un `states.csv` remuestreado cada `0.5 s`; para eso se usa el `snapshot.txt` dirigido por eventos si hace falta inspeccionar posiciones/velocidades.

# TP3 Enunciado Audit v1

**Fecha:** 2026-05-11  
**Alcance:** Fase 1 de `docs/superpowers/plans/2026-05-11_tp3-reference-outputs_v1.md`  
**Codigo auditado:** `SdS_TP3_2026Q1G01CS2_Codigo/` dentro de este repo TP4  
**Fuente principal:** `docs/TP3_Enunciado.pdf`

## Veredicto

El motor TP3 local cubre correctamente la base fisica del Sistema 1: dinamica dirigida por eventos, recinto circular, obstaculo central, estados `fresh`/`used`, salida de texto con posicion/velocidad/color, `Cfc(t)`, `Fu(t)` y muestras de perfiles radiales.

No esta listo todavia para generar el set comparable contra TP4, porque la copia local es el paquete compacto del motor y su CLI solo expone `system1 validate-config` y `system1 run`. Faltan el runner de barrido, el contrato de outputs comparable y la exportacion agregada de `1.1` a `1.4` dentro de este repo.

## Evidencia Revisada

| Tema | Evidencia |
|---|---|
| Enunciado TP3 | `docs/TP3_Enunciado.pdf`, texto extraido con `pdftotext`. |
| Resumen/wiki historico TP3 | `/Users/keoni/Claude-Workspace/projects/tp3-sds-2026Q1G01S2/docs/wiki/source_tp3_enunciado.md:53-144`. |
| Configuracion local | `SdS_TP3_2026Q1G01CS2_Codigo/configs/system1.example.toml:1-23`. |
| CLI local | `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/cli.py:10-50`. |
| Modelo fisico | `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/system1/model.py:8-55`. |
| Motor de eventos | `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/system1/simulation.py:33-239`. |
| Salida de texto | `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/system1/output.py:57-94`. |
| Observables | `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/system1/observables.py:28-167`. |

## Cobertura Por Requisito

| Enunciado item | Required | Current evidence | Gap | Action |
|---|---|---|---|---|
| Global: simulacion y animacion desacopladas | El motor debe generar archivo de texto; la animacion corre aparte desde esos archivos. | `SnapshotWriter` escribe header y pasos en texto plano (`output.py:63-94`). El historico TP3 explicita que el contrato incluye posicion, velocidad y color (`animation_output_contract.md:11-46`). | La copia compacta local no trae comando `animate`; para comparar con TP4 no es blocker si solo necesitamos CSV/texto. | Mantener outputs bajo `outputs/tp3-reference/` y no mezclar animacion en el motor. |
| Global: zip solo motor, menor a 100 KB | El entregable de codigo no debe incluir postprocesamiento, outputs, figuras ni docs. | La copia local tiene forma de motor compacto: `pyproject.toml`, `configs/`, `src/tp3_sds/`; no hay pipeline de figuras en el arbol local inspeccionado. | El README local quedo desalineado: menciona `study`, `animate`, `export-scientific-assets`, `package-delivery`, pero esos comandos no estan en el CLI local. | No usar README como fuente ejecutable. Para Fase 2, documentar comandos reales o actualizar README cuando se agregue el nuevo runner. |
| Sistema 1: dinamica dirigida por eventos | Particulas en MRU entre colisiones; tiempo intrinseco variable segun eventos. | `SimulationEngine` agenda eventos iniciales, consume una heap de eventos y avanza hasta el tiempo de cada evento (`simulation.py:61-83`, `simulation.py:109-170`, `simulation.py:213-231`). | Ninguno para el motor base. | Conservar este modelo; no introducir `dt` fisico en TP3. |
| Sistema 1: geometria | Recinto circular `L = 80 m`, obstaculo central `r0 = 1 m`, particulas de radio `r = 1 m`. | Defaults del loader: `diameter=80.0`, `obstacle_radius=1.0`, `particle_radius=1.0` (`config.py:110-114`). Config ejemplo coincide (`system1.example.toml:6-9`). `Geometry` calcula radios accesibles al centro (`model.py:13-29`). | Ninguno para defaults. | En el barrido, generar configs con los mismos valores. |
| Sistema 1: masa y velocidad | Masa `m = 1 kg`, modulo de velocidad `v0 = 1 m/s`, angulo uniforme en `[0, 2pi)`. | Defaults `mass=1.0`, `speed=1.0` (`config.py:115-119`) y config ejemplo (`system1.example.toml:11-14`). `_build_particle` sortea `velocity_angle` uniforme en `[0, 2pi)` y proyecta velocidad (`simulation.py:323-339`). | Ninguno para defaults. | En Fase 2 fijar estos parametros en el contrato de referencia. |
| Sistema 1: estado inicial | Todas las particulas arrancan frescas/verdes. | `Particle.state` default es `ParticleState.FRESH` (`model.py:32-42`). Color fresco default `(0,255,0)` (`config.py:10-11`) y output por estado (`output.py:51-54`, `output.py:78-94`). | Ninguno para el motor. | Mantener `state` y RGB en `states.csv` del nuevo contrato. |
| Sistema 1: cambio `fresh -> used` | Una particula fresca que contacta el centro pasa a usada/violeta. | `handle_boundary_collision` registra contacto central y asigna `ParticleState.USED` para `INNER_OBSTACLE` (`simulation.py:418-431`). `note_center_contact` solo incrementa si `was_fresh` (`observables.py:39-42`). | El output snapshot no registra explicitamente el evento de contacto; solo queda el estado y `center_contact_series` en memoria. | Fase 3 debe agregar stream de contactos o runner que exporte `center_contacts.csv` sin depender solo del snapshot. |
| Sistema 1: cambio `used -> fresh` | Una particula usada que contacta el borde vuelve a fresca. | `handle_boundary_collision` cambia a `FRESH` si el evento es `OUTER_WALL` y la particula estaba usada (`simulation.py:429-430`). | Igual que arriba: falta CSV de eventos para comparar transiciones con TP4. | Exportar contactos/eventos en el runner de referencia. |
| Sistema 1: output de estado | Imprimir posiciones, velocidades y color en cada tiempo de evento o cada cierto numero de eventos. | `_record_snapshot` escribe al writer cada `snapshot_every` eventos (`simulation.py:202-208`). `write_step` emite `x`, `y`, `vx`, `vy`, `state`, `r`, `g`, `b` (`output.py:78-94`). | El formato actual es apto para animacion, pero no es ideal para comparacion masiva porque mezcla pasos y particulas en un TXT grande. | Fase 2 debe definir `states.csv`; Fase 3/4 debe exportarlo con cadencia comparable. |
| 1.1 tiempo de ejecucion vs `N` | Variar `N` y graficar tiempo de ejecucion. El PDF dice `tf = 5 s`; el wiki historico registra errata oral a `tf = 500 s` (`source_tp3_enunciado.md:71-80`). | Existen estructuras `StudyConfig`, `planned_counts`, `repetitions`, `runtime_duration` (`config.py:65-87`, `config.py:141-199`). | La copia local no tiene comando `study` ni modulo `study.py`; no genera `runtime_vs_n.csv` ni figura. | Implementar runner de referencia que mida runtime por `N`, usando `tf = 500 s` para comparacion TP4 y anotando la discrepancia PDF/errata. |
| 1.2 `Cfc(t)` y `J` | Varias realizaciones por `N`; contar `Cfc(t)`, ajustar linealmente y promediar `J` con desvio. | `SimulationResult` incluye `center_contact_series` y `scanning_count` (`simulation.py:19-30`, `simulation.py:96-107`). `System1Observables` inicializa y actualiza `center_contact_series` (`observables.py:28-42`). | No hay export local de `center_contacts.csv`, ajuste lineal ni agregacion por `N`. | Exportar `center_contacts.csv` por corrida; agregar agregador de `scanning_rate_vs_n.csv`. |
| 1.3 `Fu(t)`, estacionario y `Fest` | Usar mismas simulaciones de 1.2, estudiar `Fu(t)`, reportar tiempo estacionario y `Fest` por `N`. | `record_snapshot` agrega `used_fraction_history` (`observables.py:44-54`) y `SimulationResult` la devuelve (`simulation.py:26-29`, `simulation.py:96-107`). | No hay deteccion local de estacionario ni export local de `used_fraction.csv`. | Exportar `used_fraction.csv`; en fase de agregacion reutilizar o reimplementar protocolo de estacionario. |
| 1.4 perfiles radiales | Para particulas frescas con `R dot v < 0`, calcular densidad, velocidad normal e `Jin(S)`, promediar y graficar. | `compute_radial_profile_snapshot` filtra `ParticleState.FRESH`, descarta `radial_dot >= 0`, calcula densidad por area, velocidad normal e `inward_flux` (`observables.py:65-109`). `aggregate_radial_profile_snapshots` promedia muestras y pondera velocidad por cantidad valida (`observables.py:112-167`). | No hay export local por corrida ni agregacion por realizaciones/N en la copia compacta. | Exportar `radial_profile_samples.csv` y agregar `near_shell_s2_vs_n.csv` y perfiles por `N`. |
| Maximo `N` razonable | El enunciado no fija maximo; pide que corra en tiempo razonable. | `validate_particle_density` advierte si la ocupacion supera 45% del anillo (`config.py:339-360`). Fallback de inicializacion por anillos intenta ubicar muchas particulas sin solapamiento (`simulation.py:256-320`). | Falta validar empiricamente `N=1000` para tiempo/memoria en esta copia local. | Antes del barrido full, correr smoke `N=100`, luego piloto `N=1000` corto. |

## Hallazgos Operativos

1. **No hay que adaptar TP3 a `dt`.** El `dt = 1e-4` pedido para comparar pertenece al mundo TP4 time-stepped. Para TP3, la decision correcta es usar `dt * stride = 0.5 s` como cadencia de muestreo/normalizacion, no como paso de integracion.
2. **El README local no es fuente confiable de comandos.** Menciona comandos del workspace TP3 completo, pero el CLI auditado solo tiene `validate-config` y `run`.
3. **Los observables ya existen en memoria.** `Cfc(t)`, `Fu(t)` y perfiles radiales estan disponibles en `SimulationResult`; el trabajo faltante es exportarlos de forma reproducible y agregarlos.
4. **El output actual sirve para animacion pero no para comparacion pesada.** Conviene generar CSVs separados por corrida en vez de parsear snapshots gigantes para todo el barrido.
5. **La discrepancia `tf=5 s` vs `tf=500 s` debe quedar documentada.** Para cumplir literalmente el PDF, `1.1` dice `5 s`; para este repo/flujo comparativo y el historico TP3 se usa `500 s`.

## Comando De Verificacion Fase 1

```bash
cd SdS_TP3_2026Q1G01CS2_Codigo
PYTHONPATH=src python3 -m tp3_sds system1 validate-config --config configs/system1.example.toml
```

Resultado observado:

```text
Config validation passed.
```

## Decision Para Fase 2

**Recomendado:** definir un contrato nuevo de outputs TP3 de referencia bajo:

```text
outputs/tp3-reference/tp3-final-grid/
```

Con archivos por corrida:

```text
metadata.json
states.csv
contacts.csv
center_contacts.csv
used_fraction.csv
radial_profile_samples.csv
```

No generar `boundary_forces.csv` para TP3 en v1: TP3 usa colisiones impulsivas dirigidas por eventos, mientras TP4 acumula fuerzas de una integracion temporal.

## Next Actions

- [ ] Fase 2: escribir `docs/2026-05-11_tp3-reference-output-contract_v1.md`.
- [ ] Fase 2: fijar seeds `12345..12349`, `N = 100,250,500,750,1000`, `tf = 500 s`.
- [ ] Fase 3: agregar un hook minimo para exportar estado/contactos sin cambiar la fisica del motor.
- [ ] Fase 4: crear `scripts/run_tp3_reference_sweep.py` con dry-run y smoke antes del full run.

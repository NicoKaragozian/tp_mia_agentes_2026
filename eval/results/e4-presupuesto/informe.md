# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 48

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 58% (28/48) |
| eficiencia media (éxitos) | 0.44 |
| fracción de llamadas repetidas | 58% |
| pasos medios | 42.1 |
| llamadas al LLM medias | 42.1 |
| tokens entrada / salida | 150673 / 2273 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 23.2 s |
| latencia media | 38.3 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 56% (9/16) | 0.45 | 64% | 40.9 | 154473 |
| presupuesto_100 | 81% (13/16) | 0.38 | 62% | 61.1 | 225595 |
| presupuesto_25 | 38% (6/16) | 0.54 | 48% | 24.1 | 71952 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| medium | 46% (11/24) | 50% | 35.1 |
| hard | 71% (17/24) | 66% | 49.0 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| color-locks | 11 | 46% (11/24) | 35.1 | 50% | accion_invalida, bucle |
| office-sequence | 13 | 71% (17/24) | 49.0 | 66% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 18 |
| accion_invalida | 2 |

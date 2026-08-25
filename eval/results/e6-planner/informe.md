# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 100

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 77% (77/100) |
| eficiencia media (éxitos) | 0.48 |
| fracción de llamadas repetidas | 43% |
| pasos medios | 43.4 |
| llamadas al LLM medias | 44.4 |
| tokens entrada / salida | 195056 / 2551 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 18.1 s |
| latencia media | 43.3 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 76% (38/50) | 0.47 | 44% | 44.8 | 197065 |
| con_planner | 78% (39/50) | 0.50 | 42% | 42.1 | 193047 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 100% (20/20) | 2% | 4.8 |
| medium | 75% (30/40) | 49% | 38.4 |
| hard | 68% (27/40) | 57% | 67.8 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 100% (20/20) | 4.8 | 2% | — |
| color-locks | 11 | 70% (14/20) | 44.5 | 49% | bucle |
| apartment-keys | 7 | 80% (16/20) | 32.4 | 49% | bucle |
| library-search | 7 | 60% (12/20) | 49.9 | 37% | bucle |
| office-sequence | 13 | 75% (15/20) | 85.7 | 78% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 23 |

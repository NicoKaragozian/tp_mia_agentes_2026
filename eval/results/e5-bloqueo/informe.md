# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 100

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 75% (75/100) |
| eficiencia media (éxitos) | 0.47 |
| fracción de llamadas repetidas | 44% |
| pasos medios | 46.3 |
| llamadas al LLM medias | 45.2 |
| tokens entrada / salida | 197173 / 2577 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 16.3 s |
| latencia media | 43.6 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 80% (40/50) | 0.48 | 41% | 43.8 | 167054 |
| con_bloqueo | 70% (35/50) | 0.45 | 47% | 48.7 | 227292 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 95% (19/20) | 7% | 14.5 |
| medium | 62% (25/40) | 57% | 49.7 |
| hard | 78% (31/40) | 49% | 58.8 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 95% (19/20) | 14.5 | 7% | bucle |
| color-locks | 11 | 55% (11/20) | 58.6 | 59% | bucle |
| apartment-keys | 7 | 70% (14/20) | 40.7 | 55% | bucle |
| library-search | 7 | 85% (17/20) | 29.4 | 19% | bucle |
| office-sequence | 13 | 70% (14/20) | 88.2 | 80% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 25 |

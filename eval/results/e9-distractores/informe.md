# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 100

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 75% (75/100) |
| eficiencia media (éxitos) | 0.49 |
| fracción de llamadas repetidas | 44% |
| pasos medios | 44.9 |
| llamadas al LLM medias | 44.7 |
| tokens entrada / salida | 210239 / 2447 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 16.4 s |
| latencia media | 41.9 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 72% (36/50) | 0.48 | 47% | 48.5 | 227207 |
| con_distractores | 78% (39/50) | 0.51 | 41% | 41.3 | 193272 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 95% (19/20) | 6% | 9.4 |
| medium | 75% (30/40) | 49% | 38.5 |
| hard | 65% (26/40) | 58% | 69.0 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 95% (19/20) | 9.4 | 6% | bucle |
| color-locks | 11 | 65% (13/20) | 49.6 | 51% | bucle |
| apartment-keys | 7 | 85% (17/20) | 27.4 | 47% | bucle |
| library-search | 7 | 55% (11/20) | 53.8 | 39% | bucle |
| office-sequence | 13 | 75% (15/20) | 84.2 | 77% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 25 |

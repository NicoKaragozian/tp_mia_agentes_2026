# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 50

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 72% (36/50) |
| eficiencia media (éxitos) | 0.49 |
| fracción de llamadas repetidas | 39% |
| pasos medios | 27.1 |
| llamadas al LLM medias | 27.3 |
| tokens entrada / salida | 113055 / 1523 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 18.8 s |
| latencia media | 25.7 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 72% (18/25) | 0.50 | 37% | 25.4 | 89595 |
| con_memoria_acciones | 72% (18/25) | 0.49 | 41% | 28.8 | 136515 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 100% (10/10) | 3% | 5.0 |
| medium | 75% (15/20) | 49% | 30.0 |
| hard | 55% (11/20) | 47% | 35.2 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 100% (10/10) | 5.0 | 3% | — |
| color-locks | 11 | 70% (7/10) | 36.0 | 49% | bucle |
| apartment-keys | 7 | 80% (8/10) | 24.0 | 50% | bucle |
| library-search | 7 | 70% (7/10) | 26.7 | 23% | bucle |
| office-sequence | 13 | 40% (4/10) | 43.7 | 70% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 14 |

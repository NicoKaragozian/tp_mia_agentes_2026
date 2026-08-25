# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 50

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 92% (22/24) |
| eficiencia media (éxitos) | 0.52 |
| fracción de llamadas repetidas | 29% |
| pasos medios | 21.1 |
| llamadas al LLM medias | 21.3 |
| tokens entrada / salida | 72155 / 1152 |
| corridas descartadas (fallo de infraestructura) | 26 |
| latencia mediana | 13.5 s |
| latencia media | 18.1 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 0% (0/0) | 0.00 | 0% | 0.0 | 0 |
| sin_memoria_acciones | 92% (22/24) | 0.52 | 29% | 21.1 | 72155 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 100% (5/5) | 0% | 4.0 |
| medium | 90% (9/10) | 39% | 20.6 |
| hard | 89% (8/9) | 34% | 31.1 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 100% (5/5) | 4.0 | 0% | fallo_infraestructura |
| color-locks | 11 | 80% (4/5) | 26.6 | 37% | bucle, fallo_infraestructura |
| apartment-keys | 7 | 100% (5/5) | 14.6 | 41% | fallo_infraestructura |
| library-search | 7 | 100% (5/5) | 22.0 | 9% | fallo_infraestructura |
| office-sequence | 13 | 75% (3/4) | 42.5 | 66% | bucle, fallo_infraestructura |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| fallo_infraestructura | 26 |
| bucle | 2 |

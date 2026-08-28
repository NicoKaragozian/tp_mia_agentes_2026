# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 242

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 84% (202/240) |
| eficiencia media (éxitos) | 0.46 |
| fracción de llamadas repetidas | 38% |
| pasos medios | 37.0 |
| llamadas al LLM medias | 37.0 |
| tokens entrada / salida | 160489 / 2040 |
| corridas descartadas (fallo de infraestructura) | 2 |
| latencia mediana | 15.3 s |
| latencia media | 34.7 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 98% (49/50) | 6% | 7.8 |
| medium | 82% (82/100) | 46% | 33.9 |
| hard | 79% (71/90) | 48% | 56.8 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 98% (49/50) | 7.8 | 6% | bucle |
| color-locks | 11 | 70% (35/50) | 46.1 | 48% | bucle |
| apartment-keys | 7 | 94% (47/50) | 21.6 | 45% | bucle |
| library-search | 7 | 86% (43/50) | 34.4 | 23% | bucle |
| office-sequence | 13 | 70% (28/40) | 84.8 | 78% | bucle, fallo_infraestructura |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 38 |
| fallo_infraestructura | 2 |

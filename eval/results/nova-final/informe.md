# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 50

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 80% (40/50) |
| eficiencia media (éxitos) | 0.49 |
| fracción de llamadas repetidas | 42% |
| pasos medios | 40.8 |
| llamadas al LLM medias | 40.8 |
| tokens entrada / salida | 189816 / 2305 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 17.6 s |
| latencia media | 38.8 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 100% (10/10) | 0% | 4.2 |
| medium | 85% (17/20) | 46% | 31.9 |
| hard | 65% (13/20) | 60% | 67.8 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 100% (10/10) | 4.2 | 0% | — |
| color-locks | 11 | 80% (8/10) | 40.7 | 47% | bucle |
| apartment-keys | 7 | 90% (9/10) | 23.2 | 44% | bucle |
| library-search | 7 | 50% (5/10) | 59.2 | 46% | bucle |
| office-sequence | 13 | 80% (8/10) | 76.5 | 73% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 10 |

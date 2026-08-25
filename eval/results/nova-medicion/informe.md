# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 25

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 76% (19/25) |
| eficiencia media (éxitos) | 0.53 |
| fracción de llamadas repetidas | 36% |
| pasos medios | 26.9 |
| llamadas al LLM medias | 27.5 |
| tokens entrada / salida | 115830 / 1603 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 17.0 s |
| latencia media | 26.6 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 100% (5/5) | 0% | 4.2 |
| medium | 70% (7/10) | 44% | 26.5 |
| hard | 70% (7/10) | 46% | 38.6 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 100% (5/5) | 4.2 | 0% | — |
| color-locks | 11 | 80% (4/5) | 25.4 | 34% | bucle |
| apartment-keys | 7 | 60% (3/5) | 27.6 | 54% | bucle |
| library-search | 7 | 60% (3/5) | 33.4 | 25% | bucle |
| office-sequence | 13 | 80% (4/5) | 43.8 | 68% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 6 |

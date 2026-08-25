# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 10

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 80% (8/10) |
| eficiencia media (éxitos) | 0.56 |
| fracción de llamadas repetidas | 35% |
| pasos medios | 26.4 |
| llamadas al LLM medias | 27.0 |
| tokens entrada / salida | 99906 / 1386 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 13.3 s |
| latencia media | 23.5 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 100% (2/2) | 0% | 4.5 |
| medium | 100% (4/4) | 22% | 13.8 |
| hard | 50% (2/4) | 65% | 50.0 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 100% (2/2) | 4.5 | 0% | — |
| color-locks | 11 | 100% (2/2) | 15.0 | 9% | — |
| apartment-keys | 7 | 100% (2/2) | 12.5 | 36% | — |
| library-search | 7 | 0% (0/2) | 50.0 | 59% | bucle |
| office-sequence | 13 | 100% (2/2) | 50.0 | 71% | — |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 2 |

# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 4

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 75% (3/4) |
| eficiencia media (éxitos) | 0.36 |
| fracción de llamadas repetidas | 38% |
| pasos medios | 30.8 |
| llamadas al LLM medias | 29.8 |
| tokens entrada / salida | 129817 / 1878 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 28.0 s |
| latencia media | 29.8 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| medium | 50% (1/2) | 62% | 43.5 |
| hard | 100% (2/2) | 13% | 18.0 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| color-locks | 11 | 50% (1/2) | 43.5 | 62% | bucle |
| library-search | 7 | 100% (2/2) | 18.0 | 13% | — |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 1 |

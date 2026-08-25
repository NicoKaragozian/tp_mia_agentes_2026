# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 4

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 50% (2/4) |
| eficiencia media (éxitos) | 0.29 |
| fracción de llamadas repetidas | 59% |
| pasos medios | 40.5 |
| llamadas al LLM medias | 41.0 |
| tokens entrada / salida | 187475 / 2411 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 39.4 s |
| latencia media | 38.7 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| medium | 50% (1/2) | 55% | 41.5 |
| hard | 50% (1/2) | 64% | 39.5 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| color-locks | 11 | 50% (1/2) | 41.5 | 55% | bucle |
| library-search | 7 | 50% (1/2) | 39.5 | 64% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 2 |

# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 4

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 50% (2/4) |
| eficiencia media (éxitos) | 0.35 |
| fracción de llamadas repetidas | 55% |
| pasos medios | 38.2 |
| llamadas al LLM medias | 38.8 |
| tokens entrada / salida | 221945 / 3104 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 46.8 s |
| latencia media | 44.4 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| medium | 50% (1/2) | 67% | 42.5 |
| hard | 50% (1/2) | 44% | 34.0 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| color-locks | 11 | 50% (1/2) | 42.5 | 67% | bucle |
| library-search | 7 | 50% (1/2) | 34.0 | 44% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 2 |

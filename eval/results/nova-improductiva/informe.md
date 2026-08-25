# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 6

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 33% (2/6) |
| eficiencia media (éxitos) | 0.44 |
| fracción de llamadas repetidas | 54% |
| pasos medios | 38.7 |
| llamadas al LLM medias | 39.0 |
| tokens entrada / salida | 222997 / 2597 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 50.9 s |
| latencia media | 41.3 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| medium | 33% (1/3) | 72% | 38.3 |
| hard | 33% (1/3) | 37% | 39.0 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| apartment-keys | 7 | 33% (1/3) | 38.3 | 72% | bucle |
| library-search | 7 | 33% (1/3) | 39.0 | 37% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 4 |

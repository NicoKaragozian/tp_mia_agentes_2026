# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 4

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 0% (0/4) |
| eficiencia media (éxitos) | 0.00 |
| fracción de llamadas repetidas | 74% |
| pasos medios | 50.0 |
| llamadas al LLM medias | 50.0 |
| tokens entrada / salida | 363324 / 3166 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 52.0 s |
| latencia media | 52.2 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| medium | 0% (0/2) | 81% | 50.0 |
| hard | 0% (0/2) | 68% | 50.0 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| color-locks | 11 | 0% (0/2) | 50.0 | 81% | bucle |
| library-search | 7 | 0% (0/2) | 50.0 | 68% | desborde_contexto |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| desborde_contexto | 2 |
| bucle | 2 |

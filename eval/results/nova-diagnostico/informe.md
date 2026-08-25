# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 5

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 80% (4/5) |
| eficiencia media (éxitos) | 0.48 |
| fracción de llamadas repetidas | 38% |
| pasos medios | 26.4 |
| llamadas al LLM medias | 27.0 |
| tokens entrada / salida | 90559 / 1816 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 14.5 s |
| latencia media | 26.2 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 100% (1/1) | 0% | 5.0 |
| medium | 50% (1/2) | 56% | 30.5 |
| hard | 100% (2/2) | 39% | 33.0 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 100% (1/1) | 5.0 | 0% | — |
| color-locks | 11 | 0% (0/1) | 50.0 | 84% | bucle |
| apartment-keys | 7 | 100% (1/1) | 11.0 | 27% | — |
| library-search | 7 | 100% (1/1) | 16.0 | 6% | — |
| office-sequence | 13 | 100% (1/1) | 50.0 | 72% | — |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 1 |

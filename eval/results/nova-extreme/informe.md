# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 30

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 40% (12/30) |
| eficiencia media (éxitos) | 0.30 |
| fracción de llamadas repetidas | 57% |
| pasos medios | 71.6 |
| llamadas al LLM medias | 70.2 |
| tokens entrada / salida | 358885 / 3835 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 92.7 s |
| latencia media | 69.8 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| extreme | 40% (12/30) | 57% | 71.6 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| extreme-archive | 4 | 90% (9/10) | 31.5 | 8% | desborde_contexto |
| vault-combination | 21 | 10% (1/10) | 97.8 | 80% | bucle |
| backtracking-vault | 18 | 20% (2/10) | 85.6 | 82% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 17 |
| desborde_contexto | 1 |

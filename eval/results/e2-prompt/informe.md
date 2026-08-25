# Resultados de la evaluación

Modelo: `ollama:llama3.1:8b` · corridas: 32

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 12% (4/32) |
| eficiencia media (éxitos) | 0.43 |
| fracción de llamadas repetidas | 34% |
| pasos medios | 19.4 |
| llamadas al LLM medias | 16.1 |
| tokens entrada / salida | 22966 / 5549 |
| latencia media | 218.2 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 25% (4/16) | 0.43 | 23% | 16.5 | 29320 |
| prompt_generico | 0% (0/16) | 0.00 | 44% | 22.3 | 16613 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 50% (2/4) | 34% | 11.8 |
| medium | 25% (2/8) | 37% | 18.2 |
| hard | 0% (0/8) | 24% | 20.6 |
| extreme | 0% (0/12) | 38% | 21.9 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 50% (2/4) | 11.8 | 34% | bucle |
| color-locks | 11 | 50% (2/4) | 20.5 | 25% | accion_invalida, bucle |
| apartment-keys | 7 | 0% (0/4) | 16.0 | 48% | accion_invalida, bucle |
| library-search | 7 | 0% (0/4) | 15.8 | 24% | accion_invalida, bucle |
| office-sequence | 13 | 0% (0/4) | 25.5 | 23% | accion_invalida, bucle, tool_call_en_texto |
| extreme-archive | 4 | 0% (0/4) | 6.0 | 19% | accion_invalida, bucle, tool_call_en_texto |
| vault-combination | 21 | 0% (0/4) | 50.0 | 80% | bucle |
| backtracking-vault | 18 | 0% (0/4) | 9.8 | 16% | accion_invalida, bucle, parada_prematura |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 13 |
| accion_invalida | 9 |
| tool_call_en_texto | 4 |
| parada_prematura | 2 |

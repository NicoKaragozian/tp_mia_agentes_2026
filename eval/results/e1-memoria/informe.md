# Resultados de la evaluación

Modelo: `ollama:llama3.1:8b` · corridas: 48

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 8% (4/48) |
| eficiencia media (éxitos) | 0.43 |
| fracción de llamadas repetidas | 22% |
| pasos medios | 13.2 |
| llamadas al LLM medias | 13.4 |
| tokens entrada / salida | 18598 / 315 |
| latencia media | 20.1 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 25% (4/16) | 0.43 | 31% | 20.8 | 38535 |
| memoria_ajustada | 0% (0/16) | 0.00 | 21% | 12.8 | 12023 |
| memoria_minima | 0% (0/16) | 0.00 | 15% | 6.0 | 5236 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 33% (2/6) | 0% | 5.2 |
| medium | 17% (2/12) | 30% | 18.3 |
| hard | 0% (0/12) | 24% | 10.0 |
| extreme | 0% (0/18) | 23% | 14.6 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 33% (2/6) | 5.2 | 0% | tool_call_en_texto |
| color-locks | 11 | 33% (2/6) | 22.7 | 34% | bucle, tool_call_en_texto |
| apartment-keys | 7 | 0% (0/6) | 14.0 | 27% | argumentos_invalidos, bucle, tool_call_en_texto |
| library-search | 7 | 0% (0/6) | 18.7 | 48% | bucle, tool_call_en_texto |
| office-sequence | 13 | 0% (0/6) | 1.3 | 0% | tool_call_en_texto |
| extreme-archive | 4 | 0% (0/6) | 2.2 | 8% | tool_call_en_texto |
| vault-combination | 21 | 0% (0/6) | 24.5 | 43% | bucle, tool_call_en_texto |
| backtracking-vault | 18 | 0% (0/6) | 17.0 | 17% | bucle, tool_call_en_texto |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| tool_call_en_texto | 31 |
| bucle | 12 |
| argumentos_invalidos | 1 |

## Rúbrica cualitativa (LLM-as-judge, 1–5)

| dimensión | media |
|---|---|
| coherencia_plan | 2.75 |
| recuperacion_errores | 1.96 |
| exploracion_eficiente | 2.85 |

-- 1°- ¿Cuantos turnos hubo por especialidad?
SELECT
    UPPER(TRIM(especialidad)) AS especialidad,
    COUNT(*) AS cantidad_turnos
FROM tabla_final
GROUP BY UPPER(TRIM(especialidad))
ORDER BY cantidad_turnos DESC;


-- 2°- ¿Cual es el porcentaje de ausentismo por especialidad?

-- CONSULTA 2: Porcentaje de ausentismo por especialidad

SELECT
    UPPER(TRIM(especialidad)) AS especialidad,

    COUNT(*) FILTER (
        WHERE LOWER(TRIM(estado)) = 'ausente'
    ) AS turnos_ausentes,

    COUNT(*) FILTER (
        WHERE LOWER(TRIM(estado)) IN ('atendido', 'ausente')
    ) AS turnos_programados,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE LOWER(TRIM(estado)) = 'ausente'
        ) /
        NULLIF(
            COUNT(*) FILTER (
                WHERE LOWER(TRIM(estado)) IN ('atendido', 'ausente')
            ),
            0
        ),
        2
    ) AS porcentaje_ausentismo

FROM tabla_final
GROUP BY UPPER(TRIM(especialidad))
ORDER BY porcentaje_ausentismo DESC;


-- °3 ¿Cuanto se facturo en turnos atendidos por mes (primeros 6 meses)?
SELECT
    DATE_TRUNC('month', fecha_turno) AS mes,
    SUM(costo) AS importe_facturado
FROM tabla_final
WHERE LOWER(TRIM(estado)) = 'atendido'
GROUP BY DATE_TRUNC('month', fecha_turno)
ORDER BY mes ASC
LIMIT 6;


-- °4¿Cuales son los 5 medicos con mas turnos atendidos?
SELECT
    id_medico,
    medico,
    COUNT(*) AS cantidad_turnos_atendidos
FROM tabla_final
WHERE LOWER(TRIM(estado)) = 'atendido'
GROUP BY id_medico, medico
ORDER BY cantidad_turnos_atendidos DESC
LIMIT 5;


-- 5°¿Cual es la edad promedio de los pacientes por obra social?
SELECT
    obra_social,
    ROUND(AVG(edad), 2) AS edad_promedio
FROM tabla_final
GROUP BY obra_social
ORDER BY edad_promedio DESC;

Informe del trabajo:

Punto 1: 
Usamos python para extraer la informacion de la bd SQlite y cargarlo en Duckdb.
Obtuvimos 2575 registros que almacenamos en 


Punto 2: Validación y limpieza de datos
Aplicamos las 8 reglas de validacion; como resultado obtuve:

.2163 registros validos
.412 registros rechazados
.337 recuperados

Los problemas detectados fueron:
.Datos medicos incompletos o invalidos: 158 registros
.Id duplicados o invalidos: 149 registros
.Costos invalidos: 129 registros

Al final creamos una tabla final con 2500 registros.


Punto 3: 
Hicimos 5 consultas para analizar la informacion:
.Turnos por especialidad: Clinica medica presento la mayor cantidad con 442 turnos
.Porcentaje de ausencias: Pediatria presento el porcentaje mas alto con 21,04%
. Facturacion: Mayo fue el mes con mayor facturacion por turnos atendidos en el primer semestre con
 $2.087.000
.Medicos con mas turnos atendidos: medico m21, dr. Romero C1, con 124 turnos
.Edad promediada por obra social: Pami presento el promedio mas alto con 42,30 años


Punto 4:
.Se creo un DAG en apache AIRFLOW dag_turnos_clinica, configurado para ejecutarse a las 02hrs.
.Realizamos purebas y se comprobo que el proceso ETL funciona correctamente.
.Mediante el proyecto esto permitio la la extraccion, validacion, limpieza, almacenamiento y analisis de datos.

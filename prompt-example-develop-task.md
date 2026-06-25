Usa como fuente de verdad el documento docs/DDP.md.

Ejecuta únicamente la tarea TASK-004: Crear endpoint para consulta de clientes.

Alcance:
- Crear endpoint GET /clientes/{id}
- Validar que el usuario esté autenticado
- Retornar nombre, identificación, estado y fecha de creación
- No modificar frontend
- No modificar modelo de base de datos

Archivos permitidos:
- backend/routes/clientes.py
- backend/services/clientes_service.py
- tests/test_clientes.py

Archivos restringidos:
- .env
- archivos de migraciones
- configuración de despliegue
- módulos de autenticación

Criterios de aceptación:
- Si el cliente existe, responde 200 con los datos esperados.
- Si el cliente no existe, responde 404.
- Si no hay autenticación, responde 401.
- No se exponen datos sensibles.

Pruebas mínimas:
- Prueba para cliente existente.
- Prueba para cliente inexistente.
- Prueba sin autenticación.

Resultado esperado:
- Endpoint implementado.
- Pruebas ejecutadas.
- Resumen de archivos modificados.
- Riesgos pendientes documentados.
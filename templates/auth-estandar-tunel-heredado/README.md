# Túnel de roles de la Mesa (HEREDADO)

**No copiar a un desarrollo nuevo.** El túnel `/api/roles-app` de la Mesa se retiró el 2026-11-11 y los roles viven en las tablas del propio desarrollo. Estos archivos se conservan solo como referencia para quien migra un desarrollo que todavía los usa (por ejemplo para inventariar asignaciones antes de pasar a la configuración local) y para entender `CONTRATO-TUNEL-ROLES.md`.

| Archivo | Qué era |
|---|---|
| `backend/src/helpers/roles_mesa.py` | Leía el rol por `GET /api/roles-app/<id>/mios`. Lo reemplaza `templates/auth-estandar/backend/src/helpers/roles_propios.py`. |
| `src/services/rolesMesa.js` (+ prueba) | Cliente del túnel. Lo reemplaza `src/services/configuracionLocal.js`. |
| `src/screens/ConfiguracionDesarrollo.jsx` (+ prueba) | Pantalla de configuración contra el túnel. Lo reemplaza la pantalla del mismo nombre de `templates/auth-estandar/`. |

Las rutas relativas se conservan para que se vea qué pieza reemplaza a cuál. Estos archivos no son un paquete autosuficiente (dependen de `AuthContext`, `appInfo.roles` y estilos de `templates/auth-estandar/`). Nueva guía: [Configuración local de roles y secretos](../../CONFIGURACION-LOCAL-ROLES-Y-SECRETOS.md).

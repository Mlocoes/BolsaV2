# Uso de Docker Secrets en BolsaV2

## ¿Qué son Docker Secrets?

Docker Secrets es un mecanismo seguro para gestionar información sensible (contraseñas, API keys, tokens) en contenedores Docker. Los secrets se montan como archivos en `/run/secrets/` dentro del contenedor y no se exponen como variables de entorno.

## Configuración Inicial

### 1. Ejecutar el script de inicialización

```bash
./init-secrets.sh
```

Este script:
- Crea el directorio `secrets/` si no existe
- Lee valores desde `.env` o solicita input manual
- Crea archivos individuales para cada secret
- Establece permisos seguros (600)

### 2. Secrets Configurados

El sistema usa los siguientes secrets:

- **db_password**: Contraseña de PostgreSQL
- **secret_key**: Clave secreta de la aplicación (JWT, sessions)
- **finnhub_api_key**: API key de Finnhub para cotizaciones en tiempo real
- **alpha_vantage_api_key**: API key de Alpha Vantage para datos históricos

### 3. Estructura de Archivos

```
secrets/
├── db_password.txt
├── secret_key.txt
├── finnhub_api_key.txt
└── alpha_vantage_api_key.txt
```

⚠️ **IMPORTANTE**: El directorio `secrets/` está en `.gitignore` y nunca debe subirse a git.

## Modo de Operación

### Desarrollo (con secrets)

```bash
# 1. Inicializar secrets
./init-secrets.sh

# 2. Levantar servicios
docker-compose up -d
```

### Desarrollo (sin secrets - fallback a .env)

Si no inicializas los secrets, la aplicación utilizará los valores del archivo `.env` como fallback.

```bash
docker-compose up -d
```

### Producción

En producción, los secrets deben ser gestionados mediante:
- Docker Swarm Secrets
- Kubernetes Secrets
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault

## Cómo Funciona Internamente

### 1. Docker Compose

El `docker-compose.yml` define los secrets y los monta en los contenedores:

```yaml
secrets:
  db_password:
    file: ./secrets/db_password.txt

services:
  backend:
    secrets:
      - db_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
```

### 2. Backend Configuration

El archivo `backend/app/core/config.py` implementa la función `_read_secret()`:

```python
def _read_secret(env_name: str, default: str | None = None) -> str | None:
    """Permite usar Docker secrets via variables *_FILE"""
    file_var = os.getenv(f"{env_name}_FILE")
    if file_var and os.path.exists(file_var):
        with open(file_var, "r", encoding="utf-8") as f:
            return f.read().strip()
    return os.getenv(env_name, default)
```

Prioridad de lectura:
1. Si existe `{VAR}_FILE`, lee del archivo secret
2. Si no, usa la variable de entorno `{VAR}`
3. Si no, usa el valor por defecto

## Migración desde Variables de Entorno

Si actualmente usas variables de entorno en `.env`, puedes migrar gradualmente:

1. **Mantener .env para desarrollo rápido**
2. **Usar secrets para staging/producción**
3. **El código soporta ambos métodos automáticamente**

## Verificación

Para verificar que los secrets están correctamente montados:

```bash
# Listar secrets en el contenedor
docker exec bolsav2_backend ls -la /run/secrets/

# Ver contenido (para debug - ¡no en producción!)
docker exec bolsav2_backend cat /run/secrets/secret_key
```

## Troubleshooting

### Error: "No such file or directory: /run/secrets/..."

**Causa**: El archivo secret no existe o el servicio no tiene acceso al secret.

**Solución**:
1. Ejecuta `./init-secrets.sh`
2. Verifica que el secret esté definido en `docker-compose.yml`
3. Reconstruye los contenedores: `docker-compose up -d --build`

### Error: "Database authentication failed"

**Causa**: La contraseña en `db_password.txt` no coincide con PostgreSQL.

**Solución**:
1. Verifica el contenido de `secrets/db_password.txt`
2. Asegúrate que coincide con `POSTGRES_PASSWORD` en `.env`
3. Si cambiaste la contraseña, elimina el volumen de postgres:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Error: "Permission denied" al leer secrets

**Causa**: Permisos incorrectos en archivos de secrets.

**Solución**:
```bash
chmod 600 secrets/*.txt
```

## Mejores Prácticas

1. ✅ **Nunca subas secrets a git**
2. ✅ **Usa diferentes secrets para desarrollo/staging/producción**
3. ✅ **Rota los secrets regularmente**
4. ✅ **Limita el acceso a los archivos de secrets (chmod 600)**
5. ✅ **En producción, usa gestores de secrets dedicados**
6. ❌ **No hagas echo de secrets en logs**
7. ❌ **No compartas secrets por email/slack**
8. ❌ **No hardcodees secrets en el código**

## Referencias

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Docker Compose Secrets](https://docs.docker.com/compose/use-secrets/)
- [Twelve-Factor App: Config](https://12factor.net/config)

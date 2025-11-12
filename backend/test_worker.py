"""
Script para probar el worker de Celery directamente
"""
from app.services.celery_tasks import update_all_asset_prices, update_single_asset_price

def test_worker():
    """Probar tareas del worker"""
    
    print("🔄 Iniciando prueba del worker...")
    print()
    
    # Test 1: Health check básico
    print("1️⃣ Test: Enviar tarea de actualización de precios")
    try:
        task = update_all_asset_prices.delay()
        print(f"   ✓ Tarea enviada: {task.id}")
        print(f"   Status: {task.status}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    print("2️⃣ Test: Actualización de un solo asset")
    try:
        task = update_single_asset_price.delay("AAPL")
        print(f"   ✓ Tarea enviada: {task.id}")
        print(f"   Status: {task.status}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    print("✅ Pruebas completadas")
    print("📊 Revisa los logs del worker para ver la ejecución:")
    print("   docker-compose logs worker")

if __name__ == "__main__":
    test_worker()

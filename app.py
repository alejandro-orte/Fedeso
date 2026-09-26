<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Administración FEDESO</title>
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background-color: #f8fafc;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .header {
            background-color: #2563eb;
            color: white;
            padding: 25px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        .nav-menu {
            display: flex;
            gap: 25px;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .nav-link {
            color: #6b7280;
            text-decoration: none;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 5px;
            padding-bottom: 10px;
        }
        .nav-link:hover {
            color: #2563eb;
        }
        .nav-link.active {
            color: #ef4444;
            border-bottom: 2px solid #ef4444;
            font-weight: 500;
        }
        /* Estilos Tabla Historial */
        .table-container {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            min-width: 800px;
        }
        th {
            background-color: #f9fafb;
            padding: 12px 16px;
            color: #4b5563;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            border-bottom: 2px solid #e5e7eb;
        }
        td {
            padding: 14px 16px;
            font-size: 0.9rem;
            color: #111827;
            border-bottom: 1px solid #e5e7eb;
        }
    </style>
</head>
<body>

<div class="container">
    <!-- Encabezado Principal FEDESO -->
    <div class="header">
        <div>
            <h1 style="margin: 0; font-size: 28px; font-weight: bold; letter-spacing: 1px;">FEDESO</h1>
            <p style="margin: 5px 0 0 0; font-size: 15px;">Fondo Empresarial de Solidaridad</p>
        </div>
        <a href="#" style="color: white; text-decoration: none; font-size: 14px; font-weight: bold;">Portal de Asociados</a>
    </div>

    <!-- Título del Panel -->
    <h2 style="color: #1e3a8a; display: flex; align-items: center; gap: 10px; font-size: 1.5rem; margin-bottom: 1.5rem;">
        🛠️ Panel de Administración FEDESO
    </h2>

    <!-- Menú de Navegación -->
    <div class="nav-menu">
        <a href="#" class="nav-link">👤 Crear Usuario</a>
        <a href="#" class="nav-link">💵 Registrar Préstamo</a>
        <a href="#" class="nav-link">📅 Registrar Pago / Cuota</a>
        <a href="#" class="nav-link active">📥 Verificar Notificaciones</a>
        <a href="#" class="nav-link">📈 Resumen Financiero del Fondo</a>
        <a href="#historial-pagos" class="nav-link" style="font-weight: bold; color: #4f46e5;">📁 Historial de Pagos</a>
    </div>

    <!-- Sección Original: Verificar Notificaciones -->
    <div style="margin-bottom: 3rem;">
        <h3 style="display: flex; align-items: center; gap: 10px; color: #374151; font-size: 1.25rem;">
            📥 Notificaciones de Pago Pendientes por Verificar
        </h3>
        
        <button style="border: 1px solid #d1d5db; background: white; padding: 8px 16px; border-radius: 6px; cursor: pointer; color: #374151; margin-bottom: 1rem; font-size: 13px; display: flex; align-items: center; gap: 5px;">
            🔄 Actualizar / Recargar Notificaciones
        </button>
        
        <div style="background-color: #d1fae5; color: #065f46; padding: 12px 16px; border-radius: 6px; font-size: 14px; display: flex; align-items: center; gap: 10px;">
            🎉 ¡No hay pagos pendientes por verificar! Todos han sido procesados.
        </div>
    </div>

    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 2rem 0;">

    <!-- NUEVA SECCIÓN: Historial de Pagos -->
    <div id="historial-pagos">
        <h3 style="color: #1e3a8a; font-size: 1.25rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 10px;">
            📁 Historial de Pagos Confirmados
        </h3>

        <!-- Filtros -->
        <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem;">
            <input type="text" placeholder="Buscar por asociado o comprobante..." style="flex: 1; min-width: 250px; padding: 0.6rem 1rem; border: 1px solid #d1d5db; border-radius: 6px; outline: none;">
            <input type="date" title="Fecha de notificación" style="padding: 0.6rem 1rem; border: 1px solid #d1d5db; border-radius: 6px; outline: none; color: #4b5563;">
            <button style="background-color: #2563eb; color: white; padding: 0.6rem 1.5rem; border: none; border-radius: 6px; font-weight: 500; cursor: pointer;">
                Filtrar Registros
            </button>
        </div>

        <!-- Tabla -->
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ID Ref</th>
                        <th>Asociado</th>
                        <th>Monto</th>
                        <th>Fecha Notificación</th>
                        <th>Fecha Confirmación</th>
                        <th style="text-align: center;">Estado</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>#PAG-1024</td>
                        <td style="font-weight: 500;">Luis Alejandro Ortega Garcia</td>
                        <td>$150,000 COP</td>
                        <td style="color: #6b7280;">24 Sep 2026, 10:30 AM</td>
                        <td style="color: #6b7280;">25 Sep 2026, 09:15 AM</td>
                        <td style="text-align: center;">
                            <span style="background-color: #d1fae5; color: #065f46; padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">Confirmado</span>
                        </td>
                    </tr>
                    <tr>
                        <td>#PAG-1023</td>
                        <td style="font-weight: 500;">María Gómez</td>
                        <td>$85,000 COP</td>
                        <td style="color: #6b7280;">22 Sep 2026, 04:20 PM</td>
                        <td style="color: #6b7280;">23 Sep 2026, 11:00 AM</td>
                        <td style="text-align: center;">
                            <span style="background-color: #d1fae5; color: #065f46; padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">Confirmado</span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Paginación -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; padding: 0 0.5rem;">
            <span style="font-size: 0.85rem; color: #6b7280;">Mostrando <strong style="color:#111827;">1</strong> a <strong style="color:#111827;">2</strong> de <strong style="color:#111827;">24</strong> pagos</span>
            <div style="display: flex; gap: 0.5rem;">
                <button style="padding: 0.4rem 0.8rem; border: 1px solid #d1d5db; background: white; border-radius: 4px; font-size: 0.85rem; color: #374151; cursor: pointer;">Anterior</button>
                <button style="padding: 0.4rem 0.8rem; border: 1px solid #d1d5db; background: white; border-radius: 4px; font-size: 0.85rem; color: #374151; cursor: pointer;">Siguiente</button>
            </div>
        </div>
    </div>
</div>

</body>
</html>

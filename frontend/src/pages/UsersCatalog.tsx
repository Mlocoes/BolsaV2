import { useState, useEffect, useRef } from 'react'
import { HotTable } from '@handsontable/react-wrapper'
import { registerAllModules } from 'handsontable/registry'
import { registerLanguageDictionary, esMX } from 'handsontable/i18n'
import 'handsontable/dist/handsontable.full.min.css'
import '../styles/handsontable-custom.css'
import api from '../services/api'
import Layout from '../components/Layout'

// Registrar todos los módulos de Handsontable
registerAllModules()
// Registrar idioma español (usando es-MX pero con código es-ES)
const esESDict = { ...esMX, languageCode: 'es-ES' }
registerLanguageDictionary(esESDict)

interface User {
  id: string
  username: string
  email: string
  is_active: boolean
  created_at: string
}

export default function UsersCatalog() {
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  })
  const hotTableRef = useRef(null)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    setIsLoading(true)
    try {
      const response = await api.get('/users')
      setUsers(response.data)
    } catch (error) {
      console.error('Failed to load users:', error)
      alert('This feature requires admin privileges')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.username || !formData.email || !formData.password) {
      alert('Todos los campos son obligatorios')
      return
    }

    try {
      await api.post('/auth/register', formData)
      alert('Usuario creado correctamente')
      setShowModal(false)
      setFormData({ username: '', email: '', password: '' })
      loadUsers()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al crear usuario')
    }
  }

  const toggleUserStatus = async (userId: string, currentStatus: boolean) => {
    try {
      await api.patch(`/users/${userId}`, {
        is_active: !currentStatus
      })
      alert(`Usuario ${currentStatus ? 'desactivado' : 'activado'} correctamente`)
      loadUsers()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Operación fallida')
    }
  }

  const handleDelete = async (userId: string, username: string) => {
    if (!confirm(`¿Eliminar usuario ${username}? Esta acción no se puede deshacer.`)) return

    try {
      await api.delete(`/users/${userId}`)
      alert('Usuario eliminado correctamente')
      loadUsers()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al eliminar')
    }
  }

  // Preparar datos para Handsontable
  const tableData = users.map(user => ({
    id: user.id,
    username: user.username,
    email: user.email,
    status: user.is_active ? 'Activo' : 'Inactivo',
    is_active: user.is_active,
    created_at: new Date(user.created_at).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  }))

  const columns = [
    {
      data: 'username',
      title: 'Usuario',
      readOnly: true,
      width: 150,
      className: 'htLeft htBold'
    },
    {
      data: 'email',
      title: 'Correo',
      readOnly: true,
      width: 250
    },
    {
      data: 'status',
      title: 'Estado',
      readOnly: true,
      width: 100,
      renderer: function (_instance: any, td: HTMLTableCellElement, _row: number, _col: number, _prop: any, value: any) {
        td.innerHTML = value
        if (value === 'Activo') {
          td.style.backgroundColor = '#dcfce7'
          td.style.color = '#166534'
          td.style.fontWeight = '600'
        } else {
          td.style.backgroundColor = '#fee2e2'
          td.style.color = '#991b1b'
          td.style.fontWeight = '600'
        }
        td.style.textAlign = 'center'
        return td
      }
    },
    {
      data: 'created_at',
      title: 'Creado',
      readOnly: true,
      width: 120
    },
    {
      data: 'id',
      title: 'Acciones',
      readOnly: true,
      width: 200,
      renderer: function (_instance: any, td: HTMLTableCellElement, row: number, _col: number, _prop: any, _value: any) {
        const user = users[row]
        if (!user) return td

        td.innerHTML = ''
        td.style.textAlign = 'center'

        // Botón toggle status
        const toggleBtn = document.createElement('button')
        toggleBtn.innerHTML = user.is_active ? 'Desactivar' : 'Activar'
        toggleBtn.className = 'text-blue-600 hover:text-blue-900 mr-3 text-sm font-medium'
        toggleBtn.onclick = () => toggleUserStatus(user.id, user.is_active)

        // Botón eliminar
        const deleteBtn = document.createElement('button')
        deleteBtn.innerHTML = 'Eliminar'
        deleteBtn.className = 'text-red-600 hover:text-red-900 text-sm font-medium'
        deleteBtn.onclick = () => handleDelete(user.id, user.username)

        td.appendChild(toggleBtn)
        td.appendChild(deleteBtn)

        return td
      }
    }
  ]

  if (isLoading) {
    return (
      <Layout>
        <div className="flex h-96 items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <div className="text-xl text-gray-600">Cargando usuarios...</div>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="flex flex-col h-full space-y-4">
        {/* Cabecera */}
        <div className="flex-shrink-0 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Gestión de Usuarios</h1>
            <p className="text-gray-600">Gestiona los usuarios del sistema (Solo administradores)</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            + Crear Usuario
          </button>
        </div>

        {/* Tabla con Handsontable */}
        <div className="flex-1 bg-white rounded-lg shadow p-4" style={{ minHeight: '300px', display: 'flex', flexDirection: 'column' }}>
            {users.length === 0 ? (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                No se encontraron usuarios
              </div>
            ) : (
              <div style={{ height: '400px', width: '100%' }}>
              <HotTable
                ref={hotTableRef}
                data={tableData}
                columns={columns}
                colHeaders={true}
                rowHeaders={true}
                height={400}
                licenseKey="non-commercial-and-evaluation"
                stretchH="all"
                autoWrapRow={true}
                autoWrapCol={true}
                filters={true}
                dropdownMenu={true}
                columnSorting={true}
                manualColumnResize={true}
                contextMenu={['copy']}
                language="es-ES"
              />
              </div>
            )}
        </div>

        {/* Modal Crear Usuario */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h2 className="text-2xl font-bold mb-4">Crear Usuario</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Usuario *</label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full px-3 py-2 border rounded"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Correo Electrónico *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border rounded"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Contraseña *</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-3 py-2 border rounded"
                    required
                    minLength={6}
                  />
                  <p className="text-xs text-gray-500 mt-1">Mínimo 6 caracteres</p>
                </div>

                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false)
                      setFormData({ username: '', email: '', password: '' })
                    }}
                    className="px-4 py-2 border rounded hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Crear
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Cuadro de Información */}
        <div className="flex-shrink-0 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-semibold text-yellow-900 mb-2">⚠️ Área de Administración</h3>
          <p className="text-sm text-yellow-800">
            Esta página es solo para administradores del sistema. Todas las operaciones se registran y auditan.
          </p>
        </div>
      </div>
    </Layout>
  )
}

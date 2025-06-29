const getState = ({ getStore, getActions, setStore }) => {
  return {
    store: {
      usuario: null,
      token: null,
      tasks: [],
      loading: false,
      error: null
    },
    actions: {
      // Iniciar sesión
      

      login: async (email, clave) => {
        setStore({ loading: true, error: null });
        console.log("Iniciando sesión con:", email, clave);
        console.log("Backend URL:",`${import.meta.env.VITE_BACKEND_URL}login`);
        try {
      
          const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, clave })
          });
          
          const data = await response.json();
          
          if (!response.ok) {
            throw new Error(data.error || 'Error en inicio de sesión');
          }
          
          // Guardar token y usuario en store y localStorage
          localStorage.setItem('token', data.token);
          localStorage.setItem('usuario', JSON.stringify(data.usuario));
          
          setStore({
            usuario: data.usuario,
            token: data.token,
            loading: false,
            error: null
          });
          
          return {
              success: true,
              message: "logeado exitosamente",
          };
        } catch (error) {
         
          return {
            success: false,
            message: error.message || 'Error al iniciar sesión',
          };
        }
      },
      
      // Registrar nuevo usuario
      signup: async (userData) => {
        setStore({ loading: true, error: null });
        try {
          const response = await fetch(
            `${import.meta.env.VITE_BACKEND_URL}usuario`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(userData)
            }
          );

          const data = await response.json();

          if (!response.ok) {
            // Lanza el mensaje exacto del backend
            throw new Error(data.error || 'Error en registro');
          }

          // Si llegamos aquí, fue exitoso
          setStore({ loading: false });
          return {
            success: true,
            message: 'Usuario registrado exitosamente'
          };

        } catch (error) {
          // Detén el spinner
          setStore({ loading: false, error: error.message });

          return {
            success: false,
            // Aquí sí uso error.message
            message: error.message || 'Error al registrar usuario'
          };
        }
      },

      // Cerrar sesión
      logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('usuario');
        setStore({ usuario: null, token: null, tasks: [] });
      },
      
      // Recuperar sesión desde localStorage
      restoreSession: () => {
        const token = localStorage.getItem('token');
        const usuario = JSON.parse(localStorage.getItem('usuario'));

        if (token && usuario) {
          setStore({ token, usuario });
          return {
            success: true,
            message: "Sesión restaurada exitosamente",
          };
        }
        return {
          success: false,
          message: "No se pudo restaurar la sesión",
        };
      },

      // Obtener tareas del usuario
      getTasks: async () => {
        const { token } = getStore();
        if (!token) return;
        
        try {
         // console.log("Obteniendo tareas del backend:", `${import.meta.env.VITE_BACKEND_URL}tareas`, "con token:", token);
          const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}tareas`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            }
          });
          
         
          const data = await response.json();
          
        //  console.log("Respuesta del backend:", data.tareas);

          if (!response.ok) {
            throw new Error(data.error);
          }
          
          setStore({ tasks: data.tareas });

          return {
            success: true,
            message: "Tareas obtenidas exitosamente",
          }
        } catch (error) {
          
             return {
            success: false,
            message: error.message || 'Error al obtener tareas',
          };
        }
      },
      
      // Crear nueva tarea
      createTask: async (taskData) => {
        const { token } = getStore();
        if (!token) return null;

        console.log(taskData.descripcion);
        
        try {
          const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}tarea`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              titulo: taskData.titulo,
              descripcion: taskData.descripcion,
              fecha: taskData.fecha,
              horaInicio: taskData.horaInicio,
              horaFin: taskData.horaFin,
              etiqueta: taskData.etiqueta,
              imageUrl: taskData.imageUrl || ''
            })
          });
          
          const data = await response.json();
          
          if (!response.ok) {
            throw new Error(data.error || 'Error al crear tarea');
          }
          
          // Actualizar lista de tareas localmente
          setStore(store => ({
            tasks: [...store.tasks, data.tarea]
          }));
          
          return {
            success: true,
            message: "Tarea creada exitosamente",
          };

        } catch (error) {
          return {
            success: false,
            message: error.message || 'Error al crear tarea',
          };
        }
      },

      // Eliminar tarea
      deleteTask: async (taskId) => {
        const { token } = getStore();
        if (!token) return false;
        
        try {
          const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}tarea/${taskId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (!response.ok) {
            throw new Error('Error al eliminar tarea');
          }
          
          // Actualizar lista de tareas localmente
          setStore(store => ({
            tasks: store.tasks.filter(task => task.idTarea !== taskId)
          }));
          
          return {
            success: true,
            message: "Tarea eliminada exitosamente",
          };
          
        } catch (error) {
          return {
            success: false,
            message: error.message || 'Error al eliminar tarea',
          };
        }
      }
    },
  };
};

export default getState;
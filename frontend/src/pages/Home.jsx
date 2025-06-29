import { useState } from 'react';
import CalendarView from '../components/CalendarView';
import AddTaskModal from '../components/AddTaskModal';
import TaskDetailModal from '../components/TaskDetailModal';
import PhraseBanner from '../components/PhraseBanner';
import { toast } from 'react-toastify';
import '../styles/home.css';
import { useEffect, useContext } from 'react';
import { Context } from '../store/appContext';
import { useAlert } from "../hooks/useAlert.js";

const tagColors = {
  Trabajo:  { bg: '#4CAF50', border: '#388E3C' },
  Personal: { bg: '#2196F3', border: '#1976D2' },
  Descanso: { bg: '#FFC107', border: '#FFA000', text: '#000' },
  Estudio:  { bg: '#9C27B0', border: '#7B1FA2' },
  Salud:    { bg: '#F44336', border: '#D32F2F' }
};

export default function Home() {
  const [events, setEvents] = useState([]);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [modalDate, setModalDate] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);

  const { error, success } = useAlert();
  const {store, actions} = useContext(Context);

  // Cargar tareas al montar el componente
  useEffect(() => {
    if (store.token) {
      actions.getTasks();
    }
  }, [store.token]);

  // Convertir tareas a eventos para el calendario
  useEffect(() => {
    const newEvents = store.tasks.map(task => {
      const color = tagColors[task.etiqueta] || { bg: '#607D8B', border: '#455A64' };

      const fechaSolo = task.fecha.split('T')[0];
      return {
        id: task.idTarea,
        title: task.titulo,
        start: `${fechaSolo}T${task.horaInicio}`,
        end: `${fechaSolo}T${task.horaFin}`,
        backgroundColor: color.bg,
        borderColor: color.border,
        textColor: color.text || '#FFF',
        extendedProps: { 
          tag: task.etiqueta,
          descripcion: task.descripcion,
          imageUrl: task.imageUrl
        }
      };
    });
    setEvents(newEvents);
  }, [store.tasks]);

  const openAddModal = (dateStr = null) => {
    setModalDate(dateStr);
    setAddModalOpen(true);
  };

  const closeAddModal = () => setAddModalOpen(false);

  const handleSave = async (taskData) => {
    if (!store.token) {
      error('Debe iniciar sesión para agregar tareas');
      closeAddModal();
      return;
    }

    const savedTask = await actions.createTask({
      titulo: taskData.title,
      descripcion: taskData.description,
      fecha: taskData.date,
      horaInicio: taskData.startTime,
      horaFin: taskData.endTime,
      etiqueta: taskData.tag,
      imageUrl: taskData.imageUrl || ''
    });
    
    if (savedTask.success) {
      closeAddModal();
      actions.getTasks();
      success('Tarea agregada correctamente');
    } else {
      error('Error al guardar tarea');
    }
  };

  const handleEventClick = info => {
    const task = {
      id: info.event.id,
      title: info.event.title,
      startTime: info.event.start.toTimeString().slice(0, 5),
      endTime: info.event.end.toTimeString().slice(0, 5),
      date: info.event.start.toISOString().split('T')[0],
      tag: info.event.extendedProps.tag,
      descripcion: info.event.extendedProps.descripcion,
      imageUrl: info.event.extendedProps.imageUrl
    };
    
    setSelectedTask(task);
    setDetailModalOpen(true);
  };

  const handleDeleteTask = async (taskId) => {
    toast.info(
      <div>
        <p>¿Quiere eliminar esta tarea?</p>
        <div className="toast-actions">
          <button 
            className="toast-btn toast-btn-confirm"
            onClick={ async() => {
              let result = await actions.deleteTask(Number(taskId));

              if (!result.success) {
                error('Error al eliminar la tarea');
                return;
              }

              actions.getTasks();
              toast.dismiss();
              success('Tarea eliminada correctamente');
              setDetailModalOpen(false);
            }}
          >
            Sí
          </button>
          <button 
            className="toast-btn toast-btn-cancel"
            onClick={() => toast.dismiss()}
          >
            No
          </button>
        </div>
      </div>,
      {
        autoClose: false,
        closeButton: false
      }
    );
  };

  return (
    <div className="home-container">
      <PhraseBanner />
      
      <div className="calendar-section">
        <CalendarView
          events={events}
          onDateClick={info => openAddModal(info.dateStr)}
          onEventClick={handleEventClick}
        />
      </div>

      <button className="floating-btn" onClick={() => openAddModal()}>
        +
      </button>

      <AddTaskModal
        isOpen={addModalOpen}
        defaultDate={modalDate}
        onSave={handleSave}
        onClose={closeAddModal}
      />
      
      <TaskDetailModal
        isOpen={detailModalOpen}
        task={selectedTask}
        onClose={() => setDetailModalOpen(false)}
        onDelete={handleDeleteTask} // Pasamos la función de eliminación
      />
    </div>
  ); 
}
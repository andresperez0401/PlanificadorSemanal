import { useState } from 'react';
import CalendarView from '../components/CalendarView';
import AddTaskModal from '../components/AddTaskModal';
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
  const [modalOpen, setModalOpen] = useState(false);
  const [modalDate, setModalDate] = useState(null);

  const { error, success } = useAlert();
  const {store, actions} = useContext(Context);

  //---------------------------------------------------------------------------------------------------------------------------
  //Hooks UseEffect para cargar eventos desde el store

    // Cargar tareas al montar el componente
    useEffect(() => {
      if (store.user) {
        actions.getTasks();
      }
    }, [store.user]);

    // Convertir tareas a eventos para el calendario
    useEffect(() => {
      const newEvents = store.tasks.map(task => {
        const color = tagColors[task.etiqueta] || { bg: '#607D8B', border: '#455A64' };
        return {
          id: task.idTarea,
          title: task.titulo,
          start: `${task.fecha}T${task.horaInicio}`,
          end: `${task.fecha}T${task.horaFin}`,
          backgroundColor: color.bg,
          borderColor: color.border,
          textColor: color.text || '#FFF',
          extendedProps: { tag: task.etiqueta }
        };
      });
      setEvents(newEvents);
    }, [store.tasks]);


  //---------------------------------------------------------------------------------------------------------------------------

  const openModal = (dateStr = null) => {
    setModalDate(dateStr);
    setModalOpen(true);
  };

  const closeModal = () => setModalOpen(false);

  const handleSave = async (taskData) => {

    const savedTask = await actions.createTask({
      titulo: taskData.title,
      fecha: taskData.date,
      horaInicio: taskData.startTime,
      horaFin: taskData.endTime,
      etiqueta: taskData.tag
    });

    console.log('Datos de la tarea:', savedTask);
    
    if (savedTask.success) {
      closeModal();
      success('Tarea agregada correctamente');
    } else {
      error('Error al guardar tarea');
    }
  };


  const handleEventClick = info => {
    toast.info(
      <div>
        <p>¿Quiere eliminar la tarea: "{info.event.title}"?</p>
        <div className="toast-actions">
          <button 
            className="toast-btn toast-btn-confirm"
            onClick={() => {
              actions.deleteTask(Number(info.event.id));
              toast.dismiss();
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
          onDateClick={info => openModal(info.dateStr)}
          onEventClick={handleEventClick}
        />
      </div>

      <button className="floating-btn" onClick={() => openModal()}>
        +
      </button>

      <AddTaskModal
        isOpen={modalOpen}
        defaultDate={modalDate}
        onSave={handleSave}
        onClose={closeModal}
      />
    </div>
  );
}
import { useState } from 'react';
import CalendarView from '../components/CalendarView';
import AddTaskModal from '../components/AddTaskModal';
import PhraseBanner from '../components/PhraseBanner';
import { toast } from 'react-toastify';
import '../styles/home.css';

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

  const openModal = (dateStr = null) => {
    setModalDate(dateStr);
    setModalOpen(true);
  };

  const closeModal = () => setModalOpen(false);

  const handleSave = ({ title, date, startTime, endTime, tag }) => {
    const color = tagColors[tag] || { bg: '#607D8B', border: '#455A64' };
    const newEvt = {
      id: Date.now(),
      title,
      start: `${date}T${startTime}`,
      end: `${date}T${endTime}`,
      backgroundColor: color.bg,
      borderColor: color.border,
      textColor: color.text || '#FFF',
      extendedProps: { tag }
    };
    setEvents(prev => [...prev, newEvt]);
    closeModal();
    toast.success('Tarea agregada correctamente');
  };

  const handleEventClick = info => {
    toast.info(
      <div>
        <p>¿Quiere eliminar la tarea: "{info.event.title}"?</p>
        <div className="toast-actions">
          <button 
            className="toast-btn toast-btn-confirm"
            onClick={() => {
              setEvents(prev => prev.filter(e => e.id !== +info.event.id));
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
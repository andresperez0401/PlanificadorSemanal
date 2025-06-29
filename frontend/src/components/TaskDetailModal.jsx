import { useEffect, useState } from 'react';
import '../styles/task-detail-modal.css';

const tagColors = {
  Trabajo: '#4CAF50',
  Personal: '#2196F3',
  Descanso: '#FFC107',
  Estudio: '#9C27B0',
  Salud: '#F44336'
};

export default function TaskDetailModal({ isOpen, task, onClose, onDelete }) {
  const [isVisible, setIsVisible] = useState(false);
  
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      setTimeout(() => setIsVisible(true), 10);
    } else {
      setIsVisible(false);
      document.body.style.overflow = 'auto';
    }
    
    return () => { document.body.style.overflow = 'auto'; };
  }, [isOpen]);

  if (!isOpen || !task) return null;

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      weekday: 'long',
      day: 'numeric',
      month: 'long'
    });
  };

  const formatTime = (timeString) => {
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours, 10);
    const period = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes} ${period}`;
  };

  const handleDelete = () => {
    onDelete(task.id);
  };

  return (
    <div 
      className={`task-detail-overlay ${isVisible ? 'visible' : ''}`} 
      onClick={onClose}
    >
      <div 
        className={`task-detail-card ${isVisible ? 'visible' : ''}`} 
        onClick={e => e.stopPropagation()}
      >
        {task.imageUrl && (
          <div className="task-image-container">
            <img 
              src={task.imageUrl} 
              alt={task.title} 
              className="task-image"
              onError={(e) => {
                e.target.onerror = null; 
                e.target.parentNode.style.display = 'none';
              }}
            />
          </div>
        )}

        <div className="task-content">
          <div className="task-header">
            <div className="header-content">
              <div 
                className="task-tag" 
                style={{ backgroundColor: tagColors[task.tag] || '#607d8b' }}
              >
                {task.tag}
              </div>
              <h2 className="task-title">{task.title}</h2>
            </div>
            <button 
              className="close-icon-btn" 
              onClick={onClose}
              aria-label="Cerrar modal"
            >
              <svg width="16" height="16" viewBox="0 0 24 24">
                <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>

          <div className="time-info">
            <div className="date-display">
              <span className="date-value">{formatDate(task.date)}</span>
            </div>
            
            <div className="time-range">
              <div className="time-block">
                <span className="time-label">Inicio</span>
                <span className="time-value">{formatTime(task.startTime)}</span>
              </div>
              
              <div className="time-separator">-</div>
              
              <div className="time-block">
                <span className="time-label">Fin</span>
                <span className="time-value">{formatTime(task.endTime)}</span>
              </div>
            </div>
          </div>

          <div className="task-description">
            <p className="description-content">
              {task.descripcion || "No hay descripción para esta tarea"}
            </p>
          </div>

          <div className="task-actions">
            <button 
              className="delete-btn" 
              onClick={handleDelete}
              aria-label="Eliminar tarea"
            >
              Eliminar Tarea
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
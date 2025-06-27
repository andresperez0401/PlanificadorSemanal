import { useState, useEffect } from 'react';
import '../styles/modal.css';

const tags = ['Trabajo', 'Personal', 'Descanso', 'Estudio', 'Salud'];
const tagColors = {
  Trabajo: '#4CAF50',
  Personal: '#2196F3',
  Descanso: '#FFC107',
  Estudio: '#9C27B0',
  Salud: '#F44336'
};

export default function AddTaskModal({ isOpen, onClose, onSave, defaultDate }) {
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('10:00');
  const [tag, setTag] = useState(tags[0]);

  // 1) Calculamos “hoy” en formato YYYY-MM-DD
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm   = String(now.getMonth() + 1).padStart(2, '0');
  const dd   = String(now.getDate()).padStart(2, '0');
  const todayStr = `${yyyy}-${mm}-${dd}`;

  // 2) Calculamos la hora actual en HH:MM
  const nowTime = now.toTimeString().slice(0, 5);

   // Resetear campos al abrir el modal
  useEffect(() => {
    if (isOpen) {
      setTitle('');
      setDate(
      defaultDate 
        ? defaultDate.split('T')[0]   // ✅ <- solo "YYYY-MM-DD"
        : todayStr
      );
      setStartTime('09:00');
      setEndTime('10:00');
      setTag(tags[0]);
    }
  }, [isOpen, defaultDate, todayStr]);

  // Si la fecha es hoy y el startTime está antes de ahora, lo corregimos
  useEffect(() => {
    if (date === todayStr && startTime < nowTime) {
      setStartTime(nowTime);
    }

    // Si la fecha es hoy y el endTime está antes de startTime, lo corregimos
    if (date === todayStr && endTime <= addMinutes(startTime, 60)) {
      const newEndTime = addMinutes(startTime, 60);
      setEndTime(newEndTime);
    }

    if (endTime <= addMinutes(startTime, 60)) {
      const newEndTime = addMinutes(startTime, 60);
      setEndTime(newEndTime);
    }
  }, [date, nowTime, startTime, endTime, todayStr]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title || !date || !startTime || !endTime) {
      return;
    }
    onSave({ title, date, startTime, endTime, tag });
  };


  //Funcion para sumar minutos
  function addMinutes(timeStr, minsToAdd) {
    const [h, m] = timeStr.split(':').map(Number);
    const date = new Date();
    date.setHours(h);
    date.setMinutes(m + minsToAdd);

    const hh = String(date.getHours()).padStart(2, '0');
    const mm = String(date.getMinutes()).padStart(2, '0');
    return `${hh}:${mm}`;
  }

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div className="modal-header">
          <h2 className="modal-title">Nueva Tarea</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Título de la tarea"
              className="modal-input"
              required
            />
          </div>
          
          <div className="form-group">
            <input
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
              className="modal-input"
              min={todayStr} 
              required
            />
          </div>
          
          <div className="time-group">
            <div className="form-group">
              <label>Inicio</label>
              <input
                type="time"
                value={startTime}
                onChange={e => setStartTime(e.target.value)}
                className="modal-input"
                required
              />
            </div>
            
            <div className="form-group">
              <label>Fin</label>
              <input
                type="time"
                value={endTime}
                onChange={e => setEndTime(e.target.value)}
                className="modal-input"
                required
              />
            </div>
          </div>
          
          <div className="form-group">
            <label>Etiqueta</label>
            <div className="tag-container">
              {tags.map((t) => (
                <button
                  key={t}
                  type="button"
                  className={`tag-btn ${tag === t ? 'active' : ''}`}
                  onClick={() => setTag(t)}
                  style={{ 
                    backgroundColor: tag === t ? tagColors[t] : '#f0f0f0',
                    color: tag === t ? 'white' : '#333'
                  }}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
          
          <div className="modal-actions">
            <button type="button" className="cancel-btn" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="save-btn">
              Guardar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}